#!/usr/bin/env bash
set -euo pipefail

DRAFT_REPO_URL="${DRAFT_REPO_URL:-https://github.com/dsackr/draft-framework.git}"
DRAFT_REF="${DRAFT_REF:-main}"
DRAFT_HOST="${DRAFT_HOST:-127.0.0.1}"
DRAFT_PORT="${DRAFT_PORT:-8000}"
DRAFT_START_APP="${DRAFT_START_APP:-1}"
DRAFT_CREATE_WORKSPACE="${DRAFT_CREATE_WORKSPACE:-1}"

INSTALL_DIR_SET=0
WORKSPACE_DIR_SET=0

if [[ -n "${DRAFT_INSTALL_DIR:-}" ]]; then
  INSTALL_DIR_SET=1
fi
if [[ -n "${DRAFT_WORKSPACE_DIR:-}" ]]; then
  WORKSPACE_DIR_SET=1
fi

usage() {
  cat <<'EOF'
DRAFT installer

Usage:
  curl -fsSL https://raw.githubusercontent.com/dsackr/draft-framework/main/install.sh | bash
  bash install.sh [options]

Options:
  --install-dir PATH     Framework install path. Defaults to current repo when run inside one, otherwise ~/draft-framework.
  --workspace-dir PATH   Workspace path. Defaults to ~/draft-workspace.
  --repo URL             Framework Git URL.
  --ref REF              Framework branch, tag, or commit. Defaults to main.
  --host HOST            App bind host. Defaults to 127.0.0.1.
  --port PORT            App port. Defaults to 8000.
  --no-start             Install only; do not start the app.
  --no-workspace         Do not create a workspace skeleton.
  --help                 Show this help.

Environment variables:
  DRAFT_INSTALL_DIR, DRAFT_WORKSPACE_DIR, DRAFT_REPO_URL, DRAFT_REF,
  DRAFT_HOST, DRAFT_PORT, DRAFT_START_APP, DRAFT_CREATE_WORKSPACE
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      DRAFT_INSTALL_DIR="$2"
      INSTALL_DIR_SET=1
      shift 2
      ;;
    --workspace-dir)
      DRAFT_WORKSPACE_DIR="$2"
      WORKSPACE_DIR_SET=1
      shift 2
      ;;
    --repo)
      DRAFT_REPO_URL="$2"
      shift 2
      ;;
    --ref)
      DRAFT_REF="$2"
      shift 2
      ;;
    --host)
      DRAFT_HOST="$2"
      shift 2
      ;;
    --port)
      DRAFT_PORT="$2"
      shift 2
      ;;
    --no-start)
      DRAFT_START_APP=0
      shift
      ;;
    --no-workspace)
      DRAFT_CREATE_WORKSPACE=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

log() {
  printf '\n==> %s\n' "$1"
}

absolute_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    ~*) printf '%s\n' "${1/#\~/$HOME}" ;;
    *) printf '%s\n' "$PWD/$1" ;;
  esac
}

escape_sed() {
  printf '%s' "$1" | sed 's/[\/&]/\\&/g'
}

render_template() {
  local source="$1"
  local target="$2"
  local workspace_name="$3"
  local framework_commit="$4"
  local timestamp="$5"

  if [[ -f "$target" ]]; then
    return
  fi

  mkdir -p "$(dirname "$target")"
  sed \
    -e "s|<company-draft-workspace>|$(escape_sed "$workspace_name")|g" \
    -e "s|<private-repo>|$(escape_sed "$workspace_name")|g" \
    -e "s|<tag-or-branch>|$(escape_sed "$DRAFT_REF")|g" \
    -e "s|<resolved-sha>|$(escape_sed "$framework_commit")|g" \
    -e "s|<iso-8601-timestamp>|$(escape_sed "$timestamp")|g" \
    "$source" > "$target"
}

copy_workspace_template() {
  local framework_dir="$1"
  local workspace_dir="$2"
  local framework_commit="$3"
  local template_root="$framework_dir/templates/workspace"
  local workspace_name
  local timestamp

  workspace_name="$(basename "$workspace_dir")"
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  mkdir -p "$workspace_dir"

  (
    cd "$template_root"
    while IFS= read -r directory; do
      mkdir -p "$workspace_dir/$directory"
    done < <(find . -type d -print)

    while IFS= read -r file; do
      case "$file" in
        ./.draft/workspace.yaml.tmpl)
          render_template "$template_root/$file" "$workspace_dir/.draft/workspace.yaml" "$workspace_name" "$framework_commit" "$timestamp"
          ;;
        ./.draft/framework.lock.tmpl)
          render_template "$template_root/$file" "$workspace_dir/.draft/framework.lock" "$workspace_name" "$framework_commit" "$timestamp"
          ;;
        ./.gitignore.tmpl)
          render_template "$template_root/$file" "$workspace_dir/.gitignore" "$workspace_name" "$framework_commit" "$timestamp"
          ;;
        *.tmpl)
          ;;
        *)
          if [[ ! -f "$workspace_dir/$file" ]]; then
            cp "$template_root/$file" "$workspace_dir/$file"
          fi
          ;;
      esac
    done < <(find . -type f -print)
  )

  if [[ ! -d "$workspace_dir/.git" ]]; then
    git -C "$workspace_dir" init >/dev/null
    git -C "$workspace_dir" checkout -b dev >/dev/null 2>&1 || true
  fi
}

