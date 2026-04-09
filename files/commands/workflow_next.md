---
description: "Analyze repository state and suggest the most logical next action"
---

# Workflow Next

Analyze the current repository and workflow state to suggest the single most logical next action. This command inspects git status, commit history, branch state, and spec-driven framework status, then presents one focused, actionable suggestion.

## Arguments

- No required arguments. The command operates on the current repository.

## Execution Steps

Run through the following priority checks in order. **Stop at the first match** and display that suggestion. Do NOT display multiple suggestions.

### Priority 1: Uncommitted Changes

Check for uncommitted changes in the working tree:

```bash
git status --porcelain
```

**If output is non-empty** (uncommitted changes exist):

1. Count the changed files:
   ```bash
   git status --porcelain | wc -l
   ```
2. Categorize the changes:
   - `M` = modified files
   - `A` or `??` = new/untracked files
   - `D` = deleted files

3. Display the suggestion:
   ```
   ## Next Step: Commit Your Changes

   You have <N> uncommitted changes (<M modified, A new, D deleted>).

   Review the changes:
     git diff
     git status

   Stage and commit:
     git add -A
     git commit -s -m "<type>: <description>"

   Tip: Use `git add -p` for selective staging if changes span multiple concerns.
   ```

4. If spec-driven framework changes are detected (files in `openspec/` or `.specify/` or `.opencode/`), add:
   ```
   Note: Some changes are in spec-driven framework directories.
   If these are from a completed implementation, consider a descriptive commit message
   referencing the change name.
   ```

**Stop here.** Do not check lower priorities.

### Priority 2: Unpushed Commits

Check if the current branch has commits ahead of its remote:

```bash
git status -sb
```

Parse the output for `ahead N` in the branch tracking line.

**If the branch is ahead**:

1. Count unpushed commits:
   ```bash
   git rev-list --count @{upstream}..HEAD 2>/dev/null
   ```

2. Display the suggestion:
   ```
   ## Next Step: Push Your Commits

   Branch `<branch>` has <N> unpushed commit(s).

   Push to remote:
     git push

   Or, if this is a new branch without tracking:
     git push -u origin <branch>
   ```

**If no upstream is configured** (new branch):

   ```
   ## Next Step: Push Your New Branch

   Branch `<branch>` has no remote tracking branch.

   Set up tracking and push:
     git push -u origin <branch>
   ```

**Stop here.**

### Priority 3: Squash Opportunities

Check if the current branch has multiple similar commits ahead of the default branch:

1. Get the default branch:
   ```bash
   DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "main")
   ```

2. Get commits ahead of the default branch:
   ```bash
   git log --oneline "$DEFAULT_BRANCH"..HEAD 2>/dev/null
   ```

3. If there are fewer than 3 commits ahead, skip this check.

4. Group commits by their Conventional Commits type prefix (the text before the first `:`):
   - Extract the prefix from each commit message: `feat`, `fix`, `chore`, `docs`, `refactor`, etc.
   - Count commits per prefix

5. **If any prefix has 3 or more commits**:

   ```
   ## Next Step: Consider Squashing Commits

   <N> commits on branch `<branch>` share the prefix `<type>:`:
     - <commit 1>
     - <commit 2>
     - <commit 3>
     ...

   These could be squashed into a single commit for a cleaner history.

   Suggested combined message:
     <type>: <combined description based on the individual messages>

   To squash interactively:
     git rebase -i <DEFAULT_BRANCH>

   Note: Only squash if these commits are truly related. Separate concerns
   should remain in separate commits.
   ```

**Stop here.**

### Priority 4: Active Spec-Driven Changes with Pending Tasks

Check for active changes in spec-driven frameworks:

1. **If `openspec/` directory exists**:
   ```bash
   openspec list --json 2>/dev/null
   ```
   Parse the output for active changes. For each active change, check if it has pending (unchecked) tasks by reading its `tasks.md`.

2. **If `.specify/` directory exists**:
   Check for active specs with pending tasks.

3. **If an active change with pending tasks is found**:

   ```
   ## Next Step: Continue Implementation

   Active change: `<change-name>` (<N> of <M> tasks complete)

   Continue working on it:
     /opsx-apply <change-name>

   Or check its status:
     openspec status --change "<change-name>"
   ```

   If multiple active changes exist, show the one with the most progress (closest to completion).

**Stop here.**

### Priority 5: Completed Changes Ready for Archive

Check for active OpenSpec changes where all tasks are complete:

1. For each active change found in Priority 4's listing, check if all tasks are marked `[x]`.

2. **If a fully completed change is found**:

   ```
   ## Next Step: Archive Completed Change

   Change `<change-name>` has all tasks complete but hasn't been archived.

   Archive it:
     /opsx-archive <change-name>

   This moves the change to openspec/changes/archive/ and syncs delta specs
   to the main spec baseline.
   ```

**Stop here.**

### Priority 6: Clean State

If none of the above checks matched:

```
## All Clear

Repository is in a clean state. No pending actions detected.

- Working tree is clean
- All commits are pushed
- No active changes in progress

Suggestions:
- Start a new change: `/opsx-propose`
- Review a PR: `/review_pr <number>`
- Check for security issues: `/security_remediation`
- Explore an idea: `/opsx-explore`
```

## Output Format

The command SHALL display only **one suggestion** -- the highest-priority match from the checks above. The output follows this structure:

```
## Next Step: <Action Title>

<Brief description of what was detected>

<Concrete command(s) to run>

<Optional tip or context>
```

Do NOT display a list of all possible actions. Do NOT show checks that passed without findings. The value of this command is its opinionated, focused recommendation.
