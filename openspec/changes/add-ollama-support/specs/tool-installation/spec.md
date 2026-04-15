## ADDED Requirements

### Requirement: Install Ollama as a managed tool
The role SHALL provide an `install_ollama` entry in `ai_tasks`, enabled by default. The
task file `tasks/install_ollama.yml` SHALL handle installing Ollama via OS-aware method
selection (native package or install script) and managing the systemd service. A
corresponding `vars/install_ollama.yml` file SHALL contain the `_ollama_method_map` that
maps OS families to install methods, following the same pattern as
`vars/install_cursor.yml`.

#### Scenario: install_ollama is enabled by default in ai_tasks
- **WHEN** examining the default `ai_tasks` list in `defaults/main.yml`
- **THEN** the `install_ollama` entry SHALL have `enabled: true`

#### Scenario: Dispatcher loads install_ollama vars and tasks
- **WHEN** the `install_ollama` task is enabled and the role runs
- **THEN** the dispatcher SHALL load `vars/install_ollama.yml` (including
  `_ollama_method_map`) and include `tasks/install_ollama.yml`

#### Scenario: install_ollama can be disabled
- **WHEN** the user overrides `ai_tasks` to set `install_ollama` to `enabled: false`
- **THEN** the role SHALL NOT load its vars or include its tasks

### Requirement: Configure Ollama as a managed tool
The role SHALL provide a `configure_ollama` entry in `ai_tasks`, enabled by default. The
task file `tasks/configure_ollama.yml` SHALL handle pulling models from the curated list.
A corresponding `vars/configure_ollama.yml` file SHALL exist to satisfy the dispatcher
pattern.

#### Scenario: configure_ollama is enabled by default in ai_tasks
- **WHEN** examining the default `ai_tasks` list in `defaults/main.yml`
- **THEN** the `configure_ollama` entry SHALL have `enabled: true`

#### Scenario: Dispatcher loads configure_ollama vars and tasks
- **WHEN** the `configure_ollama` task is enabled and the role runs
- **THEN** the dispatcher SHALL load `vars/configure_ollama.yml` and include
  `tasks/configure_ollama.yml`

#### Scenario: configure_ollama can be disabled independently
- **WHEN** the user disables `configure_ollama` but keeps `install_ollama` enabled
- **THEN** the role SHALL install Ollama and manage the service but SHALL NOT pull any
  models

### Requirement: Ollama installation does not require privilege escalation for model pulling
The `install_ollama` task SHALL use `become: true` for both install methods (package
install and install script are both system-level operations). The `configure_ollama` task
SHALL NOT use `become: true` because `ollama pull` operates against the local Ollama
service as a regular user.

#### Scenario: Package install runs with become
- **WHEN** the `install_ollama` task installs via native package manager
- **THEN** the task SHALL run with `become: true`

#### Scenario: Install script runs with become
- **WHEN** the `install_ollama` task executes the install script
- **THEN** the task SHALL run with `become: true`

#### Scenario: Model pulling runs without become
- **WHEN** the `configure_ollama` task pulls models
- **THEN** the `ollama pull` commands SHALL execute without `become: true`
