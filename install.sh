#!/usr/bin/env bash
set -euo pipefail

DRAFT_REPO_URL="${DRAFT_REPO_URL:-https://github.com/dsackr/draft-framework.git}"
DRAFT_REF="${DRAFT_REF:-main}"
DRAFT_HOST="${DRAFT_HOST:-127.0.0.1}"
DRAFT_PORT="${DRAFT_PORT:-8000}"
DRAFT_START_APP="${DRAFT_START_APP:-1}"
DRAFT_CREATE_WORKSPACE="${DRAFT_CREATE_WORKSPACE:-1}"
DRAFT_CONTENT_REPO="${DRAFT_CONTENT_REPO:-}"
DRAFT_DEV_BRANCH="${DRAFT_DEV_BRANCH:-draft-dev}"
DRAFT_SETUP_DRAFTSMAN="${DRAFT_SETUP_DRAFTSMAN:-}"
DRAFT_CONTENT_OWNER=""
DRAFT_CONTENT_NAME=""
DRAFT_DEFAULT_BRANCH="main"

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
  --content-repo REPO    Company private GitHub repo for DRAFT content, e.g. org/repo.
  --dev-branch BRANCH    Non-protected working branch. Defaults to draft-dev.
  --setup-draftsman      Start ChatGPT/Codex sign-in after setup.
  --help                 Show this help.

Environment variables:
  DRAFT_INSTALL_DIR, DRAFT_WORKSPACE_DIR, DRAFT_REPO_URL, DRAFT_REF,
  DRAFT_HOST, DRAFT_PORT, DRAFT_START_APP, DRAFT_CREATE_WORKSPACE,
  DRAFT_CONTENT_REPO, DRAFT_DEV_BRANCH, DRAFT_SETUP_DRAFTSMAN
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
    --content-repo)
      DRAFT_CONTENT_REPO="$2"
      shift 2
      ;;
    --dev-branch)
      DRAFT_DEV_BRANCH="$2"
      shift 2
      ;;
    --setup-draftsman)
      DRAFT_SETUP_DRAFTSMAN=1
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

can_prompt() {
  [[ -r /dev/tty ]]
}

ask() {
  local prompt="$1"
  local default="${2:-}"
  local answer
  if ! can_prompt; then
    printf '%s\n' "$default"
    return
  fi
  if [[ -n "$default" ]]; then
    read -r -p "$prompt [$default]: " answer < /dev/tty
    printf '%s\n' "${answer:-$default}"
  else
    read -r -p "$prompt: " answer < /dev/tty
    printf '%s\n' "$answer"
  fi
}

ask_yes_no() {
  local prompt="$1"
  local default="${2:-n}"
  local answer
  if ! can_prompt; then
    [[ "$default" =~ ^[Yy] ]]
    return
  fi
  read -r -p "$prompt [$default]: " answer < /dev/tty
  answer="${answer:-$default}"
  [[ "$answer" =~ ^[Yy] ]]
}

select_draftsman_provider() {
  local answer
  answer="$(ask "Draftsman provider. OpenAI OAuth is available now; other models are coming soon" "OpenAI OAuth")"
  if [[ ! "$answer" =~ ^[Oo]pen[Aa][Ii]([[:space:]]+[Oo][Aa]uth)?$ ]]; then
    printf 'Only OpenAI OAuth is available in this version; continuing with OpenAI OAuth.\n'
  fi
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
    -e "s|<github-org>|$(escape_sed "${DRAFT_CONTENT_OWNER:-github-org}")|g" \
    -e "s|<private-repo>|$(escape_sed "${DRAFT_CONTENT_NAME:-$workspace_name}")|g" \
    -e "s|<default-branch>|$(escape_sed "$DRAFT_DEFAULT_BRANCH")|g" \
    -e "s|<dev-branch>|$(escape_sed "$DRAFT_DEV_BRANCH")|g" \
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
    git -C "$workspace_dir" checkout -b "$DRAFT_DEV_BRANCH" >/dev/null 2>&1 || true
  fi
}

