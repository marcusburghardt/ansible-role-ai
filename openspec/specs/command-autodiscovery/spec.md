### Requirement: Auto-discover built-in commands from role files directory
The role SHALL auto-discover all `.md` files in the role's `files/commands/` directory using `ansible.builtin.find` and register the results for deployment. The discovery SHALL occur at runtime so that adding or removing files from `files/commands/` requires no changes to task YAML.

#### Scenario: All built-in commands are discovered
- **WHEN** the `files/commands/` directory contains `checkout_pr.md`, `review_pr.md`, and `refresh_spec_frameworks.md`
- **THEN** all three files SHALL be discovered and registered for deployment

#### Scenario: New command is added to the role
- **WHEN** a new file `my_new_command.md` is added to `files/commands/`
- **THEN** the file SHALL be auto-discovered and deployed without any changes to task YAML

#### Scenario: Command is removed from the role
- **WHEN** a file is removed from `files/commands/`
- **THEN** the file SHALL no longer be discovered or deployed on subsequent runs (existing deployed copies are not removed unless explicit cleanup is used)

### Requirement: Filter built-in commands against a blocklist
The role SHALL provide a variable `ai_opencode_commands_disabled` (default: empty list) that accepts command names without the `.md` extension. Any discovered built-in command whose basename (minus `.md`) matches an entry in this list SHALL be skipped during deployment.

#### Scenario: No commands disabled (default)
- **WHEN** `ai_opencode_commands_disabled` is empty (default)
- **THEN** all discovered built-in commands SHALL be deployed

#### Scenario: Specific command disabled
- **WHEN** `ai_opencode_commands_disabled` contains `checkout_pr`
- **THEN** `checkout_pr.md` SHALL NOT be deployed, but `review_pr.md` and `refresh_spec_frameworks.md` SHALL be deployed

#### Scenario: Multiple commands disabled
- **WHEN** `ai_opencode_commands_disabled` contains `checkout_pr` and `review_pr`
- **THEN** only `refresh_spec_frameworks.md` SHALL be deployed

### Requirement: Deploy custom commands from user-specified local paths
The role SHALL provide a variable `ai_opencode_commands_custom` (default: empty list) that accepts a list of dictionaries. Each dictionary SHALL have a required `src` key (path to the command file, relative to the playbook or absolute) and an optional `name` key (override for the deployed filename). If `name` is omitted, the basename of `src` SHALL be used. Custom commands SHALL be deployed after built-in commands so that name collisions result in the custom version winning.

#### Scenario: No custom commands (default)
- **WHEN** `ai_opencode_commands_custom` is empty (default)
- **THEN** only built-in commands are deployed

#### Scenario: Custom command with default name
- **WHEN** `ai_opencode_commands_custom` contains `{ src: ../shared-commands/deploy_staging.md }`
- **THEN** the file SHALL be copied to `{{ ai_opencode_command_dir }}/deploy_staging.md`

#### Scenario: Custom command with name override
- **WHEN** `ai_opencode_commands_custom` contains `{ src: /opt/team/audit_script.md, name: security_audit.md }`
- **THEN** the file SHALL be copied to `{{ ai_opencode_command_dir }}/security_audit.md`

#### Scenario: Custom command overrides a built-in
- **WHEN** `ai_opencode_commands_custom` contains `{ src: /opt/team/review_pr.md }` and `review_pr` is NOT in `ai_opencode_commands_disabled`
- **THEN** the custom `review_pr.md` SHALL overwrite the built-in version (custom runs after built-in deployment)

#### Scenario: Custom source path does not exist
- **WHEN** `ai_opencode_commands_custom` contains a `src` path that does not exist on the filesystem
- **THEN** the `ansible.builtin.copy` task SHALL fail with a file-not-found error
