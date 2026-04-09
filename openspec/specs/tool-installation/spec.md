### Requirement: Install system-level dependencies via OS package manager
The role SHALL provide an `install_dependencies` sub-task that installs system-level prerequisite packages (nodejs, npm, uv) using `ansible.builtin.package` with `become: true`. This task SHALL be disabled by default (`enabled: false` in `ai_tasks`) and positioned first in the task list to ensure prerequisites are present before any tool installation tasks run. The package list SHALL be sourced from the `packages` variable defined in `vars/<os_family>.yml`.

#### Scenario: Install dependencies when enabled on RHEL-family
- **WHEN** the `install_dependencies` task entry has `enabled: true` in `ai_tasks` and the target is a RHEL-family host
- **THEN** the role installs all packages listed in `vars/redhat.yml` (nodejs, npm, uv) using `ansible.builtin.package` with `become: true` and `state: present`

#### Scenario: Skip dependencies by default
- **WHEN** the `install_dependencies` task entry has `enabled: false` in `ai_tasks` (the default)
- **THEN** the role SHALL NOT attempt to install any system packages and SHALL assume prerequisites are already present

#### Scenario: Dependencies run before tool installations
- **WHEN** `install_dependencies` is enabled and `install_opencode` is also enabled
- **THEN** the `install_dependencies` task SHALL execute before `install_opencode` due to its first position in the `ai_tasks` list

### Requirement: Install OpenCode via npm
The role SHALL install OpenCode (`opencode-ai` npm package) globally using `community.general.npm`. When `ai_opencode_version` is set to `latest`, the role SHALL use `state: latest` to ensure the newest version is installed on every run. When `ai_opencode_version` is set to a specific version string, the role SHALL install that exact version with `state: present`.

#### Scenario: Install latest OpenCode
- **WHEN** `ai_opencode_version` is set to `latest` and the `install_opencode` task is enabled
- **THEN** the role installs `opencode-ai` globally via npm with `state: latest`, ensuring it is updated to the newest version

#### Scenario: Install pinned OpenCode version
- **WHEN** `ai_opencode_version` is set to a specific version (e.g., `0.1.50`) and the `install_opencode` task is enabled
- **THEN** the role installs `opencode-ai` at exactly that version globally via npm with `state: present`

#### Scenario: Skip OpenCode installation
- **WHEN** the `install_opencode` task entry has `enabled: false` in `ai_tasks`
- **THEN** the role SHALL NOT attempt to install OpenCode

### Requirement: Install OpenSPEC via npm
The role SHALL install OpenSPEC (`@fission-ai/openspec` npm package) globally using `community.general.npm`. Version handling SHALL follow the same `latest` vs pinned pattern as OpenCode, controlled by `ai_openspec_version`.

#### Scenario: Install latest OpenSPEC
- **WHEN** `ai_openspec_version` is set to `latest` and the `install_openspec` task is enabled
- **THEN** the role installs `@fission-ai/openspec` globally via npm with `state: latest`

#### Scenario: Install pinned OpenSPEC version
- **WHEN** `ai_openspec_version` is set to a specific version and the `install_openspec` task is enabled
- **THEN** the role installs `@fission-ai/openspec` at that exact version globally via npm with `state: present`

#### Scenario: Skip OpenSPEC installation
- **WHEN** the `install_openspec` task entry has `enabled: false` in `ai_tasks`
- **THEN** the role SHALL NOT attempt to install OpenSPEC

### Requirement: Install SpecKit via uv from GitHub
The role SHALL install SpecKit (`specify-cli`) using `uv tool install` from the GitHub repository. When `ai_speckit_version` is set to `latest`, the role SHALL query the GitHub API (`https://api.github.com/repos/github/spec-kit/releases/latest`) to resolve the latest release tag, then install from that tag. When set to a specific tag (e.g., `v0.4.4`), the role SHALL install directly from that tag.

#### Scenario: Install latest SpecKit
- **WHEN** `ai_speckit_version` is set to `latest` and the `install_speckit` task is enabled
- **THEN** the role queries the GitHub API to resolve the latest release tag and installs SpecKit from `git+https://github.com/github/spec-kit.git@<resolved_tag>` using `uv tool install --force`

#### Scenario: Install pinned SpecKit version
- **WHEN** `ai_speckit_version` is set to a specific tag (e.g., `v0.4.4`) and the `install_speckit` task is enabled
- **THEN** the role installs SpecKit from `git+https://github.com/github/spec-kit.git@v0.4.4` using `uv tool install --force`

#### Scenario: Skip SpecKit installation
- **WHEN** the `install_speckit` task entry has `enabled: false` in `ai_tasks`
- **THEN** the role SHALL NOT attempt to install SpecKit

### Requirement: Installation tasks require privilege escalation
The npm global installation tasks (`install_opencode`, `install_openspec`) SHALL use `become: true` for privilege escalation. The SpecKit installation (`install_speckit`) SHALL NOT use `become: true` because `uv tool install` operates in user space.

#### Scenario: npm tasks use become
- **WHEN** the `install_opencode` or `install_openspec` task runs
- **THEN** the npm install task SHALL execute with `become: true`

#### Scenario: SpecKit task runs without become
- **WHEN** the `install_speckit` task runs
- **THEN** the uv install command SHALL execute without `become: true`

### Requirement: Ensure required directories exist before installation
The role SHALL ensure that the `~/.npm` directory and the user scripts directory (`ai_user_scripts_dir`) exist before any installation tasks run. These directory tasks SHALL be included in the relevant install task files.

#### Scenario: npm directory is created
- **WHEN** the `install_opencode` or `install_openspec` task runs
- **THEN** the `~/.npm` directory SHALL exist with mode `0750` before npm operations

#### Scenario: Scripts directory is created
- **WHEN** the `configure_opencode` task runs
- **THEN** the `ai_user_scripts_dir` directory SHALL exist with mode `0750`
