# Draftsman Setup Mode

Setup mode is the first-run Draftsman conversation for a company DRAFT
workspace. It exists so enterprise architecture teams can make the Drafting
Table useful without turning onboarding into a long form-filling exercise.

Setup mode is not the same as `draft-table onboard`.

| Flow | Purpose |
|---|---|
| `draft-table onboard` | Selects or creates the company repo, vendors the framework, and stores local provider preferences. |
| Draftsman setup mode | Guides the architecture team through the minimum workspace and catalog decisions needed for useful drafting. |

## Setup Mode Contract

When setup mode starts, the Draftsman must show:

- current step
- next step
- what remains after the current step
- what can be revisited later
- one focused question, or at most three questions when the team needs choices

The Draftsman should not ask for UIDs, YAML fields, schema names, or exhaustive
inventories. It should use plain architecture language and record revisit-later
items instead of forcing perfect answers.

## Minimum Useful Setup

A workspace is useful enough for first drafting when these items exist or are
deliberately queued:

1. Private company DRAFT repo selected and framework vendored under
   `.draft/framework/`.
2. Business taxonomy defined well enough for catalog navigation.
3. First company vocabulary lists declared in advisory mode, or deliberately
   queued for later.
4. Initial active Requirement Groups selected.
5. Capability owners identified for the first mapped capabilities.
6. Acceptable-use Technology Components seeded for the most common standards.
7. Baseline deployable objects started for common Host, Runtime Service,
   Data-at-Rest Service, and Edge/Gateway patterns.
8. One real product, system, diagram, repository, or source document selected
   for the first guided Drafting Session.

Setup mode should stop once the team can draft and validate one real system. It
should not wait until every platform, capability, or compliance interpretation
is complete.

## Conversation Cadence

Every setup or drafting session should feel like a guided conversation:

- Start with the intended outcome.
- Explain what the Draftsman already knows from the repo.
- Ask only for the missing fact needed for the current step.
- Prefer multiple-choice questions when the catalog has approved options.
- Keep a short visible backlog of remaining setup work.
- Mark uncertain answers as assumptions or Drafting Session questions.
- Summarize what changed, what validation says, and what the next useful action is.

Audience matters. Architects can answer governance, lifecycle, and pattern
questions. Engineers can answer runtime, dependency, port, platform, and
operational questions. Product teams can answer product ownership, system
boundaries, customer-facing capability, and release-context questions.

## Recommended Setup Sequence

### 1. Workspace Readiness

Confirm the company repo, framework copy, provider, and validation command.

Question:

> Which private company DRAFT repo should we use for architecture content?

### 2. Business Navigation

Define enough business taxonomy for people to browse the catalog.

Question:

> What are the first 3-7 business pillars or product groupings people should
> use to find architecture?

### 3. Company Vocabulary

Declare the first controlled lists the Draftsman should use for
multiple-choice questions. Start in advisory mode.

Question:

> Which lists do we already know well enough to offer as choices: deployment
> targets, data classifications, team identifiers, availability tiers, or
> failure domains?

### 4. Governance Baseline

Choose the first active Requirement Groups. Start narrow if the company is
migrating an existing inventory.

Question:

> Which governance baseline should new objects address first: DRAFT-only,
> SOC 2, TX-RAMP, NIST CSF, or a company-specific group?

### 5. Acceptable-Use Technology

Seed the standards people will select from during interviews.

Question:

> Which enterprise standards should we seed first for identity, logging,
> monitoring, patching, backup, compute, operating systems, database, and edge?

### 6. Baseline Deployable Standards

Create enough reusable deployable objects that product drafting can choose
standards instead of inventing everything.

Question:

> Which common deployable standard should we draft first: Host, Runtime
> Service, Data-at-Rest Service, or Edge/Gateway Service?

### 7. First Real Drafting Session

Start with one real product or system and capture gaps as work in progress.

Question:

> Which product, system, diagram, repository, or source document should we use
> for the first guided Drafting Session?

## Good Setup Output

A good setup-mode response looks like this:

```text
Setup mode is active.

Current state:
- Workspace: /path/to/company-draft
- Framework copy: present
- Business taxonomy: 4 pillars
- Company vocabulary: teams and deployment targets advisory
- Active Requirement Groups: 1 active group
- Capability ownership: 5 of 8 mapped capabilities have owners
- Company catalog baseline: 12 Technology Components, 3 deployable standards

Next: pick one real product, diagram, repository, or source document and start
the first focused Drafting Session.

Left after that: finish acceptable-use mappings, draft missing baseline
standards, validate, and review the generated browser.

Can revisit later: taxonomy names, active governance groups, lifecycle choices,
availability tiers, failure domains, and incomplete object details.

Question: Which real product or system should we draft first?
```
