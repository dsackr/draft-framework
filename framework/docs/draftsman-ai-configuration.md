# Draftsman AI Configuration

## Modes

DRAFT supports two Draftsman operating modes in workspace configuration.

`external` mode means the AI runs outside the DRAFT App. The user points an AI
agent at the repo, and the agent follows `AGENTS.md`, `AI_INDEX.md`, and the
DRAFT App API. This mode is available now and does not require AI credentials
inside the app.

`embedded` mode means the DRAFT App hosts the Draftsman chat experience. The
app provides the UI, builds the effective-model context, and calls an approved
AI provider. This mode is configuration-only in the current implementation.

`disabled` mode removes Draftsman features from the workspace.

## First Embedded Provider

The first embedded-provider configuration is intentionally limited to OpenAI
with OAuth:

```yaml
draftsman:
  mode: external
  embedded:
    enabled: false
    provider: openai
    model: <openai-model-id>
    auth:
      type: oauth
      clientIdRef: DRAFT_OPENAI_OAUTH_CLIENT_ID
      clientSecretRef: DRAFT_OPENAI_OAUTH_CLIENT_SECRET
      redirectUri: http://127.0.0.1:8000/api/draftsman/oauth/openai/callback
      tokenStorage: runtime
      apiKeysAllowed: false
```

Do not store API keys, OAuth client secrets, access tokens, or refresh tokens in
`.draft/workspace.yaml` or any other tracked workspace file. Configuration may
refer to environment variables or deployment secret names, but the secret
values must live outside Git.

## Current OpenAI Constraint

The OpenAI API documentation currently describes API-key authentication for
direct API calls. OpenAI documentation also describes OAuth for ChatGPT
Actions, apps, and connector-style integrations where ChatGPT calls a third
party application.

Because DRAFT should not store API keys in workspace files, the embedded
Draftsman implementation must wait until OAuth-based OpenAI access is confirmed
for this app-to-OpenAI model-calling use case, or until an approved server-side
secret-management design is accepted.

External-agent mode is not blocked by this. A user can use ChatGPT, Codex, or
another external AI tool as the Draftsman by giving it the repo and app API
contract.

## App API

The app exposes Draftsman configuration routes:

- `GET /api/draftsman/providers`
- `GET /api/draftsman/config`
- `POST /api/draftsman/chat`
- `GET /api/draftsman/oauth/openai/start`
- `GET /api/draftsman/oauth/openai/callback`

`POST /api/draftsman/chat` currently returns `501` for embedded mode. This is
intentional: the app can validate and expose configuration without pretending
that model calls are implemented.

## Authority Boundary

AI reasoning is advisory. DRAFT remains authoritative for:

- effective-model loading
- schema and ODC interpretation
- compliance-profile applicability
- object and patch writes
- validation
- Git commit, push, and publish flows

The AI provider should never receive Git credentials or raw secrets, and should
not write files directly. The app/API executes trusted actions after validation.
