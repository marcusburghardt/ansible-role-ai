---
description: "Refresh per-repo framework artifacts after CLI tool updates"
---

# Refresh Framework Artifacts

Detect which spec-driven development framework is initialized in the current repository and run the appropriate update command to refresh per-repo artifacts (commands, skills, scripts, templates) to match the currently installed CLI version.

## Steps

1. **Detect frameworks** by checking for their directory markers:
   - `openspec/` directory indicates OpenSpec is initialized
   - `.specify/` directory indicates SpecKit is initialized

2. **Run the appropriate update command(s)**:

   **If `openspec/` exists:**
   ```bash
   openspec update
   ```
   This regenerates `.opencode/skills/` and `.opencode/command/opsx-*` files to match the current `@fission-ai/openspec` CLI version.

   **If `.specify/` exists:**
   ```bash
   specify init --here --ai opencode --force
   ```
   This regenerates `.opencode/command/speckit.*` files and `.specify/scripts/` and `.specify/templates/` to match the current `specify-cli` version.

   **If both exist**, run both commands.

3. **If neither directory exists**, report:
   > No spec-driven development framework is initialized in this repository.
   > Run `openspec init` or `specify init` to set one up.

4. **Show a summary** of what was refreshed and the CLI version used.

### Next Steps

After refreshing framework artifacts, suggest the most relevant next actions:

- "Run `git diff` to review what changed in the refreshed artifacts."
- "If changes are meaningful, commit them: `git add .opencode/ && git commit -s -m 'chore: refresh framework artifacts to latest CLI version'`"
- "If no changes were made, the artifacts were already up to date."
- "Run `/workflow_next` to see what else needs attention."