need_command git
need_command python3
need_command sed
need_command date

if [[ "$INSTALL_DIR_SET" -eq 0 && -f "$PWD/app/api/requirements.txt" && -f "$PWD/framework/tools/validate.py" ]]; then
  DRAFT_INSTALL_DIR="$PWD"
else
  DRAFT_INSTALL_DIR="${DRAFT_INSTALL_DIR:-$HOME/draft-framework}"
fi

if [[ "$WORKSPACE_DIR_SET" -eq 0 ]]; then
  DRAFT_WORKSPACE_DIR="${DRAFT_WORKSPACE_DIR:-$HOME/draft-workspace}"
fi

DRAFT_INSTALL_DIR="$(absolute_path "$DRAFT_INSTALL_DIR")"
DRAFT_WORKSPACE_DIR="$(absolute_path "$DRAFT_WORKSPACE_DIR")"
VENV_DIR="$DRAFT_INSTALL_DIR/app/api/.venv"

log "Installing DRAFT framework"
if [[ -d "$DRAFT_INSTALL_DIR/.git" ]]; then
  if [[ -n "$(git -C "$DRAFT_INSTALL_DIR" status --porcelain)" ]]; then
    echo "Install directory has uncommitted changes: $DRAFT_INSTALL_DIR" >&2
    echo "Commit or stash those changes, or choose another --install-dir." >&2
    exit 1
  fi
  git -C "$DRAFT_INSTALL_DIR" fetch origin
  if git -C "$DRAFT_INSTALL_DIR" rev-parse --verify "origin/$DRAFT_REF" >/dev/null 2>&1; then
    git -C "$DRAFT_INSTALL_DIR" checkout "$DRAFT_REF"
    git -C "$DRAFT_INSTALL_DIR" pull --ff-only origin "$DRAFT_REF"
  else
    git -C "$DRAFT_INSTALL_DIR" checkout "$DRAFT_REF"
  fi
elif [[ -e "$DRAFT_INSTALL_DIR" ]]; then
  echo "Install path exists but is not a Git checkout: $DRAFT_INSTALL_DIR" >&2
  exit 1
else
  git clone "$DRAFT_REPO_URL" "$DRAFT_INSTALL_DIR"
  git -C "$DRAFT_INSTALL_DIR" checkout "$DRAFT_REF"
fi

FRAMEWORK_COMMIT="$(git -C "$DRAFT_INSTALL_DIR" rev-parse HEAD)"

log "Installing Python app dependencies"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install -r "$DRAFT_INSTALL_DIR/app/api/requirements.txt"

if [[ "$DRAFT_CREATE_WORKSPACE" == "1" ]]; then
  log "Creating DRAFT workspace"
  copy_workspace_template "$DRAFT_INSTALL_DIR" "$DRAFT_WORKSPACE_DIR" "$FRAMEWORK_COMMIT"
fi

cat <<EOF

DRAFT install complete.

Framework: $DRAFT_INSTALL_DIR
Workspace: $DRAFT_WORKSPACE_DIR
App URL:   http://$DRAFT_HOST:$DRAFT_PORT

To start later:
  cd "$DRAFT_INSTALL_DIR"
  DRAFT_WORKSPACE="$DRAFT_WORKSPACE_DIR" "$VENV_DIR/bin/python" -m uvicorn app.api.draft_app.main:app --host "$DRAFT_HOST" --port "$DRAFT_PORT"

EOF

if [[ "$DRAFT_START_APP" == "1" ]]; then
  log "Starting DRAFT App"
  cd "$DRAFT_INSTALL_DIR"
  exec env DRAFT_WORKSPACE="$DRAFT_WORKSPACE_DIR" "$VENV_DIR/bin/python" -m uvicorn app.api.draft_app.main:app --host "$DRAFT_HOST" --port "$DRAFT_PORT"
fi
