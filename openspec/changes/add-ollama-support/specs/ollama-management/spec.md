## ADDED Requirements

### Requirement: Install Ollama with OS-aware method selection
The role SHALL provide an `install_ollama` sub-task that installs Ollama using a method
determined by `ai_ollama_install_method` (default: `auto`). When set to `auto`, the method
SHALL be resolved from `_ollama_method_map` keyed by `ansible_facts['os_family']`, falling
back to `script` for unmapped OS families. The supported methods are `package` (via
`ansible.builtin.package`) and `script` (via the official install script). The task SHALL
be idempotent by checking whether the `ollama` binary is already present on the system.

#### Scenario: Install Ollama via native package on RedHat family
- **WHEN** the `install_ollama` task is enabled and `ai_ollama_install_method` is `auto`
  and the target is a RedHat-family host and Ollama is not installed
- **THEN** the role SHALL install Ollama using `ansible.builtin.package` with
  `name: ollama` and `state: present` with `become: true`

#### Scenario: Install Ollama via native package on Debian family
- **WHEN** the `install_ollama` task is enabled and `ai_ollama_install_method` is `auto`
  and the target is a Debian-family host and Ollama is not installed
- **THEN** the role SHALL install Ollama using `ansible.builtin.package` with
  `name: ollama` and `state: present` with `become: true`

#### Scenario: Install Ollama via install script on unknown OS family
- **WHEN** the `install_ollama` task is enabled and `ai_ollama_install_method` is `auto`
  and the target OS family is not in `_ollama_method_map` and Ollama is not installed
- **THEN** the role SHALL download the official install script, execute it with
  `become: true`, and the `ollama` binary SHALL be present after completion

#### Scenario: User forces script method on a supported OS
- **WHEN** the user overrides `ai_ollama_install_method` to `script` on a RedHat-family
  host
- **THEN** the role SHALL use the install script instead of the native package manager

#### Scenario: Skip installation when Ollama is already installed
- **WHEN** the `install_ollama` task is enabled and the `ollama` binary is already present
  on the system (at either `/usr/bin/ollama` or `/usr/local/bin/ollama`)
- **THEN** the role SHALL skip the installation step without error

#### Scenario: Skip Ollama installation when task is disabled
- **WHEN** the `install_ollama` task entry has `enabled: false` in `ai_tasks`
- **THEN** the role SHALL NOT attempt to install Ollama

### Requirement: Manage Ollama systemd service lifecycle
The role SHALL manage the Ollama systemd service within the `install_ollama` task using
`ansible.builtin.systemd_service`. The service state SHALL be controlled by
`ai_ollama_service_state` (default: `started`) and persistence across reboots SHALL be
controlled by `ai_ollama_service_enabled` (default: `false`).

#### Scenario: Service is started but not enabled by default
- **WHEN** the `install_ollama` task runs with default variable values
- **THEN** the `ollama` systemd service SHALL be in `started` state and SHALL NOT be
  enabled for automatic start on boot

#### Scenario: Service is started and enabled
- **WHEN** `ai_ollama_service_state` is `started` and `ai_ollama_service_enabled` is
  `true`
- **THEN** the `ollama` systemd service SHALL be in `started` state and SHALL be enabled
  for automatic start on boot

#### Scenario: Service is installed but stopped
- **WHEN** `ai_ollama_service_state` is `stopped`
- **THEN** the `ollama` systemd service SHALL be in `stopped` state

### Requirement: Pull enabled models from curated list
The role SHALL provide a `configure_ollama` sub-task that pulls models listed in
`ai_ollama_models` where `enabled` is `true`. Each model SHALL be pulled using the
`ollama pull <name>` command. The task SHALL only attempt pulls when the Ollama service is
running.

#### Scenario: Pull default model on fresh setup
- **WHEN** the `configure_ollama` task is enabled and the Ollama service is running and
  `ai_ollama_models` contains `{ enabled: true, name: 'qwen3:8b' }`
- **THEN** the role SHALL execute `ollama pull qwen3:8b` to download the model

#### Scenario: Skip disabled models
- **WHEN** `ai_ollama_models` contains `{ enabled: false, name: 'qwen3:32b' }`
- **THEN** the role SHALL NOT pull `qwen3:32b`

#### Scenario: Pull multiple enabled models
- **WHEN** `ai_ollama_models` contains multiple entries with `enabled: true`
- **THEN** the role SHALL pull each enabled model in sequence

#### Scenario: Skip pulls when service is not running
- **WHEN** the `configure_ollama` task is enabled but the Ollama service is not running
  (e.g., `ai_ollama_service_state` is `stopped`)
- **THEN** the role SHALL skip all model pull operations without error and SHALL display a
  debug message indicating that pulls were skipped because the service is not running

#### Scenario: Skip configure_ollama when task is disabled
- **WHEN** the `configure_ollama` task entry has `enabled: false` in `ai_tasks`
- **THEN** the role SHALL NOT attempt any model pull operations

### Requirement: Curated model list with sensible defaults
The `ai_ollama_models` variable SHALL be a list of dicts with `enabled` (boolean) and
`name` (string) keys, following the same pattern as `ai_tasks`. The default list SHALL
include at least the following models: `qwen3:8b`, `qwen3:32b`, `devstral`,
`qwen3-coder:a3b`, and `llama3.1:8b`. Only `qwen3:8b` SHALL be enabled by default. Users
SHALL be able to override the entire list or individual entries in their playbooks.

#### Scenario: Default model list enables only qwen3:8b
- **WHEN** `ai_ollama_models` uses the default value
- **THEN** only `qwen3:8b` SHALL have `enabled: true`; all other models SHALL have
  `enabled: false`

#### Scenario: User enables additional models
- **WHEN** the user overrides `ai_ollama_models` in their playbook to set
  `{ enabled: true, name: 'qwen3:32b' }` alongside the default entry
- **THEN** both `qwen3:8b` and `qwen3:32b` SHALL be pulled

### Requirement: Ollama tasks positioned before OpenCode configuration
The `install_ollama` and `configure_ollama` entries in `ai_tasks` SHALL be positioned
after `install_dependencies` and before `install_opencode`, ensuring Ollama is available
before OpenCode configuration references it.

#### Scenario: Task ordering in ai_tasks
- **WHEN** examining the default `ai_tasks` list
- **THEN** `install_ollama` SHALL appear after `install_dependencies` and before
  `install_opencode`, and `configure_ollama` SHALL appear after `install_ollama` and
  before `install_opencode`
