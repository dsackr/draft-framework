from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .config import load_config, save_config
from .draftsman import DraftsmanEngine
from .github import github_status
from .providers import detect_provider
from .repo import ensure_workspace_layout, git_status, is_workspace
from .validation import validate_workspace


def create_app(config_path: Path | None = None) -> Any:
    try:
        from fastapi import Body, FastAPI, File, HTTPException, UploadFile
        from fastapi.responses import HTMLResponse
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "FastAPI runtime dependencies are missing. Install with: python3 -m pip install -e ."
        ) from exc

    app = FastAPI(title="DRAFT Table", version="0.1.0")
    draftsman = DraftsmanEngine(config_path)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return INDEX_HTML

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        config = load_config(config_path)
        repo_value = str(config.get("content_repo_path") or "").strip()
        repo_path = Path(repo_value).expanduser() if repo_value else None
        framework_repo = Path(config.get("framework_repo_path") or "").expanduser()
        provider = config.get("provider") or {}
        provider_status = detect_provider(
            str(provider.get("type") or ""),
            str(provider.get("executable") or provider.get("endpoint") or "") or None,
        )
        git = {"returncode": None, "stdout": "", "stderr": "No content repo selected."}
        validation = {"returncode": None, "stdout": "", "stderr": "No content repo selected."}
        if repo_path and repo_path.exists():
            git_process = git_status(repo_path)
            git = {
                "returncode": git_process.returncode,
                "stdout": git_process.stdout,
                "stderr": git_process.stderr,
            }
            validation_result = validate_workspace(repo_path, framework_repo)
            validation = {
                "returncode": validation_result.returncode,
                "stdout": validation_result.stdout,
                "stderr": validation_result.stderr,
            }
        return {
            "contentRepoPath": str(repo_path) if repo_path else "",
            "isWorkspace": is_workspace(repo_path) if repo_path and repo_path.exists() else False,
            "provider": {
                "type": provider_status.provider_type,
                "available": provider_status.available,
                "executable": provider_status.executable,
                "detail": provider_status.detail,
            },
            "github": github_status().__dict__,
            "git": git,
            "validation": validation,
        }

    @app.post("/api/repo/select")
    def select_repo(selection: dict[str, Any] = Body(...)) -> dict[str, Any]:
        repo_path = Path(str(selection.get("path") or "")).expanduser()
        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository path does not exist: {repo_path}")
        created = ensure_workspace_layout(repo_path)
        config = load_config(config_path)
        config["content_repo_path"] = str(repo_path)
        save_config(config, config_path)
        return {"ok": True, "path": str(repo_path), "created": [str(path) for path in created]}

    @app.post("/api/draftsman/chat")
    def draftsman_chat(request: dict[str, Any] = Body(...)) -> dict[str, Any]:
        message = str(request.get("message") or "")
        session_id = str(request.get("sessionId") or "") or None
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message is required.")
        return draftsman.chat(message, session_id).public_dict()

    @app.post("/api/draftsman/apply")
    def draftsman_apply(request: dict[str, Any] = Body(...)) -> dict[str, Any]:
        try:
            session_id = str(request.get("sessionId") or "")
            proposal_ids = request.get("proposalIds")
            if proposal_ids is not None and not isinstance(proposal_ids, list):
                raise ValueError("proposalIds must be a list when provided.")
            return draftsman.apply_proposals(session_id, proposal_ids)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/draftsman/upload")
    async def draftsman_upload(sessionId: Optional[str] = None, file: UploadFile = File(...)) -> dict[str, Any]:
        session = draftsman.session_store.load(sessionId)
        upload_dir = draftsman.session_store.upload_dir(str(session["id"]))
        safe_name = safe_upload_name(file.filename or "upload")
        target = upload_dir / safe_name
        content = await file.read()
        target.write_bytes(content)
        item = {
            "name": safe_name,
            "path": str(target),
            "contentType": file.content_type or "application/octet-stream",
            "text": extract_upload_text(safe_name, file.content_type or "", content),
        }
        session.setdefault("uploads", []).append(item)
        draftsman.session_store.save(session)
        return {
            "sessionId": session["id"],
            "name": safe_name,
            "contentType": item["contentType"],
            "textAvailable": bool(item["text"]),
        }

    return app


def safe_upload_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in name)
    return safe.strip(".-") or "upload"


