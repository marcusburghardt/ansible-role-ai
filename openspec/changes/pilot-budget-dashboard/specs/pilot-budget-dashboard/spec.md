# Spec Delta

## Purpose

Provides a governance-focused Grafana dashboard for fixed-duration AI pilot
programs, tracking spend against a total budget, scoping activity to approved
repositories, and surfacing data quality and evidence status for weekly
reporting.

## ADDED Requirements

### Requirement: Pilot budget variables with safe defaults

The role SHALL provide the following variables in `defaults/main.yml` for
configuring the pilot budget dashboard:

- `ai_grafana_pilot_budget` (default: `0`) -- total working budget in USD
  for the pilot period.
- `ai_grafana_pilot_review_threshold` (default: `0`) -- escalation
  threshold in USD that triggers a management review.
- `ai_grafana_pilot_start_date` (default: `""`) -- pilot start date in
  ISO 8601 format (YYYY-MM-DD).
- `ai_grafana_pilot_end_date` (default: `""`) -- pilot end date in
  ISO 8601 format (YYYY-MM-DD).
- `ai_grafana_pilot_repos` (default: `[]`) -- list of approved repository
  names that match the `name` column in the metrics SQLite `projects`
  table.

When `ai_grafana_pilot_repos` is empty or `ai_grafana_pilot_start_date`
is empty, the pilot dashboard SHALL NOT be deployed.

#### Scenario: Pilot dashboard is not deployed when variables are unset

- **GIVEN** `ai_grafana_pilot_repos` is `[]`
- **AND** `ai_grafana_pilot_start_date` is `""`
- **WHEN** the `configure_grafana_metrics` task runs
- **THEN** the pilot dashboard JSON file SHALL NOT be created in the
  dashboards directory

#### Scenario: Pilot dashboard is deployed when variables are configured

- **GIVEN** `ai_grafana_pilot_budget` is `500` (example value)
- **AND** `ai_grafana_pilot_review_threshold` is `1000` (example value)
- **AND** `ai_grafana_pilot_start_date` is `"2026-09-15"` (example date)
- **AND** `ai_grafana_pilot_end_date` is `"2026-11-14"` (example date)
- **AND** `ai_grafana_pilot_repos` is `["repo-a", "repo-b", "repo-c"]`
- **WHEN** the `configure_grafana_metrics` task runs
- **THEN** the pilot dashboard JSON file SHALL be created in the
  dashboards directory alongside the operational dashboard

### Requirement: Pilot budget KPI row

The pilot dashboard SHALL display a permanently expanded row titled
"Pilot Budget" at the top of the dashboard. This row SHALL contain:

- A "Pilot-to-Date Cost" stat panel showing the total cost of sessions
  in approved repositories since `ai_grafana_pilot_start_date`, with
  color thresholds at `ai_grafana_pilot_budget` (warn) and
  `ai_grafana_pilot_review_threshold` (crit).
- A "This Week" stat panel showing the cost of approved-repo sessions
  in the current Monday-Sunday week.
- A "Budget Remaining" stat panel showing
  `ai_grafana_pilot_budget` minus pilot-to-date cost.
- A "Days Remaining" stat panel showing the number of days between now
  and `ai_grafana_pilot_end_date`.
- A "Burn Rate" stat panel showing the average daily cost over the
  pilot period so far, for budget forecasting.
- A "Excluded/Unattributed Cost" stat panel showing the total cost of
  sessions NOT attributed to any approved repository during the pilot
  period.

#### Scenario: Budget KPI panels reflect pilot scope

- **GIVEN** the Grafana container is running
- **AND** the opencode-metrics database contains sessions for both
  approved and non-approved repositories
- **WHEN** the user opens the pilot dashboard
- **THEN** the "Pilot-to-Date Cost" panel SHALL include only sessions
  whose project name matches one of the `ai_grafana_pilot_repos` values
- **AND** the "Excluded/Unattributed Cost" panel SHALL include sessions
  whose project name does NOT match any approved repo or is empty/unknown
- **AND** both panels SHALL only count sessions within the pilot date
  range

#### Scenario: Budget thresholds use pilot-specific values

- **GIVEN** `ai_grafana_pilot_budget` is `500` (example value)
- **AND** `ai_grafana_pilot_review_threshold` is `1000` (example value)
- **WHEN** the pilot-to-date cost exceeds the configured budget (e.g., $500)
- **THEN** the "Pilot-to-Date Cost" panel SHALL display in amber/warning
  color
- **AND** when the cost exceeds the review threshold (e.g., $1,000), it
  SHALL display in red/critical color

### Requirement: Repository attribution row

The pilot dashboard SHALL display a collapsed row titled "Repository
Attribution" containing:

- A bar chart showing cost per approved repository.
- A time-series panel showing daily cost per approved repository.
- A stat panel showing the number of sessions per approved repository.

All panels in this row SHALL filter to only the approved repositories
defined in `ai_grafana_pilot_repos` and only sessions within the pilot
date range.

#### Scenario: Repository panels scope to approved repos only

- **GIVEN** the opencode-metrics database contains sessions for
  repositories "repo-a", "repo-b", and "repo-x" (where "repo-x" is
  not in the approved list)
- **WHEN** the user expands the "Repository Attribution" row
- **THEN** the cost bar chart SHALL show only "repo-a" and "repo-b"
- **AND** "repo-x" SHALL NOT appear in any panel in this row

### Requirement: Work output row

The pilot dashboard SHALL display a collapsed row titled "Work Output"
containing panels for:

