from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .catalog import build_reference_index, load_effective_catalog, object_summary, search_objects
from .config import load_config
from .paths import REPO_ROOT
from .providers import build_provider_command, detect_provider
from .sessions import DraftsmanSessionStore
from .validation import selected_framework_root, validate_workspace


DEFAULT_PROVIDER_TIMEOUT_SECONDS = 180


@dataclass
class DraftsmanResponse:
    session_id: str
    answer: str
    questions: list[str]
    proposals: list[dict[str, Any]]
    grounding: list[dict[str, str]]
    provider_used: bool

    def public_dict(self) -> dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "answer": self.answer,
            "questions": self.questions,
            "proposals": [public_proposal(proposal) for proposal in self.proposals],
            "grounding": self.grounding,
            "providerUsed": self.provider_used,
        }


class DraftsmanEngine:
    def __init__(
        self,
        config_path: Path | None = None,
        session_store: DraftsmanSessionStore | None = None,
    ) -> None:
        self.config_path = config_path
        self.session_store = session_store or DraftsmanSessionStore()

    def chat(self, message: str, session_id: str | None = None) -> DraftsmanResponse:
        config = load_config(self.config_path)
        configured_framework = Path(config.get("framework_repo_path") or REPO_ROOT).expanduser()
        workspace_value = str(config.get("content_repo_path") or "").strip()
        workspace = Path(workspace_value).expanduser() if workspace_value else None
        framework_root = selected_framework_root(workspace, configured_framework)
        session = self.session_store.load(session_id)
        session.setdefault("messages", []).append({"role": "user", "content": message})

        local = answer_locally(message, workspace, framework_root)
        if local:
            session["messages"].append({"role": "draftsman", "content": local.answer})
            self.session_store.save(session)
            return DraftsmanResponse(session["id"], local.answer, local.questions, [], local.grounding, False)

        provider_response = self.ask_provider(config, framework_root, workspace, message, session)
        session["messages"].append({"role": "draftsman", "content": provider_response.answer})
        session["proposals"] = merge_proposals(session.get("proposals", []), provider_response.proposals)
        self.session_store.save(session)
        return provider_response

    def apply_proposals(self, session_id: str, proposal_ids: list[str] | None = None) -> dict[str, Any]:
        config = load_config(self.config_path)
        workspace_value = str(config.get("content_repo_path") or "").strip()
        if not workspace_value:
            raise ValueError("No company DRAFT repo selected.")
        workspace = Path(workspace_value).expanduser()
        session = self.session_store.load(session_id)
        selected = set(proposal_ids or [])
        applied: list[dict[str, str]] = []
        for proposal in session.get("proposals", []):
            if selected and proposal.get("id") not in selected:
                continue
            relative_path = proposal.get("path")
            content = proposal.get("content")
            if not relative_path or not content:
                continue
            target = safe_workspace_path(workspace, str(relative_path))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(content), encoding="utf-8")
            applied.append(
                {
                    "id": str(proposal.get("id", "")),
                    "artifactId": str(proposal.get("artifactId", "")),
                    "name": str(proposal.get("name", "")),
                    "artifactType": str(proposal.get("artifactType", "")),
                    "path": str(relative_path),
                }
            )
            proposal["applied"] = True
        self.session_store.save(session)
        validation = validate_workspace(workspace, Path(config.get("framework_repo_path") or REPO_ROOT).expanduser())
        return {
            "applied": applied,
            "validation": {
                "ok": validation.ok,
                "stdout": validation.stdout,
                "stderr": validation.stderr,
            },
        }

    def ask_provider(
        self,
        config: dict[str, Any],
        framework_root: Path,
        workspace: Path | None,
        message: str,
        session: dict[str, Any],
    ) -> DraftsmanResponse:
        provider = config.get("provider") or {}
        provider_type = str(provider.get("type") or "")
        executable = str(provider.get("executable") or provider.get("endpoint") or "")
        status = detect_provider(provider_type, executable or None)
        if not status.available:
            answer = (
                "I can answer framework and catalog lookup questions locally, but architecture drafting "
                f"needs a configured provider. Current provider status: {status.detail}"
            )
            return DraftsmanResponse(session["id"], answer, [], [], [], False)

        prompt = build_draftsman_prompt(framework_root, workspace, message, session)
        raw = invoke_provider(provider, prompt)
        parsed = parse_provider_response(raw)
        proposals = normalize_proposals(parsed.get("proposals", []))
        answer = str(parsed.get("answer") or raw).strip()
        questions = [str(item) for item in parsed.get("questions", []) if str(item).strip()]
        grounding = [object_summary(obj) for obj in search_objects(load_effective_catalog(workspace, framework_root), message, 5)]
        return DraftsmanResponse(session["id"], answer, questions, proposals, grounding, True)


