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

### Requirement: Pre-built dashboard with approximately 30 panels
The deployed dashboard JSON SHALL contain approximately 30 panels
organized in 8 collapsible row sections covering cost overview, token
efficiency, session analytics, efficiency metrics, code impact, top
sessions, and trends from the opencode-metrics database. A KPI summary
row SHALL be permanently expanded at the top of the dashboard. All
detail sections SHALL be collapsed by default.

#### Scenario: Dashboard panels query the correct metrics
- **GIVEN** the Grafana container is running
- **AND** the opencode-metrics database contains session data
- **WHEN** the user opens the dashboard at http://localhost:3033
- **THEN** the dashboard SHALL display a KPI row with stat panels for:
  Total Sessions, Total Cost, Avg Session Cost, Cache Hit %,
  Output Tokens (M), Active Projects
- **AND** SHALL display collapsible sections for:
  Cost Overview (Daily Cost, Cost by Classification, Cost by Model,
  Cost by Project, Avg Cost by Classification),
  Token Efficiency (Token Usage Over Time, Token Distribution,
  Cache Hit Ratio Over Time),
  Session Analytics (Sessions by Day, Sessions by Classification
  Over Time, Duration Distribution, Sessions by Agent Type,
  Avg Duration by Classification, Messages per Classification),
  Efficiency (Cost per 1K Output Tokens, Cache Hit by Classification,
  Cost per File Changed),
  Code Impact (Lines Changed Over Time, Files Changed by Project),
  Top Sessions (table with title, classification, model, agent,
  project, cost, date),
  Trends (Weekly Cost, 7-Day Rolling Average Cost)

#### Scenario: Dashboard auto-refreshes to show new data
- **GIVEN** the Grafana container is running
- **AND** the dashboard is open in a browser
- **WHEN** new sessions are recorded in the metrics database
- **THEN** the dashboard SHALL auto-refresh at a 30-second interval

#### Scenario: Time-series panels render data correctly
- **GIVEN** the opencode-metrics database stores timestamps as epoch
  milliseconds
- **WHEN** the dashboard queries time-series data
- **THEN** all time-series panels SHALL use epoch seconds (numeric) as
  the time column to avoid RFC3339 parsing failures

#### Scenario: Pie chart panels render multiple slices
- **GIVEN** the opencode-metrics database contains sessions with
  multiple distinct classifications
- **WHEN** the user views a pie chart panel
- **THEN** each distinct category SHALL render as a separate slice

#### Scenario: Project charts remain readable with many projects
- **GIVEN** the opencode-metrics database contains more than 10
  distinct projects
- **WHEN** the user views a project bar chart
- **THEN** the chart SHALL display the top 10 projects individually
- **AND** SHALL aggregate remaining projects into an "Other" bucket

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
