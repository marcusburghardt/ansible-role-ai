## Purpose

Manages the optional deployment of the opencode-metrics plugin configuration
file, allowing users to customize classification and budget rules via Ansible
variables.

## Requirements

### Requirement: Metrics plugin config variable
The role SHALL provide an `ai_opencode_metrics_config` dict variable (default:
empty dict `{}`) that represents the full content of the opencode-metrics plugin
`config.yaml` file. When non-empty, the role SHALL deploy the config; when empty,
the role SHALL skip deployment and let the plugin create its own defaults at first
run.

#### Scenario: Default config variable is empty
- **WHEN** the consumer does not override `ai_opencode_metrics_config`
- **THEN** the role SHALL NOT deploy a `config.yaml` file to the metrics data directory, allowing the plugin to auto-create its own defaults

#### Scenario: User provides custom config
- **WHEN** the consumer sets `ai_opencode_metrics_config` to a dict containing `version`, `classification_rules`, and `budget_rules` keys
- **THEN** the role SHALL deploy a `config.yaml` file to `ai_opencode_metrics_data_dir` with the exact structure provided by the variable, serialized as YAML

### Requirement: Metrics data directory creation
The role SHALL ensure the metrics data directory
(`ai_opencode_metrics_data_dir`) exists before deploying the config file.
Directory creation SHALL only occur when `ai_opencode_metrics_config` is
non-empty.

#### Scenario: Data directory is created for config deployment
- **WHEN** `ai_opencode_metrics_config` is non-empty and the data directory does not exist
- **THEN** the role SHALL create the directory at `ai_opencode_metrics_data_dir` with mode `0755` before deploying the config file

#### Scenario: Data directory creation is skipped when no config
- **WHEN** `ai_opencode_metrics_config` is empty
- **THEN** the role SHALL NOT attempt to create the metrics data directory (the plugin creates it at first run)

### Requirement: Metrics data directory variable
The role SHALL provide an `ai_opencode_metrics_data_dir` variable (default:
`{{ ai_user_home_dir }}/.local/share/opencode-metrics`) that defines the path to
the metrics plugin data directory. This variable SHALL be used by both the metrics
config deployment and the Grafana metrics visualization tasks. This variable
replaces the previous `ai_grafana_metrics_data_dir` variable.

#### Scenario: Default data directory path
- **WHEN** the consumer does not override `ai_opencode_metrics_data_dir`
- **THEN** the variable SHALL resolve to `~/.local/share/opencode-metrics` (relative to the target user's home directory)

#### Scenario: Grafana task uses the renamed variable
- **WHEN** the `configure_grafana_metrics` task is enabled
- **THEN** the Grafana helper script SHALL use `ai_opencode_metrics_data_dir` for the container bind-mount path

### Requirement: Metrics plugin version variable
The role SHALL provide an `ai_opencode_metrics_version` variable (default: `"0.2.0"`)
that controls how the opencode-metrics plugin is installed. Accepted values are:
- A semver version string (e.g., `"0.2.0"`) -- installs the pinned version from npm.
- `"latest"` -- always installs the newest npm release.
- `"local"` -- loads the plugin from a local repository path specified by
  `ai_opencode_metrics_local_path` instead of npm.

When the value is a semver string or `"latest"`, this variable SHALL be referenced by
the default `ai_opencode_plugins` list to construct the versioned npm package
specifier. When the value is `"local"`, the npm specifier SHALL NOT appear in
`ai_opencode_plugins`.

#### Scenario: Default version is pinned
- **WHEN** the consumer does not override `ai_opencode_metrics_version`
- **THEN** the default `ai_opencode_plugins` list SHALL contain `@mburghardt/opencode-metrics@0.2.0`

#### Scenario: User overrides version
- **WHEN** the consumer sets `ai_opencode_metrics_version` to `"1.0.0"`
- **THEN** the default `ai_opencode_plugins` list SHALL contain `@mburghardt/opencode-metrics@1.0.0`

#### Scenario: Local mode excludes npm entry from plugins list
- **WHEN** the consumer sets `ai_opencode_metrics_version` to `"local"`
- **THEN** the `ai_opencode_plugins` default list SHALL NOT contain any `@mburghardt/opencode-metrics` entry
