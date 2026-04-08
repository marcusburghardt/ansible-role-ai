## Why

The AI tooling used by developers (OpenCode, OpenSPEC, SpecKit) is currently managed through a monolithic, flat Ansible playbook (`ai_opencode.yml`). This approach does not scale as new AI tools are added, lacks the granular control and reusability that roles provide, and is inconsistent with the established role-based architecture used across the other AnsibleRoles repositories (ansible-role-devsecops, ansible-role-git, ansible-role-vim). A dedicated Ansible role is needed to bring AI tool management in line with existing patterns, enable selective tool installation and configuration, and support future agent additions.

## What Changes

- Implement the `ansible-role-ai` role following the established 3-phase dispatcher architecture (OS vars, task vars, task files) used by sibling roles.
- Create a data-driven task list (`ai_tasks`) in `defaults/main.yml` with `enabled` flags, allowing consumers to selectively enable/disable sub-tasks.
- Add sub-task `install_dependencies` (disabled by default) to install system-level prerequisites (nodejs, npm, uv) via OS package manager. This enables fresh-machine scenarios where no tooling is pre-installed, while defaulting to opt-in to avoid touching system packages for users who already have them.
- Add sub-task `install_opencode` to install OpenCode via npm with support for `latest` or pinned versions, ensuring updates on each run when set to `latest`.
- Add sub-task `configure_opencode` to manage the OpenCode configuration file (`opencode.json`), the wrapper script, and user-level commands and skills deployed to the user config directory.
- Add sub-task `install_openspec` to install OpenSPEC via npm with the same version flexibility.
- Add sub-task `install_speckit` to install SpecKit via `uv tool install` with GitHub release resolution for `latest` or pinned version tags.
- Populate `defaults/main.yml` with all user-overridable variables (versions, model names, GCP settings, paths, script name, config content).
- Create OS-family-specific variables (`vars/redhat.yml`) for required system packages.
- Create per-task variable files (`vars/<task_name>.yml`) for internal variables scoped to each sub-task.
- Provide a Jinja2 template for the OpenCode configuration file to allow dynamic variable substitution.
- Provide a Jinja2 template for the wrapper script.
- Include static files for default commands to be deployed to the user config directory: `checkout_pr` (PR checkout workflow), `review_pr` (fallback for repos not yet synced by org-infra), and `refresh` (on-demand refresh of per-repo OpenSpec/SpecKit framework artifacts after CLI updates).
- Update `meta/main.yml` with proper Galaxy metadata (author, description, license, platforms, tags).
- Replace the boilerplate `README.md` with proper documentation following the sibling role pattern: role description, requirements, variables reference, example playbooks, license, and author info.
- Make the OpenCode `instructions` file list variable-driven (`ai_opencode_instructions`) and default to `["constitution.md", "AGENTS.md", "CLAUDE.md"]` so OpenCode picks up org-wide governance, auto-generated agent context, and local overrides.
- Add `ai_trusted_github_orgs` variable and export it via the wrapper script as `TRUSTED_GITHUB_ORGS`. Update `checkout_pr` and `review_pr` commands to verify the current repository belongs to a trusted organization before proceeding, prompting for confirmation on untrusted repos.
- Replace sensitive default values for `ai_gcp_project` and `ai_vertex_location` with safe placeholders suitable for public Galaxy publishing. Document in README that these must be set when using Google Vertex AI as the provider, and that they are harmlessly ignored otherwise.
- Update `tests/test.yml` to be a runnable smoke test that disables install tasks (which require npm/uv/GitHub API) and only exercises the dispatcher and configuration deployment.
- Add `.yamllint` configuration for YAML linting consistency.
- Deploy a `commit.md` instructions file to `~/.config/opencode/` with universal commit standards (Conventional Commits, Signed-off-by, Assisted-by trailers) and add it to `ai_opencode_instructions` via `~/` path so it is always loaded regardless of which repository the user is working in. The file explicitly defers to repository-level guidelines (constitution.md, AGENTS.md, etc.) when they conflict, acting as a baseline that repos can override.

## Capabilities

### New Capabilities
- `tool-installation`: Install and update AI developer tools (OpenCode, OpenSPEC, SpecKit) with support for latest or pinned versions.
- `opencode-configuration`: Configure OpenCode with user-level settings (config file, wrapper script, commands, and skills deployed to the user config directory).
- `role-structure`: Implement the data-driven dispatcher pattern with selectable sub-tasks, OS-specific variables, and per-task variable scoping.

### Modified Capabilities
<!-- No existing specs to modify - this is a greenfield role. -->

## Impact

- **Files created**: `defaults/main.yml`, `vars/redhat.yml`, `vars/install_opencode.yml`, `vars/configure_opencode.yml`, `vars/install_openspec.yml`, `vars/install_speckit.yml`, `tasks/main.yml`, `tasks/install_opencode.yml`, `tasks/configure_opencode.yml`, `tasks/install_openspec.yml`, `tasks/install_speckit.yml`, `templates/opencode.json.j2`, `templates/ai_agent_script.sh.j2`, `files/commands/`, `files/skills/`, `meta/main.yml`.
- **Dependencies**: Requires `community.general` collection (for `community.general.npm` module). Requires `uv` on target for SpecKit and `npm`/`nodejs` for OpenCode and OpenSPEC -- these can be installed by the opt-in `install_dependencies` sub-task or managed externally by the user.
- **Target platforms**: RHEL-family (Fedora, EL) as primary, matching sibling roles.
- **Consumers**: Any playbook currently using `ai_opencode.yml` can migrate to `ansible.builtin.include_role: ansible-role-ai` with equivalent or better configurability.
