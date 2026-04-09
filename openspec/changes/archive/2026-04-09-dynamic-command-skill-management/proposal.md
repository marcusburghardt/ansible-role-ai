## Why

The `configure_opencode` task hard-codes command filenames in a loop, requiring a manual edit to the task YAML every time a command is added, removed, or renamed. There is also a live bug: the loop references `refresh.md` but the actual file is `refresh_spec_frameworks.md`. Skills directories are created but have no deployment mechanism at all. For wider adoption, users need a frictionless way to disable built-in commands/skills they don't want and to bring their own from external paths -- without touching role internals.

## What Changes

- **Auto-discover built-in commands**: Replace the hard-coded loop with `ansible.builtin.find` against `files/commands/*.md`. Any `.md` file added to or removed from `files/commands/` is automatically picked up -- no task edits required.
- **Auto-discover built-in skills**: Add the same auto-discovery for `files/skills/*/` directories, ready for when built-in skills are shipped.
- **Blocklist variables**: Introduce `ai_opencode_commands_disabled` and `ai_opencode_skills_disabled` lists so users can opt out of specific built-ins by name.
- **Custom command/skill variables**: Introduce `ai_opencode_commands_custom` and `ai_opencode_skills_custom` lists so users can deploy commands and skills from external local paths (relative to playbook or absolute). Each entry supports an optional `name` override for the deployed filename/directory.
- **Configurable skills target directory**: Introduce `ai_skills_target` (`agent-neutral` by default, deploying to `~/.agents/skills/`; or `opencode` for `~/.config/opencode/skills/`).
- **Fix filename mismatch bug**: Remove the stale `refresh.md` reference; auto-discovery resolves it naturally by using the actual filename `refresh_spec_frameworks.md`.
- **Add optional cleanup task**: Introduce a new `cleanup_opencode` task (disabled by default in `ai_tasks`) with `ai_opencode_commands_cleanup` and `ai_opencode_skills_cleanup` variables to explicitly remove named commands or skills from the target.

## Capabilities

### New Capabilities
- `command-autodiscovery`: Auto-discover and deploy built-in commands from `files/commands/` with blocklist filtering and custom command injection from external sources
- `skill-autodiscovery`: Auto-discover and deploy built-in skills from `files/skills/` with blocklist filtering, custom skill injection from external sources, and configurable target directory
- `opencode-cleanup`: Optional task to remove specific named commands and skills from the target host

### Modified Capabilities
- `opencode-configuration`: The command deployment mechanism changes from a hard-coded loop to auto-discovery with blocklist and custom sources. Skills gain a deployment mechanism. New default variables are added.

## Impact

- **`defaults/main.yml`**: New variables added (`ai_opencode_commands_disabled`, `ai_opencode_commands_custom`, `ai_opencode_skills_disabled`, `ai_opencode_skills_custom`, `ai_skills_target`, `ai_opencode_commands_cleanup`, `ai_opencode_skills_cleanup`). New task entry for `cleanup_opencode` (disabled by default).
- **`tasks/configure_opencode.yml`**: Command deployment rewritten from hard-coded loop to auto-discover + filter + custom merge. Skill deployment tasks added.
- **`tasks/cleanup_opencode.yml`**: New task file for opt-in cleanup.
- **`vars/configure_opencode.yml`**: New derived variable for resolved skills deploy directory.
- **`vars/cleanup_opencode.yml`**: New vars file for cleanup task.
- **Backwards compatibility**: Fully backward-compatible. Zero-config users get identical behavior (all built-ins deployed, no customs, no cleanup). The `refresh.md` filename bug is fixed as a side effect.
