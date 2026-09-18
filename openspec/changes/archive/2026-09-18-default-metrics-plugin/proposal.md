# Proposal

## Why

The `@mburghardt/opencode-metrics` plugin is now officially published on npm and
is maintained alongside this role. Users currently need to know the exact npm
package name and manually add it to `ai_opencode_plugins` -- an unnecessary
friction point for a first-party plugin. Shipping it as a default gives every
user automatic metrics collection out of the box while preserving the ability to
opt out by editing the plugin list.

## What Changes

- **Default plugin list**: `ai_opencode_plugins` changes from an empty list to a
  list containing `@mburghardt/opencode-metrics` at a pinned version.
- **Pinned version variable**: New `ai_opencode_metrics_version` variable
  (default: `"0.2.0"`) controls the plugin version. Manually updated when the
  plugin releases a new version.
- **Variable rename**: `ai_grafana_metrics_data_dir` is renamed to
  `ai_opencode_metrics_data_dir` to reflect that the data directory belongs to
  the metrics plugin, not Grafana specifically. All consumers of the old variable
  (Grafana template, README) are updated. This rename supersedes the definition
  established in the archived change `2026-09-16-configure-grafana-metrics`.
- **Optional plugin config templating**: New `ai_opencode_metrics_config`
  variable (default: `{}`) allows users to customize classification and budget
  rules via their playbook. When non-empty, the role deploys a `config.yaml` to
  the plugin's data directory. When empty, the plugin creates its own defaults at
  first run.
- **New template**: `opencode_metrics_config.yaml.j2` renders the user-provided
  config structure.
- **README updates**: Variable table and plugin documentation updated to reflect
  the new defaults and variables.

## Capabilities

### New Capabilities

- `metrics-plugin-config`: Manages the optional deployment of the
  opencode-metrics plugin configuration file (`config.yaml`) with user-defined
  classification and budget rules.

### Modified Capabilities

- `opencode-configuration`: The plugin list default changes from empty to
  containing the metrics plugin. A new version variable is introduced. The
  `ai_grafana_metrics_data_dir` variable is renamed to
  `ai_opencode_metrics_data_dir`.

## Impact

- **defaults/main.yml**: New variables (`ai_opencode_metrics_version`,
  `ai_opencode_metrics_config`), changed default for `ai_opencode_plugins`,
  renamed `ai_grafana_metrics_data_dir` to `ai_opencode_metrics_data_dir`.
- **tasks/configure_opencode.yml**: Two new conditional tasks for metrics config
  deployment.
- **templates/opencode_metrics_config.yaml.j2**: New template file.
- **templates/opencode_grafana.sh.j2**: Variable reference rename.
- **README.md**: Variable table and documentation updates.
- **Backward compatibility**: Users who previously set `ai_opencode_plugins: []`
  explicitly will retain that behavior. Users who relied on the default empty
  list will now get the metrics plugin. Users referencing
  `ai_grafana_metrics_data_dir` directly must update to the new name --
  **BREAKING** for playbooks using the old variable name.
