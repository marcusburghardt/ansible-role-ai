## 1. Add Next Steps to Existing Commands

- [x] 1.1 Add a `### Next Steps` section to the end of `files/commands/review_pr.md` (after Step 9) with context-aware suggestions: checkout the PR for local testing (`/checkout_pr <N>`), approve if no findings (`gh pr review <N> --approve`), and post comments if HIGH+ findings were found.
- [x] 1.2 Add a `### Next Steps` section to the end of `files/commands/checkout_pr.md` with suggestions: run `/review_pr <N>` for a full review, run local tests if a Makefile or test config is detected, and switch back to main when done.
- [x] 1.3 Add a `### Next Steps` section to the end of `files/commands/refresh_spec_frameworks.md` (after Step 4) with suggestions: run `git diff` to review what changed, and commit updated artifacts if changes are meaningful.

## 2. Create workflow_next Command

- [x] 2.1 Create `files/commands/workflow_next.md` with YAML frontmatter, H1 title, Arguments section, and the priority-ordered analysis pipeline skeleton.
- [x] 2.2 Write Priority 1 (Uncommitted Changes): check `git status --porcelain`, suggest committing with a concrete `git add` and `git commit` example showing the count of changed files.
- [x] 2.3 Write Priority 2 (Unpushed Commits): check if the branch is ahead of its remote tracking branch, suggest pushing or setting up tracking if no remote exists.
- [x] 2.4 Write Priority 3 (Squash Opportunities): analyze commits ahead of the default branch with `git log --oneline`, group by Conventional Commits type prefix, suggest squash if 3+ commits share the same prefix with a proposed combined message and rebase command.
- [x] 2.5 Write Priority 4 (Active Spec-Driven Changes): detect OpenSpec/SpecKit frameworks, check for active changes with pending tasks, suggest continuing implementation with the appropriate command.
- [x] 2.6 Write Priority 5 (Completed Changes Ready for Archive): check if any active OpenSpec changes have all tasks complete, suggest archiving.
- [x] 2.7 Write Priority 6 (Clean State Fallback): report clean state, suggest starting new work.
- [x] 2.8 Write the output format section: single focused suggestion with description, suggested action, and concrete command. Ensure only the highest-priority suggestion is displayed.

## 3. Verification

- [x] 3.1 Verify YAML frontmatter parses correctly on `workflow_next.md`, confirm all priority steps are numbered consistently.
- [x] 3.2 Verify the three modified commands still have valid structure (frontmatter intact, step numbering consistent, `### Next Steps` appears after the last existing step).
- [x] 3.3 Run `ansible-lint` to verify no lint issues are introduced.