@dataclass
class LocalAnswer:
    answer: str
    questions: list[str]
    grounding: list[dict[str, str]]


def answer_locally(message: str, workspace: Path | None, framework_root: Path) -> LocalAnswer | None:
    lowered = message.lower()
    if is_framework_definition_question(lowered, "technology component"):
        return LocalAnswer(read_doc_section(framework_root / "docs" / "technology-components.md", "What A Technology Component Is"), [], [])
    if is_framework_definition_question(lowered, "host standard") or is_framework_definition_question(lowered, "service standard"):
        return LocalAnswer(read_doc_intro(framework_root / "docs" / "standards.md"), [], [])
    if is_framework_definition_question(lowered, "requirement group") or is_framework_definition_question(lowered, "definition checklist"):
        return LocalAnswer(read_doc_intro(framework_root / "docs" / "requirement-groups.md"), [], [])
    if is_framework_definition_question(lowered, "software deployment pattern"):
        return LocalAnswer(read_doc_intro(framework_root / "docs" / "software-deployment-patterns.md"), [], [])
    if "where" in lowered and any(term in lowered for term in ("used", "referenced", "use")):
        return answer_usage_question(message, workspace, framework_root)
    return None


def is_framework_definition_question(lowered: str, term: str) -> bool:
    return term in lowered and any(prefix in lowered for prefix in ("what is", "what's", "explain", "define"))


def answer_usage_question(message: str, workspace: Path | None, framework_root: Path) -> LocalAnswer:
    objects = load_effective_catalog(workspace, framework_root)
    matches = search_objects(objects, message, 3)
    content_matches = [
        match for match in matches
        if match.get("type") not in {"requirement_group", "capability", "domain"}
    ]
    if content_matches:
        matches = content_matches
    if not matches:
        return LocalAnswer("I could not find a matching catalog object in the loaded DRAFT model.", [], [])
    target = matches[0]
    target_uid = str(target.get("uid") or target.get("id") or "")
    referenced_by = build_reference_index(objects).get(target_uid, [])
    grounding = [object_summary(target)]
    if not referenced_by:
        answer = (
            f"I found {target.get('name')}, but it is not referenced by any "
            "other object in the currently loaded DRAFT model."
        )
        return LocalAnswer(answer, [], grounding)
    lines = [f"{target.get('name')} is referenced by:"]
    for ref in referenced_by:
        source = objects.get(ref["source"], {})
        grounding.append(object_summary(source))
        lines.append(f"- {source.get('name', ref['source'])} via {ref['path']}")
    return LocalAnswer("\n".join(lines), [], grounding)


def read_doc_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    body = match.group("body").strip() if match else text.strip()
    return trim_markdown(body)


def read_doc_intro(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    body = re.sub(r"^# .*\n", "", text, count=1).strip()
    body = body.split("\n## ", 1)[0].strip()
    return trim_markdown(body)


def trim_markdown(text: str, limit: int = 1400) -> str:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3].rstrip() + "..."


