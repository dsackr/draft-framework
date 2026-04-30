from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import DEFAULT_CONFIG_DIR


SESSION_ROOT = DEFAULT_CONFIG_DIR / "sessions"


def new_session_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"session-{timestamp}-{secrets.token_hex(4)}"


class DraftsmanSessionStore:
    def __init__(self, root: Path = SESSION_ROOT) -> None:
        self.root = root.expanduser()

    def load(self, session_id: str | None = None) -> dict[str, Any]:
        resolved = session_id or new_session_id()
        path = self.path(resolved)
        if not path.exists():
            return {"id": resolved, "messages": [], "uploads": [], "proposals": []}
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {"id": resolved, "messages": [], "uploads": [], "proposals": []}

    def save(self, session: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.path(str(session["id"]))
        with path.open("w", encoding="utf-8") as handle:
            json.dump(session, handle, indent=2)
            handle.write("\n")
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def path(self, session_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in session_id)
        return self.root / f"{safe}.json"

    def upload_dir(self, session_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in session_id)
        directory = self.root / safe / "uploads"
        directory.mkdir(parents=True, exist_ok=True)
        return directory
