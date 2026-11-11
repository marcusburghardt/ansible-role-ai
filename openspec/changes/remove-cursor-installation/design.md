# Design

## Context

See `proposal.md` for motivation. Current state that shapes the approach:

- `install_cursor` is one of ten `ai_tasks` entries and is disabled by default.
- `tasks/main.yml` resolves every enabled task by name from `tasks/<name>.yml`,
  so an `ai_tasks` entry without a matching file fails at include time.
- The `cursor-installation` capability spec currently lives at
  `openspec/specs/cursor-installation/spec.md`, but it begins with
  `## ADDED Requirements` and has no `## Requirements` section. OpenSpec parses
  no requirements from it (`openspec list --specs` reports 0), and archive will
  refuse to apply a delta to it until the structure is normalized.
- `openspec/specs/tool-installation/spec.md` cites `vars/install_cursor.yml` as
  the per-task variable-file exemplar.
- No test in `tests/` references `install_cursor`.

## Goals / Non-Goals

**Goals:**

- Remove every Cursor artifact from this role: task, vars, template, defaults,
  README documentation, and capability spec.
- Leave the role with a coherent scope: spec-driven frameworks, OpenCode harness
  and configuration, commands, skills, and the local model runtime.
- Hand off the implementation and its behavioral spec to a dedicated
  `ansible-role-cursor` repository.
- Keep the consumer migration path explicit and minimal.

**Non-Goals:**

- Creating or scaffolding the `ansible-role-cursor` repository in this change.
  It is a separate repository with its own release cycle.
- Refactoring or renaming the remaining role (for example, `ansible-role-ai`
  to a narrower name) or changing the `ai_` variable prefix.
- Repairing the other archived specs that are structurally invalid for OpenSpec
  (for example `role-structure`, `grafana-metrics`). That is separate repo
  hygiene, except for `cursor-installation`, which this change must touch.
- Changing Ollama, OpenCode, SpecKit, OpenSpec, or Grafana behavior.

## Decisions

### Decision 1: Hard removal at the next minor release
Delete the task instead of keeping a deprecation shim.

- **Why**: The task ships disabled, so default consumers see no behavior change.
  A shim would keep the code and the API surface in a role that explicitly no
  longer owns it, and it would still end in a breaking release later.
- **Alternatives considered**: (a) one-release deprecation with a failing task
  and pointer message -- rejected as extra release cycles for a disabled
  feature; (b) keep the entry and delegate with `include_role` -- rejected
  because it re-couples the roles across repositories.
- **Versioning**: `BREAKING CHANGE` footer; release-please bumps `0.5.x` to
  `0.6.0` while the project is below `1.0.0`.

### Decision 2: The new role is `ansible-role-cursor`, not a generic IDE role
The repository is Cursor-specific, matching the existing VSCode-specific role.

- **Why**: Each editor has its own download API, packaging quirks, and update
  cadence. A shared "ide" role would recreate the scope problem this change
  removes, and the existing VSCode role already establishes the pattern.
- **Consequence**: Variable names use a `cursor_` prefix
  (`cursor_version`, `cursor_install_method`, `cursor_appimage_dir`) so the two
  roles cannot collide in a shared playbook.

### Decision 3: Composition happens in the consumer playbook, not via meta dependencies
This role does not declare `ansible-role-cursor` as a dependency.

- **Why**: A meta dependency would install Cursor implicitly for everyone,
  defeating the opt-in nature. Consumers who want both compose them explicitly
  or use an umbrella playbook.
- **Alternatives considered**: galaxy dependency in `meta/main.yml` -- rejected
  for the same reason the task was opt-in in the first place.

### Decision 4: The Cursor spec is ported, not rewritten
The 14 requirements and their scenarios move to the new repository as its
baseline capability spec, adapted to the `cursor_` variable names.

- **Why**: The scenarios encode hard-won behavior -- redirect-based version
  resolution, per-format idempotency, AppImage marker semantics, desktop entry
  rules. Regenerating them would lose detail.
- **Consequence**: In this repository, the capability is deleted via a
  `## REMOVED Requirements` delta with per-requirement reason and migration.

### Decision 5: Normalize the existing cursor spec before archiving
The change includes converting `openspec/specs/cursor-installation/spec.md`
from a delta-shaped file (`## ADDED Requirements`) into a main spec
(`## Purpose` plus `## Requirements`).

- **Why**: Archive refuses to apply a delta to a structurally invalid main spec,
  and the removal delta cannot match requirements the parser cannot see. The
  first task must restore parseability, which also makes the subsequent removal
  verifiable (`openspec show cursor-installation --type spec` should list 14
  requirements before archive).

## Risks / Trade-offs

- **Consumers with a full `ai_tasks` override break** → Document the removal in
  README under a short migration note and in the changelog via the
  `BREAKING CHANGE` footer. The failure message is an Ansible "file not found"
  for `tasks/install_cursor.yml`, which is clear enough to act on.
- **Behavioral regression when porting** → Port the spec verbatim and add a
  syntax-check plus an AppImage-path integration test in the new repository
  before its first release.
- **Duplicated scaffolding across three AI/IDE roles** → Accepted. Each repo
  stays small; a shared template can be extracted later if a fourth editor role
  appears.
- **The Grafana dashboard still mentions Cursor as an example agent name** →
  Leave it. It is illustrative text in a description, not a dependency, and
  changing it would add unrelated churn to this change.
- **Other archived specs remain structurally invalid** → Out of scope; note it
  for a separate hygiene change.

## Migration Plan

1. Release `0.6.0` with Cursor removed.
2. Consumers who enabled the task: install `ansible-role-cursor`, rename
   `ai_cursor_*` variables to `cursor_*`, and add the role (or its
   `install_cursor` task list entry) to their playbook.
3. Rollback: pin the previous role version (`0.5.x`) until the migration is
   complete. No state is destroyed by the upgrade itself; the role never
   uninstalls Cursor.
