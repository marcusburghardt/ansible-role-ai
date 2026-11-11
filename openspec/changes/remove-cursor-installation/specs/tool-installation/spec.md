# Spec Delta

## MODIFIED Requirements

### Requirement: Install Ollama as a managed tool
The role SHALL provide an `install_ollama` entry in `ai_tasks`, enabled by default. The
task file `tasks/install_ollama.yml` SHALL handle installing Ollama via OS-aware method
selection (native package or install script) and managing the systemd service. A
corresponding `vars/install_ollama.yml` file SHALL contain the `_ollama_method_map` that
maps OS families to install methods, following the role's per-task variable-file
convention.

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

## ADDED Requirements

### Requirement: Role scope excludes IDE installation
The role SHALL NOT provide any task that installs an IDE or code editor. IDE
installation SHALL be owned by dedicated per-editor roles such as
`ansible-role-cursor` and the VSCode-specific role.

#### Scenario: Default task list contains no IDE installer
- **WHEN** examining the default `ai_tasks` list in `defaults/main.yml`
- **THEN** no entry SHALL reference an IDE or editor installation task

#### Scenario: Removed Cursor task is absent
- **WHEN** the role is checked out after this change
- **THEN** `tasks/install_cursor.yml` SHALL NOT exist and the dispatcher SHALL NOT
  reference an `install_cursor` entry
