## Context

The `configure_opencode` task currently deploys commands via a hard-coded `loop:` list in `tasks/configure_opencode.yml`. This list must be manually synchronized whenever a command file is added, removed, or renamed in `files/commands/`. The list currently has a bug (`refresh.md` vs. `refresh_spec_frameworks.md`). Skills directories are created but no deployment mechanism exists. Users who want to add their own commands or skills must manually place files on the target -- there is no Ansible-managed path for custom sources.

The role is intended for local-only use (controller and target are the same machine), which simplifies source path resolution.

## Goals / Non-Goals

**Goals:**
- Eliminate manual synchronization between `files/commands/` contents and task YAML
- Let users disable specific built-in commands/skills without forking the role
- Let users deploy custom commands/skills from local paths alongside built-ins
- Prepare the skills deployment pipeline for when built-in skills are added
- Provide an opt-in cleanup mechanism for removing unwanted commands/skills
- Fix the `refresh.md` filename mismatch bug

**Non-Goals:**
- Deploying any built-in skills in this change (infrastructure only)
- Remote source support (fetching commands/skills from URLs or remote hosts)
- Template-based commands (custom commands are copied as-is, no Jinja2 processing)
- Automatic cleanup of orphaned files (cleanup is explicit and opt-in)

## Decisions

### Decision 1: Auto-discovery via `ansible.builtin.find` + blocklist filtering

**Choice:** Use `ansible.builtin.find` to discover `files/commands/*.md` and `files/skills/*/` at runtime, then filter results against a blocklist variable.

**Alternatives considered:**
- *Allowlist variable* (user explicitly lists what to deploy): More control, but recreates the synchronization problem -- the default allowlist would need to match `files/commands/` contents.
- *Glob in `loop:`* (e.g., `loop: "{{ lookup('fileglob', 'commands/*.md') }}"`): Ansible `fileglob` lookup works, but returns full paths and is harder to filter. `ansible.builtin.find` + `register` is more idiomatic for conditional filtering.

**Rationale:** Blocklist + auto-discovery means zero config for the common case (deploy everything), and users only need to act when they want to opt out. Adding a new command to the role is just dropping a `.md` file into `files/commands/`.

### Decision 2: Separate variables for built-in control vs. custom sources

**Choice:** Four variables: `ai_opencode_commands_disabled`, `ai_opencode_commands_custom`, `ai_opencode_skills_disabled`, `ai_opencode_skills_custom`.

**Alternatives considered:**
- *Unified variable* (single list mixing built-in overrides and custom entries): Tempting for brevity, but conflates two concerns -- disabling built-ins and adding externals have different shapes.

**Rationale:** Separation of concerns. Disabling is a simple list of names. Custom sources need `src` and optional `name`. Mixing them would require sentinel values or type detection, adding complexity for no real gain.

### Decision 3: Custom entries use `src` (required) + `name` (optional)

**Choice:** Each custom entry is a dict with `src:` (path to the file or directory) and an optional `name:` (override for the deployed filename/directory name). If `name` is omitted, the basename of `src` is used.

```yaml
ai_opencode_commands_custom:
  - src: ../shared-commands/deploy_staging.md
  - src: /opt/team/audit_script.md
    name: security_audit.md
```

**Rationale:** `src` paths can be relative (resolved by Ansible relative to the playbook) or absolute. The optional `name` override handles cases where the source filename doesn't match the desired command/skill name. This is a common Ansible pattern and will feel natural to users.

### Decision 4: Skills target directory is configurable via `ai_skills_target`

**Choice:** A string variable `ai_skills_target` with two values: `agent-neutral` (default, deploys to `~/.agents/skills/`) or `opencode` (deploys to `~/.config/opencode/skills/`). A derived variable `ai_opencode_skills_deploy_dir` resolves the actual path in `vars/configure_opencode.yml`.

**Rationale:** `~/.agents/skills/` is the cross-agent convention (works with OpenCode, Claude Code, etc.), so it's the better default. But some users may want OpenCode-specific placement. One variable, two clear options.

### Decision 5: Cleanup is a separate task, disabled by default

**Choice:** New task `cleanup_opencode` in `ai_tasks` (disabled by default) with `ai_opencode_commands_cleanup` and `ai_opencode_skills_cleanup` list variables. Uses `ansible.builtin.file: state=absent`.

**Alternatives considered:**
- *Cleanup inline in `configure_opencode`*: Mixing deployment and removal in one task makes the logic harder to reason about and impossible to disable independently.
- *Automatic orphan detection*: Would require tracking deployed files across runs (state management), which adds complexity far beyond the current need.

**Rationale:** Clean separation of concerns. Deploying and removing are different intents. Disabled by default so it never runs unless the user explicitly opts in and provides a list.

### Decision 6: Two separate task blocks for built-in vs. custom command deployment

**Choice:** Built-in commands use `ansible.builtin.copy` with `src:` relative to the role's `files/` directory. Custom commands use `ansible.builtin.copy` with the user-provided `src:` path. These are two separate tasks in `configure_opencode.yml` because the source resolution semantics differ (role-relative vs. playbook-relative/absolute).

**Rationale:** A single combined task would require constructing the `src` path dynamically with conditionals, which is fragile and hard to debug. Two tasks are explicit and each is straightforward.

## Risks / Trade-offs

- **[Risk] `ansible.builtin.find` on `files/commands/` at role_path level** -- `role_path` is available in tasks and resolves to the role's root directory. If the role is installed via Galaxy into a non-standard location, `role_path` still works correctly. Mitigation: `role_path` is a built-in Ansible magic variable; this is the standard approach.

- **[Risk] Custom `src` paths that don't exist cause failures** -- If a user specifies a `src` path that doesn't exist, `ansible.builtin.copy` will fail with a clear "file not found" error. Mitigation: This is expected Ansible behavior and the error message is descriptive. No special handling needed.

- **[Risk] Name collisions between built-in and custom commands** -- If a custom command has the same filename as a built-in (and the built-in is not disabled), the custom will overwrite the built-in since custom deployment runs after built-in deployment. Mitigation: This is arguably the correct behavior (user intent wins), but it should be documented.

- **[Trade-off] No Jinja2 processing for custom commands/skills** -- Custom files are copied as-is via `ansible.builtin.copy`, not processed as templates. This keeps things simple but means custom commands can't use Ansible variables. Mitigation: If template support is needed later, a `template: true` flag could be added to custom entries in a future change.