- PRs created count (scoped to pilot repos and date range).
- PRs reviewed count (scoped to pilot repos and date range).
- Issues referenced count (scoped to pilot repos and date range).
- Non-deliverable spend percentage (sessions with zero PRs and zero
  issues in approved repos).
- Most expensive PRs table (showing PR reference, cost, and session
  count, scoped to approved repos).

#### Scenario: Work output panels scope to pilot

- **GIVEN** the opencode-metrics database contains PR and issue metrics
  for both approved and non-approved repositories
- **WHEN** the user expands the "Work Output" row
- **THEN** all panels SHALL count only sessions attributed to approved
  repositories within the pilot date range

### Requirement: Session breakdown row

The pilot dashboard SHALL display a collapsed row titled "Session
Breakdown" containing panels for:

- Root session count (sessions without a parent, in approved repos).
- Child session count (sessions with a parent, in approved repos).
- Cost split: root sessions vs sub-agent sessions (time-series).
- Classification breakdown (cost by classification in approved repos).

#### Scenario: Session counts distinguish root and child sessions

- **GIVEN** the opencode-metrics database contains root sessions that
  spawned sub-agent sessions for approved repositories
- **WHEN** the user expands the "Session Breakdown" row
- **THEN** the root session count SHALL count only sessions where
  `parent_session_id IS NULL`
- **AND** the child session count SHALL count only sessions where
  `parent_session_id IS NOT NULL`
- **AND** both counts SHALL be scoped to approved repos and pilot dates

### Requirement: Model and token detail row

The pilot dashboard SHALL display a collapsed row titled "Model & Token
Detail" containing panels for:

- Cost by model (bar chart, scoped to pilot repos and dates).
- Token usage by type (input, output, cache read, scoped to pilot).
- Cost per 1K output tokens (stat, scoped to pilot).

#### Scenario: Model breakdown scopes to pilot activity

- **GIVEN** the opencode-metrics database contains sessions using
  multiple models across approved and non-approved repositories
- **WHEN** the user expands the "Model & Token Detail" row
- **THEN** the cost by model panel SHALL include only sessions from
  approved repositories within the pilot date range

### Requirement: Data quality and evidence status row

The pilot dashboard SHALL display a collapsed row titled "Data Quality &
Evidence" containing:

- A "Last Data Point" stat panel showing the timestamp of the most
  recent measurement in the database.
- A text panel with a static disclaimer stating that all cost values
  are OpenCode local estimates computed by the metrics plugin, not
  GCP-reconciled or authoritative billing values. Estimates SHALL NOT
  be presented as final billing.
- A "Sessions with Missing Metadata" stat panel showing the count of
  sessions where project name is empty or "unknown" within the pilot
  date range.
- Placeholder stat panels for future controls metrics (blocked prompts,
  hard stops, unmatched sessions, reconciliation failures), each
  displaying "No data" with a description explaining the metric's
  purpose and that upstream data collection is not yet implemented.

#### Scenario: Data freshness indicator shows last measurement time

- **GIVEN** the opencode-metrics database contains measurements
- **WHEN** the user expands the "Data Quality & Evidence" row
- **THEN** the "Last Data Point" panel SHALL display the timestamp of
  the most recent `recorded_at_epoch` value from the measurements table

#### Scenario: Estimate disclaimer is always visible

- **GIVEN** the pilot dashboard is deployed
- **WHEN** the user expands the "Data Quality & Evidence" row
- **THEN** a text panel SHALL display a disclaimer that all cost values
  are local estimates and not GCP-reconciled billing

#### Scenario: Placeholder panels show No data gracefully

- **GIVEN** the opencode-metrics database does not contain guardrail
  event data
- **WHEN** the user views the placeholder panels for controls metrics
- **THEN** each placeholder panel SHALL display "No data" without errors
- **AND** each panel's description SHALL explain what the metric will
  track once upstream data collection is implemented

### Requirement: Pilot dashboard metadata

The pilot dashboard SHALL use:

- UID: `opencode-pilot-dashboard`
- Title: `OpenCode Pilot`
- Tags: `["opencode", "pilot"]`
- Auto-refresh: `30s`
- Default time range: from `ai_grafana_pilot_start_date` to `now`
- Timezone: `browser`

The UID and title SHALL differ from the operational dashboard to avoid
conflicts when both dashboards are deployed simultaneously.

#### Scenario: Both dashboards coexist in Grafana

- **GIVEN** both `opencode-metrics.json` and the pilot dashboard JSON
  are present in the dashboards directory
- **WHEN** the Grafana container starts
- **THEN** both dashboards SHALL appear in the Grafana dashboard list
- **AND** each SHALL have a distinct title and UID

### Requirement: Monday-Sunday week alignment

All weekly aggregations in the pilot dashboard SHALL use a Monday-Sunday
reporting period. Weekly cost panels SHALL group data using SQLite's
`strftime('%W')` function (which counts weeks starting from Monday) and
the "Active This Week" equivalent SHALL use
`date('now', 'weekday 1', '-7 days')` to compute the current week's
Monday boundary.

#### Scenario: Weekly cost aligns to Monday-Sunday

- **GIVEN** the opencode-metrics database contains sessions spanning
  a Saturday-to-Tuesday period
- **WHEN** the user views the weekly cost panel
- **THEN** the Saturday and Sunday sessions SHALL be attributed to the
  week ending on that Sunday
- **AND** the Monday and Tuesday sessions SHALL be attributed to the
  following week
