### Requirement: Opt-in cleanup task for commands
The role SHALL provide a task `cleanup_opencode` (disabled by default in `ai_tasks`) that removes named command files from the command directory. The variable `ai_opencode_commands_cleanup` (default: empty list) SHALL accept command filenames (with `.md` extension). Each listed file SHALL be removed from `{{ ai_opencode_command_dir }}` using `ansible.builtin.file` with `state: absent`.

#### Scenario: Cleanup task is disabled by default
- **WHEN** the user has not modified the `ai_tasks` list
- **THEN** the `cleanup_opencode` task SHALL NOT run

#### Scenario: Cleanup task is enabled and removes commands
- **WHEN** the user enables `cleanup_opencode` in `ai_tasks` and sets `ai_opencode_commands_cleanup` to `[old_command.md]`
- **THEN** `{{ ai_opencode_command_dir }}/old_command.md` SHALL be removed if it exists

#### Scenario: Cleanup target does not exist
- **WHEN** a filename in `ai_opencode_commands_cleanup` does not exist in the command directory
- **THEN** the task SHALL succeed without error (`state: absent` is idempotent)

### Requirement: Opt-in cleanup task for skills
The `cleanup_opencode` task SHALL also remove named skill directories from the skills deploy directory. The variable `ai_opencode_skills_cleanup` (default: empty list) SHALL accept skill directory names. Each listed directory SHALL be removed recursively from `{{ ai_opencode_skills_deploy_dir }}` using `ansible.builtin.file` with `state: absent`.

#### Scenario: Cleanup removes a skill directory
- **WHEN** the user enables `cleanup_opencode` and sets `ai_opencode_skills_cleanup` to `[deprecated-skill]`
- **THEN** `{{ ai_opencode_skills_deploy_dir }}/deprecated-skill/` and all its contents SHALL be removed

#### Scenario: Cleanup target skill does not exist
- **WHEN** a directory name in `ai_opencode_skills_cleanup` does not exist
- **THEN** the task SHALL succeed without error

### Requirement: Cleanup task has its own vars file
The `cleanup_opencode` task SHALL have a corresponding `vars/cleanup_opencode.yml` file following the role's existing pattern of per-task vars files loaded by the main dispatcher.

#### Scenario: Cleanup vars file is loaded when task is enabled
- **WHEN** `cleanup_opencode` is enabled in `ai_tasks`
- **THEN** the dispatcher SHALL load `vars/cleanup_opencode.yml` before including `tasks/cleanup_opencode.yml`