def extract_upload_text(name: str, content_type: str, content: bytes) -> str:
    lowered = name.lower()
    if content_type.startswith("text/") or lowered.endswith((".txt", ".md", ".csv", ".json", ".yaml", ".yml")):
        try:
            return content.decode("utf-8")[:20000]
        except UnicodeDecodeError:
            return content.decode("utf-8", errors="replace")[:20000]
    return ""


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DRAFT Table</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f8fafc;
      --panel: #ffffff;
      --text: #111827;
      --muted: #64748b;
      --border: #d8dee9;
      --accent: #2563eb;
      --ok: #047857;
      --bad: #b91c1c;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0f172a;
        --panel: #111827;
        --text: #e5e7eb;
        --muted: #94a3b8;
        --border: #334155;
        --accent: #60a5fa;
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .shell {
      display: grid;
      grid-template-columns: 280px 1fr;
      min-height: 100vh;
    }
    aside {
      border-right: 1px solid var(--border);
      padding: 24px;
    }
    main { padding: 24px; }
    h1, h2 { margin: 0 0 12px; }
    p { color: var(--muted); line-height: 1.5; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }
    label {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 6px;
    }
    input {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      background: transparent;
      color: var(--text);
      font: inherit;
    }
    button {
      margin-top: 10px;
      border: 0;
      border-radius: 6px;
      padding: 10px 12px;
      background: var(--accent);
      color: white;
      font: inherit;
      cursor: pointer;
    }
    pre {
      overflow: auto;
      white-space: pre-wrap;
      background: rgba(100, 116, 139, 0.12);
      padding: 12px;
      border-radius: 6px;
      min-height: 56px;
    }
    .status { font-weight: 700; }
    .ok { color: var(--ok); }
    .bad { color: var(--bad); }
    .chat {
      display: grid;
      gap: 12px;
    }
    .messages {
      display: grid;
      gap: 10px;
      min-height: 260px;
      max-height: 48vh;
      overflow: auto;
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: rgba(100, 116, 139, 0.08);
    }
    .message {
      padding: 12px;
      border-radius: 8px;
      line-height: 1.5;
      white-space: pre-wrap;
    }
    .user { background: rgba(37, 99, 235, 0.14); }
    .draftsman { background: var(--panel); border: 1px solid var(--border); }
    textarea {
      width: 100%;
      min-height: 92px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      background: transparent;
      color: var(--text);
      font: inherit;
      resize: vertical;
    }
    .proposal {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      margin-top: 8px;
      background: rgba(100, 116, 139, 0.08);
    }
    .proposal strong { display: block; margin-bottom: 4px; }
    @media (max-width: 800px) {
      .shell { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--border); }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <h1>DRAFT Table</h1>
      <p>Local drafting table for a DRAFT architecture catalog. The Draftsman conversation is the primary workspace.</p>
    </aside>
    <main>
      <section class="panel">
        <h2>Content Repo</h2>
        <label for="repo-path">Local repo path</label>
        <input id="repo-path" placeholder="/path/to/company-draft-catalog">
        <button id="select-repo">Select Repo</button>
        <p id="repo-message"></p>
      </section>
      <section class="panel chat" style="margin-top:16px">
        <h2>Draftsman Conversation</h2>
        <p>Talk through the architecture, attach source material, and let the Draftsman interview for missing facts. DRAFT Table does not show raw YAML.</p>
        <div class="messages" id="messages"></div>
        <label for="upload">Source material</label>
        <input id="upload" type="file">
        <button id="upload-button">Attach Source</button>
        <p id="upload-message"></p>
        <label for="draftsman-message">Message</label>
        <textarea id="draftsman-message" placeholder="Example: What is a Technology Component? Or: Review the uploaded diagram and draft the architecture artifacts we need."></textarea>
        <button id="send-message">Send</button>
        <div id="proposal-actions"></div>
      </section>
      <div class="grid" style="margin-top:16px">
        <section class="panel">
          <h2>Provider</h2>
          <pre id="provider">Loading...</pre>
        </section>
        <section class="panel">
          <h2>Git Status</h2>
          <pre id="git">Loading...</pre>
        </section>
        <section class="panel">
          <h2>Validation</h2>
          <pre id="validation">Loading...</pre>
        </section>
      </div>
    </main>
  </div>
  <script>
    let sessionId = null;
    let latestProposals = [];

    function addMessage(role, text) {
      const messages = document.getElementById('messages');
      const node = document.createElement('div');
      node.className = `message ${role}`;
      node.textContent = text;
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
    }

    function replaceLastDraftsmanMessage(text) {
      const messages = document.getElementById('messages');
      if (messages.lastChild) {
        messages.lastChild.textContent = text;
      } else {
        addMessage('draftsman', text);
      }
    }

    async function readJson(response) {
      const text = await response.text();
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch (error) {
        return {detail: text};
      }
    }

    function renderProposals(proposals) {
      latestProposals = proposals || [];
      const target = document.getElementById('proposal-actions');
      if (!latestProposals.length) {
        target.innerHTML = '';
        return;
      }
      target.innerHTML = `
        <h3>Proposed Artifacts</h3>
        ${latestProposals.map(proposal => `
          <div class="proposal">
            <strong>${proposal.action} ${proposal.artifactType}: ${proposal.name}</strong>
            <div>${proposal.summary || 'No summary provided.'}</div>
          </div>
        `).join('')}
        <button id="apply-proposals">Apply Proposed Artifacts</button>
      `;
      document.getElementById('apply-proposals').addEventListener('click', applyProposals);
    }

    async function refresh() {
      const response = await fetch('/api/status');
      const data = await response.json();
      document.getElementById('repo-path').value = data.contentRepoPath || '';
      document.getElementById('provider').textContent =
        `${data.provider.type || 'not selected'}\\n${data.provider.available ? 'available' : 'missing'}\\n${data.provider.detail || ''}`;
      document.getElementById('git').textContent =
        data.git.stdout || data.git.stderr || 'No Git output.';
      document.getElementById('validation').textContent =
        data.validation.stdout || data.validation.stderr || 'No validation output.';
    }
    document.getElementById('select-repo').addEventListener('click', async () => {
      const path = document.getElementById('repo-path').value.trim();
      const message = document.getElementById('repo-message');
      message.textContent = 'Selecting repo...';
      const response = await fetch('/api/repo/select', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path})
      });
      const data = await response.json();
      message.textContent = response.ok ? `Selected ${data.path}` : data.detail;
      await refresh();
    });

    document.getElementById('send-message').addEventListener('click', async () => {
      const input = document.getElementById('draftsman-message');
      const message = input.value.trim();
      if (!message) return;
      addMessage('user', message);
      input.value = '';
      addMessage('draftsman', 'Thinking...');
      try {
        const response = await fetch('/api/draftsman/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message, sessionId})
        });
        const data = await readJson(response);
        sessionId = data.sessionId || sessionId;
        if (!response.ok) {
          throw new Error(data.detail || `Request failed with HTTP ${response.status}.`);
        }
        replaceLastDraftsmanMessage(data.answer || data.detail || 'No response.');
        if (data.questions?.length) {
          addMessage('draftsman', `I need to confirm:\\n- ${data.questions.join('\\n- ')}`);
        }
        renderProposals(data.proposals || []);
      } catch (error) {
        replaceLastDraftsmanMessage(`The Draftsman request failed: ${error.message}`);
        renderProposals([]);
      }
    });

    document.getElementById('upload-button').addEventListener('click', async () => {
      const input = document.getElementById('upload');
      const message = document.getElementById('upload-message');
      if (!input.files.length) {
        message.textContent = 'Choose a file first.';
        return;
      }
      const form = new FormData();
      form.append('file', input.files[0]);
      const url = sessionId ? `/api/draftsman/upload?sessionId=${encodeURIComponent(sessionId)}` : '/api/draftsman/upload';
      const response = await fetch(url, {method: 'POST', body: form});
      const data = await response.json();
      sessionId = data.sessionId || sessionId;
      message.textContent = response.ok ? `Attached ${data.name}` : data.detail;
    });

    async function applyProposals() {
      if (!sessionId || !latestProposals.length) return;
      const response = await fetch('/api/draftsman/apply', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({sessionId, proposalIds: latestProposals.map(proposal => proposal.id)})
      });
      const data = await response.json();
      if (!response.ok) {
        addMessage('draftsman', data.detail || 'Could not apply the proposed artifacts.');
        return;
      }
      const applied = (data.applied || []).map(item => `${item.artifactType || 'Artifact'}: ${item.name || item.id}`).join('\\n- ');
      addMessage('draftsman', `Applied artifact changes${applied ? `:\\n- ${applied}` : '.'}\\nValidation ${data.validation?.ok ? 'passed' : 'needs attention'}.`);
      renderProposals([]);
      await refresh();
    }
    refresh();
  </script>
</body>
</html>
"""