repo_slug() {
  local repo="$1"
  repo="${repo#https://github.com/}"
  repo="${repo#http://github.com/}"
  repo="${repo#git@github.com:}"
  repo="${repo%.git}"
  printf '%s\n' "$repo"
}

configure_content_repo() {
  if [[ -z "$DRAFT_CONTENT_REPO" ]] && can_prompt; then
    DRAFT_CONTENT_REPO="$(ask "What GitHub repo will you use with DRAFT? Use owner/repo or a GitHub URL")"
  fi
  if [[ -z "$DRAFT_CONTENT_REPO" ]]; then
    echo "A company content repo is required. Pass --content-repo owner/repo or set DRAFT_CONTENT_REPO." >&2
    exit 1
  fi

  need_command gh
  gh auth status >/dev/null

  local slug info name_with_owner
  slug="$(repo_slug "$DRAFT_CONTENT_REPO")"
  log "Checking GitHub repo access: $slug"
  info="$(gh repo view "$slug" --json nameWithOwner,defaultBranchRef --jq '.nameWithOwner + " " + (.defaultBranchRef.name // "main")')"
  name_with_owner="${info% *}"
  DRAFT_DEFAULT_BRANCH="${info##* }"
  DRAFT_CONTENT_OWNER="${name_with_owner%%/*}"
  DRAFT_CONTENT_NAME="${name_with_owner##*/}"

  if [[ -d "$DRAFT_WORKSPACE_DIR/.git" ]]; then
    git -C "$DRAFT_WORKSPACE_DIR" fetch origin
  elif [[ -e "$DRAFT_WORKSPACE_DIR" && -n "$(find "$DRAFT_WORKSPACE_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
    echo "Workspace path exists but is not an empty Git checkout: $DRAFT_WORKSPACE_DIR" >&2
    exit 1
  else
    mkdir -p "$(dirname "$DRAFT_WORKSPACE_DIR")"
    gh repo clone "$slug" "$DRAFT_WORKSPACE_DIR"
  fi

  git -C "$DRAFT_WORKSPACE_DIR" fetch origin || true
  if git -C "$DRAFT_WORKSPACE_DIR" show-ref --verify --quiet "refs/remotes/origin/$DRAFT_DEV_BRANCH"; then
    git -C "$DRAFT_WORKSPACE_DIR" checkout "$DRAFT_DEV_BRANCH"
    git -C "$DRAFT_WORKSPACE_DIR" pull --ff-only origin "$DRAFT_DEV_BRANCH" || true
  elif git -C "$DRAFT_WORKSPACE_DIR" rev-parse --verify HEAD >/dev/null 2>&1; then
    git -C "$DRAFT_WORKSPACE_DIR" checkout -B "$DRAFT_DEV_BRANCH"
  else
    git -C "$DRAFT_WORKSPACE_DIR" checkout --orphan "$DRAFT_DEV_BRANCH"
  fi
}

commit_workspace_setup() {
  git -C "$DRAFT_WORKSPACE_DIR" add .gitignore .draft catalog configurations
  if git -C "$DRAFT_WORKSPACE_DIR" diff --cached --quiet; then
    return
  fi
  git -C "$DRAFT_WORKSPACE_DIR" commit -m "Initialize DRAFT workspace"
  git -C "$DRAFT_WORKSPACE_DIR" push -u origin "$DRAFT_DEV_BRANCH"
}

open_url() {
  local url="$1"
  if command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 || true
  else
    printf 'Open this URL: %s\n' "$url"
  fi
}

wait_for_app() {
  local url="http://$DRAFT_HOST:$DRAFT_PORT/api/health"
  local attempt
  for attempt in $(seq 1 40); do
    if python3 - "$url" >/dev/null 2>&1 <<'PY'
import sys, urllib.request
urllib.request.urlopen(sys.argv[1], timeout=1).read()
PY
    then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

start_draftsman_oauth() {
  local start_url="http://$DRAFT_HOST:$DRAFT_PORT/api/draftsman/oauth/openai/start?workspace=$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$DRAFT_WORKSPACE_DIR")"
  local auth_url
  auth_url="$(python3 - "$start_url" <<'PY'
import json, sys, urllib.request
data = json.load(urllib.request.urlopen(sys.argv[1], timeout=10))
print(data["authUrl"])
PY
)"
  printf '\nOpening ChatGPT sign-in for DRAFT Draftsman.\n'
  open_url "$auth_url"
}

enable_embedded_draftsman() {
  "$VENV_DIR/bin/python" - "$DRAFT_WORKSPACE_DIR/.draft/workspace.yaml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
draftsman = config.setdefault("draftsman", {})
draftsman["mode"] = "embedded"
embedded = draftsman.setdefault("embedded", {})
embedded["enabled"] = True
embedded["provider"] = "openai"
embedded["model"] = embedded.get("model") or "gpt-5.5"
auth = embedded.setdefault("auth", {})
for key in (
    "accessToken",
    "access_token",
    "apiKey",
    "api_key",
    "apiKeyRef",
    "api_key_ref",
    "clientSecret",
    "client_secret",
    "clientSecretRef",
    "client_secret_ref",
    "refreshToken",
    "refresh_token",
):
    auth.pop(key, None)
auth.update(
    {
        "type": "oauth",
        "clientId": "app_EMoamEEZ73f0CkXaXp7hrann",
        "redirectUri": "http://localhost:1455/auth/callback",
        "tokenStorage": "user-local",
        "apiKeysAllowed": False,
    }
)
path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
PY
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
  log "Configuring company content repo"
  configure_content_repo
  if [[ -z "$DRAFT_SETUP_DRAFTSMAN" ]] && can_prompt; then
    if ask_yes_no "Set up the AI Draftsman now? OpenAI OAuth is available; other models are coming soon" "y"; then
      DRAFT_SETUP_DRAFTSMAN=1
      select_draftsman_provider
    else
      DRAFT_SETUP_DRAFTSMAN=0
    fi
  fi
  log "Checking DRAFT workspace folders"
  copy_workspace_template "$DRAFT_INSTALL_DIR" "$DRAFT_WORKSPACE_DIR" "$FRAMEWORK_COMMIT"
  if [[ "$DRAFT_SETUP_DRAFTSMAN" == "1" ]]; then
    enable_embedded_draftsman
  fi
  commit_workspace_setup
fi

cat <<EOF

DRAFT install complete.

Framework: $DRAFT_INSTALL_DIR
Workspace: $DRAFT_WORKSPACE_DIR
App URL:   http://$DRAFT_HOST:$DRAFT_PORT

To start later:
  cd "$DRAFT_INSTALL_DIR/app/api"
  DRAFT_WORKSPACE="$DRAFT_WORKSPACE_DIR" "$VENV_DIR/bin/python" -m uvicorn draft_app.main:app --host "$DRAFT_HOST" --port "$DRAFT_PORT"

EOF

if [[ "$DRAFT_START_APP" == "1" ]]; then
  log "Starting DRAFT App"
  cd "$DRAFT_INSTALL_DIR/app/api"
  env DRAFT_WORKSPACE="$DRAFT_WORKSPACE_DIR" "$VENV_DIR/bin/python" -m uvicorn draft_app.main:app --host "$DRAFT_HOST" --port "$DRAFT_PORT" &
  APP_PID=$!
  if wait_for_app; then
    if [[ "$DRAFT_SETUP_DRAFTSMAN" == "1" ]]; then
      start_draftsman_oauth || true
    fi
    open_url "http://$DRAFT_HOST:$DRAFT_PORT"
  else
    echo "DRAFT App did not become ready on http://$DRAFT_HOST:$DRAFT_PORT" >&2
  fi
  wait "$APP_PID"
fi