def build_draftsman_prompt(framework_root: Path, workspace: Path | None, message: str, session: dict[str, Any]) -> str:
    objects = load_effective_catalog(workspace, framework_root)
    matches = [object_summary(obj) for obj in search_objects(objects, message, 8)]
    docs = [
        ("Draftsman Instructions", framework_root / "docs" / "draftsman.md"),
        ("Workspace Model", framework_root / "docs" / "workspaces.md"),
        ("Schema Reference", framework_root / "docs" / "yaml-schema-reference.md"),
        ("Requirement Groups", framework_root / "docs" / "requirement-groups.md"),
        ("Capabilities", framework_root / "docs" / "capabilities.md"),
    ]
    doc_context = "\n\n".join(f"## {title}\n{path.read_text(encoding='utf-8')[:5000]}" for title, path in docs if path.exists())
    uploads = session.get("uploads", [])[-6:]
    upload_context = "\n".join(
        f"- {item.get('name')} ({item.get('contentType', 'unknown')}): {item.get('path')}\n{item.get('text', '')[:3000]}"
        for item in uploads
    )
    return f"""
You are the DRAFT Draftsman. You conduct architecture interviews and produce DRAFT artifacts.

Rules:
- Never ask for API keys or secrets.
- Do not show raw YAML to the user.
- Reuse existing artifacts when possible.
- Separate observed facts from assumptions.
- Ask focused follow-up questions for missing Requirement Group facts.
- Use requirements.activeRequirementGroups in .draft/workspace.yaml as the source for
  which workspace-activated requirement groups to push during interviews. Do not enforce an
  available workspace-mode group just because its YAML exists.
- Preserve provider identity on workspace-activated Requirement Groups so DRAFT-provided,
  third-party-provided, and company-provided control interpretations remain distinct.
- First-class objects use generated uid values for machine identity. Do not ask
  humans to invent semantic object ids. Use names and aliases in conversation,
  and keep uid stable through renames.
- For Requirement Group entries with relatedCapability, resolve the capability object first,
  check workspace capability implementations, prefer implementations with lifecycleStatus preferred,
  and present those as recommended options before asking an open question.
- For capability requirements, ask what mechanism satisfies the capability:
  field, internal component, Technology Component configuration, external interaction, deployment
  configuration, or architectural decision.
- Do not turn capability requirements into team ownership questions unless the
  applicable Requirement Group explicitly asks for ownership.
- For Host Requirement Group patch management, ask what patch platform, installed component,
  Technology Component configuration, or architectural decision applies updates; do not ask which
  team owns patching as the capability answer.
- For Appliance Components, remember that the object maps directly to a vendor-product
  identity but carries service-like operating capability answers because there
  is no Host Standard or Service Standard wrapper to inherit the host or service requirements.
- If you propose artifacts, return them as JSON proposals with YAML content for the backend only.
- The visible answer must summarize artifacts in plain language.

User request:
{message}

Relevant existing objects:
{json.dumps(matches, indent=2)}

Uploaded source material:
{upload_context or "No uploaded source material in this session."}

Framework context:
{doc_context}

Return JSON only with this shape:
{{
  "answer": "plain-language response for the user; no YAML",
  "questions": ["focused follow-up question if needed"],
  "proposals": [
    {{
      "id": "short proposal id",
      "action": "create|update",
      "artifactType": "Technology Component|Appliance Component|Host Standard|Service Standard|Database Standard|Reference Architecture|Software Deployment Pattern|Capability|Requirement Group|Decision Record|Drafting Session",
      "name": "artifact name",
      "summary": "plain-language summary",
      "path": "relative file path under the company DRAFT repo",
      "content": "complete YAML content for the backend to write; never mention this content in the answer"
    }}
  ]
}}
"""


