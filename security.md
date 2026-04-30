# DRAFT Table Security Boundary

DRAFT Table is a local-first helper for a DRAFT content repository. It is not a
credential broker and does not store AI provider API keys.

## Local Binding

The web UI binds to `127.0.0.1` by default. Phase 1 rejects non-localhost hosts
from the CLI because the app is designed for a single user's workstation.

## Provider Credentials

DRAFT Table never asks the user to paste provider API keys, access tokens, or
refresh tokens. Provider CLIs own their own authentication:

- Codex owns Codex/OpenAI login state.
- Claude Code owns Claude login state.
- Gemini CLI owns Google login state.
- Local LLM mode talks to an Ollama-compatible localhost endpoint.
- Custom command mode executes a configured local command.

Phase 1 detects provider CLI executables with `PATH` lookup only. It does not
read provider credential files.

## GitHub Credentials

GitHub authentication is used only for repository clone, pull, commit, push,
and future pull-request operations. DRAFT Table prefers GitHub CLI token
management through `gh auth login`. It does not write GitHub tokens to
`~/.draft-table/config.yaml`.

If a device-flow fallback is added later, tokens must be stored through the OS
keychain or another platform credential store, not plaintext app config.

## App Config

`~/.draft-table/config.yaml` may store:

- framework repo path
- content repo path
- provider type
- provider executable path
- selected model name
- localhost endpoint for local LLM mode
- non-secret preferences

Config save logic strips unknown secret-looking keys. Diagnostic output uses
redaction for keys such as `api_key`, `access_token`, `refresh_token`,
`client_secret`, `password`, `secret`, and `token`.

## User Interface Boundary

The content repo working tree is the source of truth, but DRAFT Table should
not show raw YAML code to users. Future AI drafting features should present
proposed changes as artifact-level summaries, interview answers, validation
results, and commit-ready change sets. YAML may be written to the working tree
internally, but users who want to inspect or edit YAML should use Git or their
preferred coding tool outside DRAFT Table.
