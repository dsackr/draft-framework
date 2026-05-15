#!/usr/bin/env bash
set -euo pipefail

DRAFT_TABLE_REPO_URL="${DRAFT_TABLE_REPO_URL:-https://github.com/getdraft/draftsman.git}"
DRAFT_TABLE_REF="${DRAFT_TABLE_REF:-main}"
DRAFT_TABLE_INSTALL_DIR="${DRAFT_TABLE_INSTALL_DIR:-$HOME/draft-framework}"
DRAFT_TABLE_VENV="${DRAFT_TABLE_VENV:-$DRAFT_TABLE_INSTALL_DIR/.venv}"

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_command git
need_command python3

run_onboarding() {
  if [[ ! -r /dev/tty ]]; then
    echo "DRAFT Table onboarding needs an interactive terminal." >&2
    echo "Run $DRAFT_TABLE_VENV/bin/draft-table onboard after installation completes." >&2
    exit 1
  fi
  "$DRAFT_TABLE_VENV/bin/draft-table" onboard </dev/tty
}

if [[ -d "$DRAFT_TABLE_INSTALL_DIR/.git" ]]; then
  git -C "$DRAFT_TABLE_INSTALL_DIR" fetch origin "$DRAFT_TABLE_REF"
  git -C "$DRAFT_TABLE_INSTALL_DIR" checkout "$DRAFT_TABLE_REF"
  git -C "$DRAFT_TABLE_INSTALL_DIR" pull --ff-only origin "$DRAFT_TABLE_REF"
else
  mkdir -p "$(dirname "$DRAFT_TABLE_INSTALL_DIR")"
  git clone --branch "$DRAFT_TABLE_REF" "$DRAFT_TABLE_REPO_URL" "$DRAFT_TABLE_INSTALL_DIR"
fi

python3 -m venv "$DRAFT_TABLE_VENV"
"$DRAFT_TABLE_VENV/bin/python" -m pip install --upgrade pip
"$DRAFT_TABLE_VENV/bin/python" -m pip install -e "$DRAFT_TABLE_INSTALL_DIR"
run_onboarding
echo "Starting DRAFT Table web UI. Press Ctrl-C to stop it."
"$DRAFT_TABLE_VENV/bin/draft-table" serve