def invoke_provider(provider: dict[str, Any], prompt: str) -> str:
    provider_type = str(provider.get("type") or "")
    executable = str(provider.get("executable") or "")
    model = str(provider.get("model") or "")
    timeout_seconds = provider_timeout_seconds(provider)
    if provider_type == "local-llm":
        return invoke_ollama(str(provider.get("endpoint") or "http://127.0.0.1:11434"), model, prompt, timeout_seconds)
    try:
        command = build_provider_command(provider_type, executable, prompt, model)
        process = subprocess.run(command, text=True, capture_output=True, check=False, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return (
            f"The {provider_display_name(provider_type)} provider did not return within "
            f"{timeout_seconds} seconds, so I stopped waiting. I did not create or apply any artifacts. "
            "Try the request again in smaller batches, verify the provider CLI works in a terminal, "
            "or increase the provider timeout in the DRAFT Table config."
        )
    except (OSError, ValueError) as exc:
        return f"The {provider_display_name(provider_type)} provider could not be started: {exc}"
    if process.returncode != 0:
        return process.stderr.strip() or process.stdout.strip() or f"Provider command failed with exit code {process.returncode}."
    return process.stdout.strip()


def provider_timeout_seconds(provider: dict[str, Any]) -> int:
    raw = provider.get("timeout_seconds") or provider.get("timeoutSeconds") or provider.get("timeout")
    if raw in (None, ""):
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    return max(5, min(value, 1800))


def provider_display_name(provider_type: str) -> str:
    return {
        "codex": "Codex",
        "claude-code": "Claude Code",
        "gemini-cli": "Gemini CLI",
        "local-llm": "local LLM",
        "custom-command": "custom command",
    }.get(provider_type, provider_type or "AI")


def invoke_ollama(endpoint: str, model: str, prompt: str, timeout_seconds: int = DEFAULT_PROVIDER_TIMEOUT_SECONDS) -> str:
    if not model:
        return "Local LLM mode needs a selected model name."
    url = endpoint.rstrip("/") + "/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        return f"Local LLM endpoint is not reachable: {exc}"
    except json.JSONDecodeError as exc:
        return f"Local LLM endpoint returned invalid JSON: {exc}"
    return str(data.get("response", ""))


def parse_provider_response(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"answer": raw, "questions": [], "proposals": []}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else {"answer": raw, "questions": [], "proposals": []}
        except json.JSONDecodeError:
            pass
    return {"answer": raw, "questions": [], "proposals": []}


def normalize_proposals(proposals: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if not isinstance(proposals, list):
        return normalized
    for index, proposal in enumerate(proposals, start=1):
        if not isinstance(proposal, dict):
            continue
        proposal_id = str(proposal.get("id") or f"proposal-{index}")
        identity = proposal_identity(str(proposal.get("content") or ""))
        normalized.append(
            {
                "id": proposal_id,
                "action": str(proposal.get("action") or "create"),
                "artifactType": str(proposal.get("artifactType") or "Artifact"),
                "name": str(proposal.get("name") or proposal_id),
                "summary": str(proposal.get("summary") or ""),
                "path": str(proposal.get("path") or ""),
                "artifactId": identity.get("uid", ""),
                "artifactUid": identity.get("uid", ""),
                "content": str(proposal.get("content") or ""),
                "applied": bool(proposal.get("applied", False)),
            }
        )
    return normalized


def proposal_identity(content: str) -> dict[str, str]:
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        "uid": str(data.get("uid") or data.get("id") or ""),
        "type": str(data.get("type") or ""),
        "name": str(data.get("name") or ""),
    }


def public_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": proposal.get("id", ""),
        "artifactId": proposal.get("artifactId", ""),
        "artifactUid": proposal.get("artifactUid", ""),
        "action": proposal.get("action", ""),
        "artifactType": proposal.get("artifactType", ""),
        "name": proposal.get("name", ""),
        "summary": proposal.get("summary", ""),
        "path": proposal.get("path", ""),
        "applied": proposal.get("applied", False),
    }


def merge_proposals(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(item.get("id")): item for item in existing if item.get("id")}
    for proposal in incoming:
        by_id[str(proposal.get("id"))] = proposal
    return list(by_id.values())


def safe_workspace_path(workspace: Path, relative_path: str) -> Path:
    target = (workspace / relative_path).resolve()
    root = workspace.resolve()
    if root not in target.parents and target != root:
        raise ValueError("Proposal path escapes the company DRAFT repo.")
    return target
