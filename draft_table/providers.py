from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_PROVIDERS = ("codex", "claude-code", "gemini-cli", "local-llm", "custom-command")


@dataclass(frozen=True)
class ProviderStatus:
    provider_type: str
    executable: str
    available: bool
    detail: str


def executable_name(provider_type: str) -> str:
    return {
        "codex": "codex",
        "claude-code": "claude",
        "gemini-cli": "gemini",
        "local-llm": "",
        "custom-command": "",
    }.get(provider_type, "")


def detect_provider(provider_type: str, executable: str | None = None) -> ProviderStatus:
    if provider_type not in SUPPORTED_PROVIDERS:
        return ProviderStatus(provider_type, executable or "", False, "Unsupported provider")

    if provider_type == "local-llm":
        endpoint = executable or "http://127.0.0.1:11434"
        return ProviderStatus(provider_type, endpoint, True, "Uses Ollama-compatible localhost endpoint")

    if provider_type == "custom-command":
        if not executable:
            return ProviderStatus(provider_type, "", False, "No custom command configured")
        resolved = shutil.which(executable) or executable
        if shutil.which(executable) or Path(executable).exists():
            return ProviderStatus(provider_type, resolved, True, "Custom command configured")
        return ProviderStatus(provider_type, resolved, False, "Custom command was not found")

    command = executable or executable_name(provider_type)
    resolved = shutil.which(command)
    if not resolved:
        return ProviderStatus(provider_type, command, False, install_hint(provider_type))
    return ProviderStatus(provider_type, resolved, True, "Detected provider CLI")


def doctor(configured_provider: dict[str, str] | None = None) -> list[ProviderStatus]:
    configured_provider = configured_provider or {}
    statuses: list[ProviderStatus] = []
    for provider_type in SUPPORTED_PROVIDERS:
        configured_executable = ""
        if configured_provider.get("type") == provider_type:
            configured_executable = configured_provider.get("executable") or configured_provider.get("endpoint") or ""
        statuses.append(detect_provider(provider_type, configured_executable or None))
    return statuses


def install_hint(provider_type: str) -> str:
    return {
        "codex": "Install Codex CLI, then run its login flow with codex --login.",
        "claude-code": "Install Claude Code, then run claude and complete its login flow.",
        "gemini-cli": "Install Gemini CLI, then run gemini and complete its Google login flow.",
    }.get(provider_type, "Configure this provider locally.")


def build_provider_command(
    provider_type: str,
    executable: str,
    prompt: str,
    model: str = "",
) -> list[str]:
    if provider_type == "codex":
        command = [executable or "codex", "exec"]
        if model:
            command.extend(["--model", model])
        command.append(prompt)
        return command
    if provider_type == "claude-code":
        command = [executable or "claude", "--print"]
        if model:
            command.extend(["--model", model])
        command.append(prompt)
        return command
    if provider_type == "gemini-cli":
        command = [executable or "gemini"]
        if model:
            command.extend(["--model", model])
        command.extend(["--prompt", prompt])
        return command
    if provider_type == "custom-command":
        if not executable:
            raise ValueError("custom-command requires an executable")
        return [executable, prompt]
    if provider_type == "local-llm":
        raise ValueError("local-llm command construction is not supported in Phase 1")
    raise ValueError(f"Unsupported provider: {provider_type}")


def format_statuses(statuses: Iterable[ProviderStatus]) -> str:
    lines = []
    for status in statuses:
        marker = "ok" if status.available else "missing"
        executable = f" ({status.executable})" if status.executable else ""
        lines.append(f"{status.provider_type}: {marker}{executable} - {status.detail}")
    return "\n".join(lines)
