#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-dsackr/draft-framework}"
MILESTONE="v1.0"

require_gh() {
  if ! command -v gh >/dev/null 2>&1; then
    echo "GitHub CLI is required. Install gh, then rerun this script." >&2
    exit 1
  fi
  if ! gh auth status >/dev/null 2>&1; then
    echo "GitHub CLI is not authenticated. Run: gh auth login -h github.com" >&2
    exit 1
  fi
}

ensure_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  if gh label list --repo "$REPO" --search "$name" --json name --jq '.[].name' | grep -Fxq "$name"; then
    gh label edit "$name" --repo "$REPO" --color "$color" --description "$description" >/dev/null
  else
    gh label create "$name" --repo "$REPO" --color "$color" --description "$description" >/dev/null
  fi
}

ensure_milestone() {
  local number
  number="$(gh api "repos/$REPO/milestones?state=all" --jq ".[] | select(.title == \"$MILESTONE\") | .number" | head -n 1)"
  if [[ -z "$number" ]]; then
    gh api --method POST "repos/$REPO/milestones" \
      -f title="$MILESTONE" \
      -f state="open" \
      -f description="Tracks the remaining MVP work required for DRAFT 1.0 readiness." \
      >/dev/null
  else
    gh api --method PATCH "repos/$REPO/milestones/$number" -f state="open" >/dev/null
  fi
}

issue_exists() {
  local title="$1"
  gh issue list --repo "$REPO" --state all --limit 200 --json title --jq ".[].title" | grep -Fxq "$title"
}

create_issue() {
  local title="$1"
  local body_file="$2"
  shift 2
  local labels=("$@")
  local args=(--repo "$REPO" --title "$title" --body-file "$body_file" --milestone "$MILESTONE")

  for label in "${labels[@]}"; do
    args+=(--label "$label")
  done

  if issue_exists "$title"; then
    echo "Issue already exists: $title"
  else
    gh issue create "${args[@]}"
  fi
}

main() {
  require_gh

  ensure_label "v1.0" "5319e7" "Required for the first stable DRAFT compatibility baseline."
  ensure_label "mvp" "fbca04" "Minimum viable product work."
  ensure_label "deployment" "1d76db" "Deployment contract, environment, and runtime concerns."
  ensure_label "automation" "0e8a16" "Generated plans, IaC, pipeline, or automation work."
  ensure_label "catalog" "bfdadc" "Architecture catalog content and examples."
  ensure_label "compliance" "d93f0b" "Requirement Groups, evidence, governance, and controls."
  ensure_label "draftsman" "c5def5" "AI-assisted authoring and DRAFT Table workflow."
  ensure_milestone

  local tmp_dir
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir:-}"' EXIT

  cat > "$tmp_dir/deployment-contract.md" <<'ISSUE'
## Problem

DRAFT currently captures deployable architecture facts, but deployable is still mostly a semantic promise. The framework needs one explicit path from approved DRAFT objects to a generated deployment plan.

## MVP outcome

Define a minimal executable deployment contract that can translate one approved Software Deployment Pattern graph into a deployment manifest and dry-run plan.

## Acceptance criteria

- [ ] Add a machine-readable deployment target and environment binding contract.
- [ ] Generate a deployment manifest from an approved Software Deployment Pattern and its closed deployable object graph.
- [ ] Add one narrow adapter path for dry-run output, even if the first adapter only emits a neutral plan format rather than applying infrastructure.
- [ ] Block deployment plan generation when the graph contains unresolved Drafting Session questions, invalid references, not-compliant requirements, or unapproved required objects.
- [ ] Represent secrets only as references, never as literal values.
- [ ] Add validator coverage and documentation for the contract.

## Source

Tracked from `ROADMAP.md`.
ISSUE

  cat > "$tmp_dir/golden-workspace.md" <<'ISSUE'
## Problem

The framework has strong schemas, Requirement Groups, and validation logic, but the example catalog does not yet prove a complete product deployment path with compliance evidence.

## MVP outcome

Ship one complete golden workspace that demonstrates the intended DRAFT loop end to end.

## Acceptance criteria

- [ ] Include Technology Components, Host, Runtime Service, Data-at-Rest Service, Edge/Gateway Service, Product Service, Reference Architecture, Software Deployment Pattern, Decision Record, and Drafting Session examples.
- [ ] Activate at least one workspace-mode security or compliance Requirement Group.
- [ ] Record valid `requirementImplementations` evidence for the active group.
- [ ] Demonstrate acceptable-use Technology Component mappings through capabilities.
- [ ] Ensure the golden workspace validates without warnings.
- [ ] Regenerate the browser so topology, relationships, requirements, evidence, and acceptable-use views can be inspected.
- [ ] Document how maintainers should use the golden workspace as a regression target for v1.0 changes.

## Source

Tracked from `ROADMAP.md`.
ISSUE

  cat > "$tmp_dir/draftsman-workflow.md" <<'ISSUE'
## Problem

DRAFT Table has the first Draftsman loop, but production authoring still depends too much on provider-generated YAML and post-write validation.

## MVP outcome

Make Draftsman output structured, reviewable, repairable, and safe enough for governed company workspaces.

## Acceptance criteria

- [ ] Replace opaque YAML proposal content with a structured proposal model that can be validated before writing files.
- [ ] Show schema-aware review cards and diffs before apply.
- [ ] Map validation failures to actionable repair steps that the Draftsman can propose or perform.
- [ ] Record source provenance on every generated or materially updated artifact.
- [ ] Preserve Drafting Session state so interrupted work can resume without relying on chat history.
- [ ] Add branch, commit, and pull request workflow from DRAFT Table or document the minimum supported CLI path.
- [ ] Add tests that cover proposal validation, failed validation recovery, provenance capture, and resumable sessions.

## Source

Tracked from `ROADMAP.md`.
ISSUE

  create_issue "v1.0: executable deployment contract" "$tmp_dir/deployment-contract.md" \
    "v1.0" "mvp" "deployment" "automation"
  create_issue "v1.0: complete golden reference workspace" "$tmp_dir/golden-workspace.md" \
    "v1.0" "mvp" "catalog" "compliance"
  create_issue "v1.0: deterministic Draftsman production workflow" "$tmp_dir/draftsman-workflow.md" \
    "v1.0" "mvp" "draftsman" "compliance"
}

main "$@"
