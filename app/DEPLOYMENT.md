# Deploying The DRAFT App

The app is designed to run as an internal web service with the company private
workspace mounted or cloned separately from the framework image.

Build the image from the framework repo:

```bash
docker build -f app/Dockerfile -t draft-app .
```

Run against a mounted workspace:

```bash
docker run --rm -p 8000:8000 \
  -e DRAFT_WORKSPACE=/workspace \
  -v /path/to/company-draft-workspace:/workspace \
  draft-app
```

The mounted workspace must be writable by the app process. The app writes only
workspace-owned paths: `catalog/`, `configurations/`, and `.draft/`.

Local developer mode can use `gh auth` and local Git credentials. Shared
internal deployments should use a GitHub App or OAuth integration so commits
and pull requests are attributable and credentials are not stored in tracked
workspace files.
