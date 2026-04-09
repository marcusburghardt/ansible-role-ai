## Why

Commands deployed by this Ansible role end abruptly after their primary action, leaving the user to figure out the next logical step. For example, after checking out a PR there is no suggestion to run local tests or review it; after a PR review there is no prompt to post comments or checkout the branch for deeper inspection. Additionally, there is no general-purpose mechanism for OpenCode to analyze the current repository state (uncommitted changes, commit history, active spec-driven changes) and suggest the most logical next action -- such as committing after implementation, squashing similar commits for a cleaner history, or archiving a completed change.

## What Changes

- Add context-aware "Next Steps" suggestions to the end of existing commands (`review_pr.md`, `checkout_pr.md`, `refresh_spec_frameworks.md`) so each command concludes with actionable guidance tailored to what just happened
- Create a new `workflow_next.md` command that analyzes the current repository and workflow state to suggest the most logical next action: commit uncommitted changes, squash related commits, push unpushed branches, archive completed changes, or continue in-progress work
- `security_remediation.md` already has a `### Next Steps` section and requires no changes

## Capabilities

### New Capabilities
- `workflow-next-step`: A new command that inspects git state, branch context, commit history, and spec-driven framework status to suggest the single most logical next action with a concrete command the user can run

### Modified Capabilities

## Impact

- **Files modified**: `files/commands/review_pr.md` (add Next Steps section), `files/commands/checkout_pr.md` (add Next Steps section), `files/commands/refresh_spec_frameworks.md` (add Next Steps section)
- **Files added**: `files/commands/workflow_next.md` (new command, auto-discovered by existing deployment mechanism)
- **No task/defaults changes needed**: All changes are to command files in `files/commands/`, which are auto-discovered and deployed
- **Existing commands unaffected functionally**: The additions are purely additive -- appended sections after the existing final step
