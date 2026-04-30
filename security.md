# DRAFT Table Security Boundary

DRAFT Table is a local-first helper for a company DRAFT repository. It is not a
credential broker and does not store AI provider API keys.

## Network Binding

The web UI binds to `0.0.0.0` by default so another device on the same LAN can
reach the drafting table. Startup output prints the LAN URL and local URL.

Use local-only binding when working on an untrusted network:

```bash
draft-table serve --host 127.0.0.1
```

DRAFT Table is still local-first, but LAN binding means other users on the same
network may be able to open the UI if firewall rules allow it. Run LAN mode only
on trusted networks.

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

- installed framework repo path
- company DRAFT repo path
- provider type
- provider executable path
- selected model name
- localhost endpoint for local LLM mode
- non-secret preferences

Config save logic strips unknown secret-looking keys. Diagnostic output uses
redaction for keys such as `api_key`, `access_token`, `refresh_token`,
`client_secret`, `password`, `secret`, and `token`.

## User Interface Boundary

The company DRAFT repo working tree is the source of truth, but DRAFT Table should
not show raw YAML code to users. Future AI drafting features should present
proposed changes as artifact-level summaries, interview answers, validation
results, and commit-ready change sets. YAML may be written to the working tree
internally, but users who want to inspect or edit YAML should use Git or their
preferred coding tool outside DRAFT Table.

## Vendored Framework Boundary

During onboarding, DRAFT Table copies the selected framework version into the
company repo at `.draft/framework/`. Normal Draftsman use reads that local copy
instead of calling back to the public upstream repo. Framework refresh is an
explicit user action through `draft-table framework refresh`; the resulting
`.draft/framework/` and `.draft/framework.lock` changes are ordinary Git
changes that should be reviewed before commit.
