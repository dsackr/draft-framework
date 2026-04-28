# Draftsman AI Configuration

## Modes

DRAFT supports three Draftsman operating modes in workspace configuration.

`external` mode means the AI runs outside the DRAFT App. The user points an AI
agent at the repo, and the agent follows `AGENTS.md`, `AI_INDEX.md`, and the
DRAFT App API. This mode is available now and does not require AI credentials
inside the app.

`embedded` mode means the DRAFT App hosts the Draftsman chat experience. The
app provides the UI, builds the effective-model context, and calls the approved
AI provider with the signed-in user's account.

`disabled` mode removes Draftsman features from the workspace.

## First Embedded Provider

The first embedded provider is OpenAI through ChatGPT/Codex OAuth. This follows
the same user-owned subscription model used by Codex-style tools: each user
signs in with their own ChatGPT/Codex account, and the app uses that user's
session for embedded Draftsman chat.

Workspace configuration contains only non-secret setup:

```yaml
draftsman:
  mode: embedded
  embedded:
    enabled: true
    provider: openai
    model: gpt-5.5
    auth:
      type: oauth
      clientId: app_EMoamEEZ73f0CkXaXp7hrann
      redirectUri: http://localhost:1455/auth/callback
      tokenStorage: user-local
      apiKeysAllowed: false
```

Do not store API keys, access tokens, refresh tokens, ID tokens, or OAuth
client secrets in `.draft/workspace.yaml` or any other tracked workspace file.
Local DRAFT app tokens are stored under `~/.draft/auth-profiles.json` with
user-only file permissions. This file is outside the company workspace repo.

## Local OAuth Flow

The DRAFT App uses an OpenAI Codex-style OAuth/PKCE flow:

1. During install, the user chooses to set up the AI Draftsman and selects
   OpenAI OAuth. The Setup tab can also start sign-in later.
2. The app starts a local callback listener on `127.0.0.1:1455`.
3. The user signs in with ChatGPT in the browser.
4. OpenAI redirects to `http://localhost:1455/auth/callback`.
5. The app exchanges the code for the user's tokens and stores them outside Git.
6. `POST /api/draftsman/chat` can call the embedded Draftsman using that user's
   signed-in ChatGPT/Codex account.

The Setup tab also provides `Use Existing Codex Login`, which imports a local
`~/.codex/auth.json` session into DRAFT's `~/.draft/` token store.

## Shared App Boundary

The local Codex OAuth callback assumes the browser and DRAFT App run on the
same workstation. A shared internal deployment must use a per-user server-side
OAuth/session design before enabling embedded chat for multiple users. It must
not place one user's token where another user can use it.

## App API

The app exposes Draftsman configuration and auth routes:

- `GET /api/draftsman/providers`
- `GET /api/draftsman/config`
- `PUT /api/draftsman/config`
- `GET /api/draftsman/oauth/openai/status`
- `GET /api/draftsman/oauth/openai/start`
- `POST /api/draftsman/oauth/openai/complete`
- `POST /api/draftsman/oauth/openai/import-codex`
- `POST /api/draftsman/oauth/openai/logout`
- `POST /api/draftsman/chat`

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
