## Why

The opencode-metrics plugin collects session metrics into a local SQLite
database (~/.local/share/opencode-metrics/metrics.db) with a dimensional
schema designed for analytics. However, there is no visualization layer
deployed by the role. Users must manually set up Grafana, install the
SQLite datasource plugin, configure the datasource, and build dashboards
from scratch. This friction prevents the feedback loop that makes the
metrics collection valuable.

This change adds an opt-in sub-task that deploys a helper script to run
an ephemeral Grafana container (podman) pre-configured with the SQLite
datasource and a pre-built dashboard. The user starts Grafana on demand
-- no persistent service, no systemd, no manual configuration.

## What Changes

- Add `configure_grafana_metrics` to `ai_tasks` (disabled by default,
  like `install_cursor`).
- Add variables for port, container name, script name, data directory,
  and provisioning directory.
- Deploy Grafana provisioning files: SQLite datasource config, dashboard
  provider config, and a pre-built dashboard JSON with 9 panels.
- Deploy a helper script (`~/bin/opencode-grafana`) that wraps podman
  commands for start/stop/status/logs.
- Document the new task and variables in README.md.

## Capabilities

### New Capabilities

- `grafana-metrics`: Ephemeral Grafana container with pre-built
  opencode-metrics dashboard.

### Modified Capabilities

None. This is a standalone sub-task with no modifications to existing
capabilities.

## Impact

- **Files added**: `tasks/configure_grafana_metrics.yml`,
  `vars/configure_grafana_metrics.yml`,
  `templates/opencode_grafana.sh.j2`,
  `files/grafana/provisioning/datasources/sqlite.yaml`,
  `files/grafana/provisioning/dashboards/provider.yaml`,
  `files/grafana/dashboards/opencode-metrics.json`
- **Files modified**: `defaults/main.yml`, `README.md`
- **Backward compatibility**: Full. New task is disabled by default.
  Existing tasks are unmodified.
- **Dependencies**: Requires podman on the target host. Does not install
  podman -- assumes it is already present (standard on Fedora/RHEL).
- **Breaking changes**: None.
