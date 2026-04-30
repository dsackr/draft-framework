from __future__ import annotations

from pathlib import Path
import os


PACKAGE_ROOT = Path(__file__).resolve().parent
def discover_repo_root() -> Path:
    env_root = os.environ.get("DRAFT_TABLE_FRAMEWORK_REPO", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()
    for root in (PACKAGE_ROOT, *PACKAGE_ROOT.parents, Path.cwd(), *Path.cwd().parents):
        if (root / "framework" / "tools" / "validate.py").exists():
            return root
    return PACKAGE_ROOT.parent


REPO_ROOT = discover_repo_root()
FRAMEWORK_ROOT = REPO_ROOT / "framework"
DEFAULT_CONFIG_DIR = Path.home() / ".draft-table"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_WORKSPACE_PARENT = Path.home() / "draft-table-workspaces"
