### Requirement: Three-phase task dispatcher in main.yml
The `tasks/main.yml` file SHALL implement the 3-phase dispatcher pattern: (1) include OS-family-specific variables from `vars/{{ ansible_facts['os_family']|lower }}.yml`, (2) loop over `ai_tasks` and include per-task variables from `vars/{{ task.name }}.yml` for enabled tasks, (3) loop over `ai_tasks` and include task files from `tasks/{{ task.name }}.yml` for enabled tasks.

#### Scenario: OS-specific variables are loaded
- **WHEN** the role runs on a RHEL-family host
- **THEN** variables from `vars/redhat.yml` SHALL be loaded

#### Scenario: Only enabled task variables are loaded
- **WHEN** `ai_tasks` contains entries with `enabled: true` and `enabled: false`
- **THEN** only variables for tasks with `enabled: true` SHALL be included

#### Scenario: Only enabled task files are executed
- **WHEN** `ai_tasks` contains entries with `enabled: true` and `enabled: false`
- **THEN** only task files for tasks with `enabled: true` SHALL be included and executed

#### Scenario: Loop variable is named task
- **WHEN** the dispatcher loops over `ai_tasks`
- **THEN** the loop variable SHALL be named `task` via `loop_control.loop_var` to keep `item` available for sub-tasks

### Requirement: Data-driven task list with enabled flags
The `defaults/main.yml` file SHALL define an `ai_tasks` list variable where each entry has `enabled` (boolean) and `name` (string matching the task filename without `.yml`). All tasks SHALL default to `enabled: true`.

#### Scenario: Default task list includes all sub-tasks
- **WHEN** the role is used without overriding `ai_tasks`
- **THEN** the default `ai_tasks` list SHALL contain entries for `install_opencode`, `configure_opencode`, `install_openspec`, and `install_speckit`, all with `enabled: true`

#### Scenario: Consumer disables a specific task
- **WHEN** the consumer sets `ai_tasks` with `install_speckit` having `enabled: false`
- **THEN** the SpecKit installation SHALL be skipped entirely

### Requirement: OS-family-specific variables file
The role SHALL include a `vars/redhat.yml` file containing package lists specific to RHEL-family distributions. The variable `packages` SHALL list any system packages required by the role's tools.

#### Scenario: RedHat variables define required packages
- **WHEN** the role runs on a RHEL-family host
- **THEN** `vars/redhat.yml` SHALL be loaded and define the `packages` variable with npm-related package names

### Requirement: Per-task variable files
Each sub-task SHALL have a corresponding `vars/<task_name>.yml` file for task-scoped internal variables. These files MAY be empty placeholders if the task has no internal variables.

#### Scenario: Task variables are scoped to their task
- **WHEN** the `install_opencode` task is enabled
- **THEN** variables from `vars/install_opencode.yml` SHALL be loaded before the task file runs

### Requirement: Consistent task naming convention
All task names SHALL follow the pattern `"{{ role_name }} | {{ task.name }} | <action description>"` for traceability in Ansible output.

#### Scenario: Task names are hierarchical
- **WHEN** any task in the role executes
- **THEN** its `name` field SHALL follow the `{{ role_name }} | {{ task.name }} | <description>` pattern

### Requirement: Variable prefix convention
All user-facing variables defined by the role SHALL use the `ai_` prefix to avoid naming collisions with other roles and playbook variables.

#### Scenario: No unprefixed variables in defaults
- **WHEN** examining `defaults/main.yml`
- **THEN** every variable name SHALL start with `ai_`

### Requirement: README documents role usage
The `README.md` file SHALL replace the default boilerplate with proper documentation following the sibling role pattern. It SHALL include: a role description with bullet list of what the role does, a requirements section listing prerequisites, a role variables section referencing `defaults/main.yml` with key variables explained, example playbooks showing common usage patterns, license information matching the repository LICENSE, and author contact information.

#### Scenario: README contains actionable information
- **WHEN** a new user reads the README
- **THEN** it SHALL contain enough information to consume the role: what it does, what variables to set, and a copy-pasteable playbook example

### Requirement: No sensitive defaults in published role
All default values in `defaults/main.yml` SHALL use safe placeholder values suitable for public publishing on Ansible Galaxy. Variables that reference internal infrastructure (GCP project names, internal regions) SHALL use clearly placeholder values (e.g., `your-gcp-project`). The README SHALL document which variables must be set for specific provider configurations.

#### Scenario: GCP variables use placeholders
- **WHEN** examining `defaults/main.yml`
- **THEN** `ai_gcp_project` SHALL default to `your-gcp-project` and `ai_vertex_location` SHALL default to `us-central1`

#### Scenario: README documents required configuration for Vertex
- **WHEN** a user wants to use Google Vertex AI as the provider
- **THEN** the README SHALL clearly state that `ai_gcp_project` and `ai_vertex_location` must be set to real values

#### Scenario: Placeholders are harmless for non-Vertex users
- **WHEN** a user is not using Google Vertex AI
- **THEN** the placeholder values SHALL be exported as env vars by the wrapper script but SHALL NOT cause errors or side effects in OpenCode

### Requirement: Runnable smoke test
The `tests/test.yml` file SHALL be a runnable smoke test that exercises the role's dispatcher pattern and configuration deployment without requiring external tools (npm, uv) or API access. Install tasks SHALL be disabled in the test playbook so it can run in a minimal environment.

#### Scenario: Test runs without npm/uv installed
- **WHEN** `tests/test.yml` is executed on a host without npm or uv
- **THEN** the playbook SHALL complete successfully because install tasks are disabled

#### Scenario: Test exercises dispatcher and config deployment
- **WHEN** `tests/test.yml` is executed
- **THEN** it SHALL exercise the 3-phase dispatcher and the `configure_opencode` task, verifying directory creation, template rendering, and command file deployment

### Requirement: YAML lint configuration
The role SHALL include a `.yamllint` configuration file for YAML linting consistency. The configuration SHALL define rules appropriate for Ansible roles.

#### Scenario: yamllint validates role files
- **WHEN** `yamllint .` is run in the role directory
- **THEN** all YAML files SHALL pass validation with the configured rules

### Requirement: Consistent license identifiers across all files
All SPDX license identifier headers in role files SHALL use `Apache-2.0` to match the role's declared license in `meta/main.yml` and `README.md`. No scaffolded `MIT-0` headers SHALL remain.

#### Scenario: No mismatched license headers
- **WHEN** examining all files with SPDX headers
- **THEN** every `SPDX-License-Identifier` SHALL specify `Apache-2.0`

### Requirement: Galaxy metadata is properly configured
The `meta/main.yml` file SHALL contain accurate Galaxy metadata including author, description, license (matching the repository LICENSE file), minimum Ansible version, supported platforms, and relevant galaxy tags.

#### Scenario: Meta contains correct values
- **WHEN** the role is published or consumed
- **THEN** `meta/main.yml` SHALL specify `author: Marcus Burghardt`, `license: Apache-2.0`, `min_ansible_version: '2.16'`, platforms for EL and Fedora, and relevant tags such as `ai`, `opencode`, `developer-tools`
