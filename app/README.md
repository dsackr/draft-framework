# DRAFT App

The DRAFT App is the shared internal web application and API surface for a
company DRAFT workspace. It is designed so the browser UI and AI agents use the
same operations:

- resolve the effective framework model
- inspect catalog and configuration objects
- initialize private workspace structure
- write catalog objects and patch-style configuration overrides
- validate workspace changes
- commit and publish through Git/GitHub workflows
- detect pinned framework update opportunities
- expose Draftsman AI mode configuration without storing API keys in workspace
  files

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
  bash -s -- --workspace-dir /path/to/company-draft-workspace
```

PowerShell custom workspace path:

```powershell
irm https://raw.githubusercontent.com/dsackr/draft-framework/main/install.ps1 -OutFile install.ps1
.\install.ps1 -WorkspaceDir "C:\DRAFT\workspace"
```

Manual setup:

```bash
cd app/api
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
DRAFT_WORKSPACE=/path/to/company-draft-workspace uvicorn draft_app.main:app --reload
```

For local mode, GitHub operations expect the user to already be authenticated
with `gh auth login` and normal Git credentials. Shared deployment mode should
use a GitHub App or OAuth integration rather than storing tokens in tracked
workspace files.

Useful API routes:

- `POST /api/workspace/init`
- `GET /api/workspace/effective-model`
- `POST /api/objects/upsert`
- `POST /api/object-patches/upsert`
- `POST /api/workspace/validate`
- `POST /api/git/commit`
- `POST /api/publish`
- `GET /api/framework/updates`
- `GET /api/draftsman/providers`
- `GET /api/draftsman/config`
- `POST /api/draftsman/chat`

See [DEPLOYMENT.md](DEPLOYMENT.md) for the container entrypoint.
