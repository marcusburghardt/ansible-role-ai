## Context

The role already deploys `commit.md` as an always-on instruction and
`pr_workflow.py` as a portable helper. The missing pieces are a PR standard and
a non-weakenable baseline. Git enforcement belongs to the dedicated Git role.

## Decisions

### Use instructions for policy, not a skill

Skills are on-demand and may never be loaded. Commit and PR rules must apply to
every change, so they remain instruction files. No commit or PR skill is added.

### Baseline is a floor

Repository guidance may add stricter rules or explicitly waive a rule. Silence
must not opt out. This keeps the role useful in repositories that only define a
type list, which was the source of the observed drift.

### Keep `commit.md` and `pr.md` separate

Commit messages and PR metadata are reviewed at different stages and change for
different reasons. Separate files keep the instruction list readable and make
targeted repository overrides possible.

### Commit validation moves to the Git role

`pr_workflow.py` remains focused on PR snapshots, journals, reviews, and PR
titles. Commit-message validation and hook installation are Git concerns and
belong to `ansible-role-git`, which deploys `commit_lint.py` and installs
per-repository `commit-msg` hooks without a global `core.hooksPath`.

## Alternatives Considered

- **A skill for commit guidance**: rejected because skills are not guaranteed to
  load before a commit.
- **Global Git hook installation in this role**: rejected because hook
  enforcement is generic Git configuration and interferes with repository hook
  tooling when a global hooks path is used.
