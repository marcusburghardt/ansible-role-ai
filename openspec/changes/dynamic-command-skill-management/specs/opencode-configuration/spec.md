## MODIFIED Requirements

### Requirement: Deploy Ansible-managed commands to user config directory
The role SHALL auto-discover all `.md` files in the role's `files/commands/` directory at runtime and deploy them to `{{ ai_opencode_command_dir }}`. Commands whose basename (minus `.md`) appears in `ai_opencode_commands_disabled` SHALL be skipped. After built-in deployment, custom commands from `ai_opencode_commands_custom` SHALL be deployed, each using its `src` path as the source and `name` (or basename of `src`) as the destination filename. All command files SHALL be copied as-is without template processing using `ansible.builtin.copy` with mode `0640`. Managed files SHALL be overwritten on every role execution. The role SHALL NOT delete, modify, or interfere with any other files in the command directory that are not part of the current deployment run.

#### Scenario: Default behavior deploys all built-in commands
- **WHEN** `ai_opencode_commands_disabled` is empty and `ai_opencode_commands_custom` is empty
- **THEN** all `.md` files in `files/commands/` SHALL be deployed to `{{ ai_opencode_command_dir }}`

#### Scenario: Built-in command is disabled
- **WHEN** `ai_opencode_commands_disabled` contains `checkout_pr`
- **THEN** `checkout_pr.md` SHALL NOT be deployed, but all other built-in commands SHALL be

#### Scenario: Custom command is deployed alongside built-ins
- **WHEN** `ai_opencode_commands_custom` contains `{ src: ../my-commands/deploy.md }`
- **THEN** `deploy.md` SHALL be deployed to `{{ ai_opencode_command_dir }}` alongside the built-in commands

#### Scenario: User-created commands are not affected
- **WHEN** the user has created custom command files directly in `{{ ai_opencode_command_dir }}`
- **THEN** those files SHALL remain untouched after the role runs

#### Scenario: Commands directory is created if missing
- **WHEN** the `{{ ai_opencode_command_dir }}` directory does not exist
- **THEN** the role SHALL create it before deploying command files

### Requirement: Ensure user skills directories exist (OpenCode-specific and agent-neutral)
The role SHALL ensure both `{{ ai_opencode_skills_dir }}` (OpenCode-specific) and `{{ ai_user_home_dir }}/.agents/skills/` (agent-neutral) directories exist. Built-in skills from `files/skills/` SHALL be auto-discovered and deployed to `{{ ai_opencode_skills_deploy_dir }}` (resolved via `ai_skills_target`), filtered against `ai_opencode_skills_disabled`. Custom skills from `ai_opencode_skills_custom` SHALL be deployed after built-ins. The role SHALL NOT delete, modify, or interfere with any other directories in the skills directory that are not part of the current deployment run.

#### Scenario: OpenCode skills directory is created if missing
- **WHEN** the `{{ ai_opencode_skills_dir }}` directory does not exist
- **THEN** the role SHALL create it

#### Scenario: Agent-neutral skills directory is created if missing
- **WHEN** the `{{ ai_user_home_dir }}/.agents/skills/` directory does not exist
- **THEN** the role SHALL create it

#### Scenario: Built-in skills are deployed to configured target
- **WHEN** `files/skills/` contains skill directories and `ai_skills_target` is `agent-neutral`
- **THEN** the skills SHALL be deployed to `{{ ai_user_home_dir }}/.agents/skills/`

#### Scenario: Custom skills are deployed alongside built-ins
- **WHEN** `ai_opencode_skills_custom` contains `{ src: /opt/team/my-skill }`
- **THEN** the `my-skill/` directory SHALL be deployed to `{{ ai_opencode_skills_deploy_dir }}/my-skill/`

#### Scenario: User-created skills are not affected
- **WHEN** the user has created custom skill directories in the skills deploy directory
- **THEN** those directories and files SHALL remain untouched after the role runs
