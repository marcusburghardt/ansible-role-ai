### Requirement: Ephemeral Grafana container for metrics visualization
The role SHALL provide a `configure_grafana_metrics` sub-task (disabled
by default) that deploys a helper script and provisioning files for
running an ephemeral Grafana container with podman. The container SHALL
be pre-configured with the frser-sqlite-datasource plugin and a
pre-built dashboard for the opencode-metrics database.

#### Scenario: Task is disabled by default
- **WHEN** the consumer runs the role with default `ai_tasks` values
- **THEN** the `configure_grafana_metrics` task SHALL NOT execute
- **AND** no Grafana-related files SHALL be deployed

#### Scenario: Task deploys provisioning files and helper script
- **WHEN** the consumer enables `configure_grafana_metrics` in `ai_tasks`
- **AND** runs the role
- **THEN** the role SHALL create the provisioning directory at
  `ai_grafana_metrics_provisioning_dir`
- **AND** SHALL deploy the SQLite datasource configuration
- **AND** SHALL deploy the dashboard provider configuration
- **AND** SHALL deploy the pre-built dashboard JSON
- **AND** SHALL deploy the helper script to `ai_user_scripts_dir` with
  mode 0755

### Requirement: Helper script manages container lifecycle
The helper script SHALL support four subcommands: start, stop, status,
and logs. The script SHALL use podman as the container runtime.

#### Scenario: Start creates the container
- **WHEN** the user runs `opencode-grafana start`
- **AND** podman is installed
- **AND** the metrics data directory exists
- **THEN** the script SHALL start a Grafana container with:
  the frser-sqlite-datasource plugin installed via GF_INSTALL_PLUGINS,
  the metrics data directory bind-mounted to /data/metrics,
  the provisioning directory bind-mounted to /etc/grafana/provisioning,
  the dashboard directory bind-mounted to /var/lib/grafana/dashboards,
  a named volume for Grafana state persistence,
  anonymous admin access enabled,
  port bound to ai_grafana_metrics_port (default 3033)

#### Scenario: Start fails gracefully when podman is missing
- **WHEN** the user runs `opencode-grafana start`
- **AND** podman is not installed
- **THEN** the script SHALL exit with an error message indicating
  podman is required

#### Scenario: Start fails gracefully when metrics database is missing
- **WHEN** the user runs `opencode-grafana start`
- **AND** the metrics data directory does not exist
- **THEN** the script SHALL exit with an error message indicating the
  opencode-metrics plugin needs to collect data first

#### Scenario: Stop removes the container
- **WHEN** the user runs `opencode-grafana stop`
- **THEN** the script SHALL stop and remove the container
- **AND** SHALL NOT remove the named volume (state persists)

#### Scenario: Status shows container state
- **WHEN** the user runs `opencode-grafana status`
- **THEN** the script SHALL display whether the container is running
  and the port it is bound to

### Requirement: Pre-built dashboard with 9 panels
The deployed dashboard JSON SHALL contain 9 panels covering the key
metrics from the opencode-metrics database.

#### Scenario: Dashboard panels query the correct metrics
- **GIVEN** the Grafana container is running
- **AND** the opencode-metrics database contains session data
- **WHEN** the user opens the dashboard at http://localhost:3033
- **THEN** the dashboard SHALL display panels for:
  Daily Cost (time-series),
  Cost by Classification (pie chart),
  Cost by Project (bar chart),
  Cost by Model (bar chart),
  Cache Hit Ratio (time-series),
  Session Count by Day (bar chart),
  Token Usage (time-series with input/output/cache_read),
  Duration Distribution (histogram),
  Top Sessions (table with title, classification, model, cost)

#### Scenario: Dashboard handles empty database gracefully
- **GIVEN** the Grafana container is running
- **AND** the opencode-metrics database exists but has no data
- **WHEN** the user opens the dashboard
- **THEN** the panels SHALL display "No data" without errors

### Requirement: SQLite datasource provisioning
The provisioned datasource SHALL point to the metrics database path
inside the container (/data/metrics/metrics.db) with query-only mode.

#### Scenario: Datasource is auto-configured on first start
- **GIVEN** the provisioning files are deployed
- **WHEN** the user starts the Grafana container for the first time
- **THEN** the SQLite datasource SHALL be available without manual
  configuration
- **AND** SHALL connect to /data/metrics/metrics.db

### Requirement: Grafana state persistence across restarts
The helper script SHALL use a named podman volume for Grafana's
/var/lib/grafana directory to persist user preferences, annotations,
and dashboard modifications across container restarts.

#### Scenario: Dashboard modifications persist after stop/start
- **GIVEN** the user has modified a dashboard panel in Grafana
- **WHEN** the user stops and restarts the container
- **THEN** the dashboard modifications SHALL be preserved
