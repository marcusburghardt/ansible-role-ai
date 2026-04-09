## Context

The Ansible role deploys four commands to `~/.config/opencode/command/`. Three of them (`review_pr.md`, `checkout_pr.md`, `refresh_spec_frameworks.md`) end after their primary action with no guidance on what to do next. Only `security_remediation.md` includes a `### Next Steps` section. Users are left to recall the available commands and figure out logical workflow continuations on their own.

Separately, there is no general-purpose mechanism for the AI agent to look at the overall repository state and proactively suggest actions. Common situations like "you have uncommitted changes after an implementation session" or "your last 4 commits could be squashed into one clean commit" require the user to notice and act on their own.

## Goals / Non-Goals

**Goals:**
- Add context-aware `### Next Steps` sections to the three commands that lack them
- Create a new `workflow_next.md` command that analyzes repository state and suggests the single most logical next action
- Keep suggestions concise and actionable -- each suggestion should include the concrete command to run
- Respect the role's existing patterns (static command files, auto-discovery deployment, same guardrails conventions)

**Non-Goals:**
- Automatically executing suggested next steps (all suggestions are informational only)
- Modifying `security_remediation.md` (it already has adequate next-step guidance)
- Creating a persistent workflow engine or state machine -- this is stateless analysis per invocation
- Suggesting steps outside the user's immediate context (e.g., cross-repo actions)

## Decisions

### 1. Next Steps per command: context-specific, not generic

Each command gets tailored next-step suggestions based on what that command just did, not a generic list. The suggestions are conditional on the command's outcome.

| Command | Context | Example Suggestions |
|---------|---------|-------------------|
| `review_pr` | Just completed a review | "Run `/checkout_pr <N>` to test locally", "Post in-line comments if findings were HIGH+" |
| `checkout_pr` | Just checked out a PR branch | "Run `/review_pr <N>` for a full review", "Run local tests: `make test`", "Switch back: `git checkout main`" |
| `refresh` | Just refreshed framework artifacts | "Run `git diff` to see what changed", "Commit updated artifacts if changes are meaningful" |

**Rationale**: Generic suggestions ("maybe commit?") are noise. Context-specific suggestions based on what just happened are actionable.

**Alternatives considered**: A single shared "next steps" template appended to all commands. Rejected because different commands have different logical continuations.

### 2. `workflow_next.md`: priority-ordered state analysis

The new command inspects multiple signals in priority order and suggests the single highest-priority action:

```
Priority 1: Uncommitted changes exist → suggest commit
Priority 2: Unpushed commits exist → suggest push
Priority 3: Multiple similar recent commits on the current branch → suggest squash
Priority 4: Active OpenSpec/SpecKit change with pending tasks → suggest continue implementation
Priority 5: Completed change not yet archived → suggest archive
Priority 6: Clean state → report "nothing to do" or suggest exploring new work
```

**Rationale**: A single focused suggestion is more useful than a list of everything the user could do. Priority ordering ensures the most urgent action surfaces first.

**Alternatives considered**: Show all possible actions as a menu. Rejected because it recreates the problem of the user having to decide. The command should be opinionated about what matters most right now.

### 3. Squash detection heuristic

The squash suggestion triggers when:
- 3+ commits on the current branch (ahead of default branch) share the same Conventional Commits type and scope
- Example: `fix: update lodash`, `fix: update axios`, `fix: update express` → suggest squashing into `fix: update security dependencies`

The heuristic uses `git log --oneline <default-branch>..HEAD` and groups by commit message prefix (type + optional scope).

**Rationale**: Squashing is most valuable when there are multiple mechanically similar commits (e.g., from iterative fixes or batch security remediations). The heuristic avoids suggesting squash for diverse, intentionally separate commits.

### 4. Framework detection reuse

The command reuses the same framework detection pattern from `refresh_spec_frameworks.md`: check for `openspec/` and `.specify/` directories. If a framework is detected, check for active changes and their status.

**Rationale**: Consistency with established patterns. No new detection logic needed.

## Risks / Trade-offs

- **[Suggestion staleness]** Suggestions are point-in-time snapshots. If the user takes an action between invoking the command and acting on the suggestion, the suggestion may be stale. → Mitigation: Suggestions are cheap to regenerate -- the user can just run the command again.
- **[Squash heuristic false positives]** The heuristic might suggest squashing commits that the user intentionally kept separate. → Mitigation: The suggestion is advisory only and includes context ("3 commits with prefix `fix:` could be squashed"). The user decides.
- **[Command file size]** The `workflow_next.md` command needs to cover multiple analysis paths. → Mitigation: Keep the analysis steps focused and use clear priority ordering to limit the output to one suggestion.
