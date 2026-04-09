## Why

AI-assisted contributions currently lack consistent coding principles across repositories that don't provide their own governance files (e.g., `constitution.md`, `AGENTS.md`). The existing `commit.md` global instruction covers commit standards but not broader coding principles like readability, simplicity, composability, or dependency management. The repository's `constitution.md` contains mature, battle-tested principles (Core Principles I-VII, language-specific coding standards) that originated in the ComplyTime organization but are universally applicable. Deploying an organization-agnostic version of these principles as a global OpenCode instruction file ensures all AI-assisted contributions are consistent regardless of the project, while respecting project-level overrides when they exist.

## What Changes

- Deploy a new `coding-standards.md` file to `~/.config/opencode/` containing organization-agnostic core coding principles extracted from the existing `constitution.md`
- Add `~/.config/opencode/coding-standards.md` to the `ai_opencode_instructions` default list so it is always loaded into OpenCode sessions
- Follow the same precedence pattern as `commit.md`: the file explicitly states that project-level rules take precedence over these baseline defaults

## Capabilities

### New Capabilities
- `global-constitution-deployment`: Deploy an organization-agnostic coding standards file as a global OpenCode instruction file, covering core principles (single source of truth, simplicity, incremental improvement, readability, composability, convention over configuration), contribution workflow standards, and language-specific coding guidelines

### Modified Capabilities
- `opencode-configuration`: Update the default `ai_opencode_instructions` list to include `~/.config/opencode/coding-standards.md` alongside the existing `commit.md`

## Impact

- **Files added**: `files/coding-standards.md` (static coding standards file), `defaults/` variable additions
- **Files modified**: `defaults/main.yml` (update `ai_opencode_instructions` default), `tasks/configure_opencode.yml` (add deployment task for constitution file)
- **Configuration**: The deployed `opencode.json` will include `~/.config/opencode/coding-standards.md` in its `instructions` array, positioned after `commit.md` but before repository-relative paths so project-level files override via last-wins semantics
- **Existing users**: Users who override `ai_opencode_instructions` are unaffected. Users on defaults will get the new coding standards file automatically on next role run
- **No breaking changes**: The coding standards file uses the same precedence-deferral pattern as `commit.md`, so existing project-level governance is respected
