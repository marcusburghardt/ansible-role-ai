## ADDED Requirements

### Requirement: workflow_next command follows established command format
The command SHALL be deployed as `files/commands/workflow_next.md` with YAML frontmatter containing a `description` field, an H1 title, an Arguments section, step-by-step Execution Steps, and auto-discovered by the existing command deployment mechanism.

#### Scenario: Command is auto-discovered and deployed
- **WHEN** the Ansible role runs with `configure_opencode` enabled
- **THEN** `workflow_next.md` SHALL be auto-discovered from `files/commands/` and deployed to `{{ ai_opencode_command_dir }}`

#### Scenario: Command can be disabled
- **WHEN** `ai_opencode_commands_disabled` contains `workflow_next`
- **THEN** `workflow_next.md` SHALL NOT be deployed

### Requirement: Detect uncommitted changes as highest priority
The command SHALL check `git status --porcelain` for uncommitted changes (staged or unstaged). If uncommitted changes exist, the command SHALL suggest committing as the next action, showing the number of changed files and a draft commit command.

#### Scenario: Uncommitted changes exist
- **WHEN** the working tree has 3 modified files and 1 new untracked file
- **THEN** the command SHALL suggest: "You have 4 uncommitted changes. Consider committing:" followed by a concrete `git add` and `git commit` example

#### Scenario: No uncommitted changes
- **WHEN** the working tree is clean
- **THEN** the command SHALL proceed to check for unpushed commits

### Requirement: Detect unpushed commits
The command SHALL check whether the current branch has commits ahead of its remote tracking branch. If unpushed commits exist, the command SHALL suggest pushing.

#### Scenario: Branch is ahead of remote
- **WHEN** the current branch has 2 commits ahead of `origin/main`
- **THEN** the command SHALL suggest: "You have 2 unpushed commits. Push with:" followed by the concrete `git push` command

#### Scenario: No remote tracking branch
- **WHEN** the current branch has no remote tracking branch configured
- **THEN** the command SHALL suggest setting up tracking with `git push -u origin <branch>`

#### Scenario: Branch is up to date with remote
- **WHEN** the current branch is even with its remote tracking branch
- **THEN** the command SHALL proceed to check for squash opportunities

### Requirement: Detect squash opportunities in commit history
The command SHALL analyze commits on the current branch that are ahead of the default branch. If 3 or more commits share the same Conventional Commits type (and optional scope), the command SHALL suggest squashing them into a single commit with a proposed combined message.

#### Scenario: Multiple similar commits detected
- **WHEN** the current branch has 4 commits ahead of `main`, and 3 of them start with `fix:` (e.g., `fix: update lodash`, `fix: update axios`, `fix: update express`)
- **THEN** the command SHALL suggest: "3 commits with prefix `fix:` could be squashed into one. Suggested: `fix: update security dependencies`" followed by the interactive rebase command

#### Scenario: No squash opportunities
- **WHEN** all commits on the current branch have different types/scopes
- **THEN** the command SHALL proceed to check for active spec-driven changes

#### Scenario: On default branch with no ahead commits
- **WHEN** the user is on the default branch with no commits ahead
- **THEN** the command SHALL skip squash analysis and proceed to check for active spec-driven changes

### Requirement: Detect active spec-driven changes with pending tasks
The command SHALL check for OpenSpec (`openspec/` directory) and SpecKit (`.specify/` directory) frameworks. If an active change exists with pending tasks, the command SHALL suggest continuing implementation.

#### Scenario: OpenSpec change with pending tasks
- **WHEN** `openspec/` exists and `openspec list --json` shows an active change with incomplete tasks
- **THEN** the command SHALL suggest: "Active change '<name>' has N remaining tasks. Continue with `/opsx-apply`"

#### Scenario: SpecKit change in progress
- **WHEN** `.specify/` exists and there are pending spec-driven tasks
- **THEN** the command SHALL suggest continuing the SpecKit workflow

#### Scenario: No spec-driven framework detected
- **WHEN** neither `openspec/` nor `.specify/` directories exist
- **THEN** the command SHALL skip this check

### Requirement: Detect completed changes ready for archive
The command SHALL check if any active OpenSpec changes have all tasks marked complete. If so, the command SHALL suggest archiving.

#### Scenario: Completed OpenSpec change
- **WHEN** an OpenSpec change has all tasks marked `[x]`
- **THEN** the command SHALL suggest: "Change '<name>' is complete. Archive with `/opsx-archive <name>`"

#### Scenario: No completed changes
- **WHEN** no active changes are fully complete
- **THEN** the command SHALL proceed to the clean-state fallback

### Requirement: Clean state fallback
If no actionable suggestion is found at any priority level, the command SHALL report that the repository is in a clean state and suggest exploring new work.

#### Scenario: Nothing to do
- **WHEN** working tree is clean, branch is up to date, no squash opportunities, no active changes
- **THEN** the command SHALL report: "Repository is in a clean state. No pending actions detected." and suggest exploring new work or starting a new change

### Requirement: Single focused suggestion output
The command SHALL display only the single highest-priority suggestion, not a list of all possible actions. The output SHALL include: a brief description of what was detected, the suggested action, and the concrete command to run.

#### Scenario: Multiple conditions are true simultaneously
- **WHEN** the working tree has uncommitted changes AND unpushed commits exist AND a squash opportunity exists
- **THEN** the command SHALL suggest ONLY committing (the highest priority action), not all three

### Requirement: review_pr command includes Next Steps section
The `review_pr.md` command SHALL include a `### Next Steps` section after its final step (Step 9). The suggestions SHALL be conditional on the review outcome.

#### Scenario: Review completed with findings
- **WHEN** the review produced HIGH or CRITICAL findings
- **THEN** the Next Steps SHALL suggest checking out the PR locally with `/checkout_pr <N>` to test, and posting in-line comments if not already done

#### Scenario: Review completed without findings
- **WHEN** the review found no issues
- **THEN** the Next Steps SHALL suggest approving the PR via `gh pr review <N> --approve`

### Requirement: checkout_pr command includes Next Steps section
The `checkout_pr.md` command SHALL include a `### Next Steps` section after its final step. The suggestions SHALL guide the user toward review, testing, or returning to the main branch.

#### Scenario: PR checked out successfully
- **WHEN** a PR branch has been checked out
- **THEN** the Next Steps SHALL suggest running `/review_pr <N>` for a full review, running local tests (if a Makefile or test config is detected), and switching back to the main branch when done

### Requirement: refresh_spec_frameworks command includes Next Steps section
The `refresh_spec_frameworks.md` command SHALL include a `### Next Steps` section after its final step. The suggestions SHALL guide the user toward reviewing and committing the updated artifacts.

#### Scenario: Framework artifacts were refreshed
- **WHEN** OpenSpec or SpecKit artifacts were updated
- **THEN** the Next Steps SHALL suggest running `git diff` to review changes and committing updated artifacts if the changes are meaningful
