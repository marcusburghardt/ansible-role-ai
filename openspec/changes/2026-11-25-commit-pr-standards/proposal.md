## Why

Commit and PR guidance is currently advisory only. `commit.md` is deployed as a
global instruction, but it defers to any repository guidance and contains no
enforcement. `pr.md` exists in the role but is never deployed, so PR titles have
no configured standard. Agents therefore produce long commit subjects and
non-conventional PR titles even on hosts configured by this role.

This change keeps contribution policy in this role. Git hook enforcement is
owned by `ansible-role-git`, which deploys `commit_lint.py` and manages
per-repository `commit-msg` hooks.

## What Changes

- Rewrite `commit.md` so repository rules may add stricter requirements but do
  not silently waive the baseline.
- Expand the documented Conventional Commits type set.
- Deploy `pr.md` and add it to the default OpenCode instructions list.
- Keep `validate-pr-title` in `pr_workflow.py`; commit validation moves to the
  Git role.
- Align shipped command examples with the standards.
- Document the standards and the Git role handoff.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `opencode-configuration`: Deploy `pr.md`, include it in the default
  instruction list, and treat commit/PR standards as a non-weakenable floor.

## Impact

- **Files added**: `openspec/changes/2026-11-25-commit-pr-standards/`
- **Files modified**: `files/commit.md`, `files/pr.md`,
  `files/scripts/pr_workflow.py`, `files/commands/workflow_next.md`,
  `files/commands/refresh_spec_frameworks.md`,
  `files/commands/security_remediation.md`,
  `files/commands/address_feedback.md`, `defaults/main.yml`,
  `tasks/configure_opencode.yml`, `tests/test.yml`,
  `tests/test_pr_workflow.py`, `README.md`
- **Defaults**: `~/.config/opencode/pr.md` is added to
  `ai_opencode_instructions`.
- **Compatibility**: no variable changes. Consumers who override
  `ai_opencode_instructions` are unaffected and can add `pr.md` themselves.
- **Git enforcement**: provided by `ansible-role-git`; this role does not set
  `core.hooksPath` or install Git hooks.
