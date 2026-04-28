# DRAFT App

The DRAFT App is the shared internal web application and API surface for a
company DRAFT workspace. It is designed so the browser UI and AI agents use the
same operations:

- start from a branded Drafting Table workspace
- browse the effective catalog with the same generated browser shape used by
  GitHub Pages
- ask the Draftsman for catalog changes directly from the app-served catalog
  browser
- resolve the effective framework model
- inspect catalog and configuration objects
- use installer-created private workspace structure
- write catalog objects and patch-style configuration overrides
- validate workspace changes
- commit and publish through Git/GitHub workflows
- detect pinned framework update opportunities
- expose Draftsman runtime status without storing API keys or OAuth token
  values in workspace files

The browser UI uses a dark theme by default and opens to a Welcome screen. The
Drafting Table accepts natural-language prompts and uploaded source material
without asking users for object IDs. The Architecture entry opens the generated
catalog browser as a full-page experience. When that browser is served by the
app, it shows the workspace catalog name and exposes a Draftsman box in the
left navigation for guided updates. When the same browser is published through
GitHub Pages, it stays read-only and does not show the Draftsman. The Setup tab
handles runtime status, per-user ChatGPT/Codex sign-in, and Git publishing
controls.

First-run configuration is intentionally text based. The installer asks which
private GitHub repo DRAFT should use for company content, validates access with
`gh auth`, clones that repo, populates required folders, commits setup to the
configured working branch, optionally starts OpenAI OAuth for the embedded
Draftsman, then starts the app and opens the browser.

Local development starts the API against a workspace path:

```bash
curl -fsSL https://raw.githubusercontent.com/dsackr/draft-framework/main/install.sh | bash
```

PowerShell on Windows:

```powershell
irm https://raw.githubusercontent.com/dsackr/draft-framework/main/install.ps1 | iex
```

For a custom workspace path:

```bash
curl -fsSL https://raw.githubusercontent.com/dsackr/draft-framework/main/install.sh | \
  bash -s -- --content-repo owner/private-draft-catalog --workspace-dir /path/to/company-draft-workspace
```

PowerShell custom workspace path:

```powershell
irm https://raw.githubusercontent.com/dsackr/draft-framework/main/install.ps1 -OutFile install.ps1
.\install.ps1 -ContentRepo "owner/private-draft-catalog" -WorkspaceDir "C:\DRAFT\workspace"
```

After install, restart the app from the framework repo:

```powershell
.\run.ps1
```

or with a custom workspace:

```powershell
.\run.ps1 -WorkspaceDir "C:\DRAFT\workspace"
```

Manual setup:

```bash
cd app/api
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
DRAFT_WORKSPACE=/path/to/company-draft-workspace uvicorn draft_app.main:app --app-dir app/api --reload
```

For local mode, GitHub operations expect the user to already be authenticated
with `gh auth login` and normal Git credentials. Shared deployment mode should
use a GitHub App or OAuth integration rather than storing tokens in tracked
workspace files.

Useful API routes:

- `POST /api/workspace/init`
- `GET /api/workspace/effective-model`
- `GET /api/catalog/browser`
- `POST /api/objects/upsert`
- `POST /api/object-patches/upsert`
- `POST /api/workspace/validate`
- `POST /api/git/commit`
- `POST /api/publish`
- `GET /api/framework/updates`
- `GET /api/draftsman/providers`
- `GET /api/draftsman/config`
- `PUT /api/draftsman/config`
- `GET /api/draftsman/oauth/openai/status`
- `GET /api/draftsman/oauth/openai/start`
- `POST /api/draftsman/oauth/openai/complete`
- `POST /api/draftsman/oauth/openai/import-codex`
- `POST /api/draftsman/oauth/openai/logout`
- `POST /api/draftsman/chat`

See [DEPLOYMENT.md](DEPLOYMENT.md) for the container entrypoint.
