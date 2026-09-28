# Proposal

## Why

The existing Grafana dashboard (`opencode_metrics_dashboard.json.j2`) is designed
for ongoing personal operational monitoring with a monthly recurring budget model.
A separate 60-day AI pilot requires a governance-focused dashboard with fixed
total-budget thresholds (e.g., $500 working / $1,000 review), scoped to approved
repositories, and aligned with weekly reporting requirements that include spend
tracking, work-output attribution, session accounting, data-quality indicators,
and evidence-status labeling. Merging pilot-specific panels into the existing
dashboard would clutter it for non-pilot users and introduce conflicting budget
semantics.

## What Changes

- Add a new Grafana dashboard template (`opencode_pilot_dashboard.json.j2`)
  purpose-built for pilot budget tracking and weekly reporting, deployed
  alongside the existing operational dashboard.
- Add new Ansible variables to configure pilot parameters: total budget,
  review threshold, start/end dates, and approved repository list.
- Add a conditional deployment task that only provisions the pilot dashboard
  when pilot variables are defined.
- Add a "Data Quality & Evidence" row to surface data freshness, estimate vs
  reconciled value labeling, and placeholders for controls/governance metrics
  once upstream data sources become available.

## Capabilities

### New Capabilities

- `pilot-budget-dashboard`: A second Grafana dashboard template and associated
  Ansible variables for pilot-scoped budget tracking, weekly reporting, repository
  attribution, work-output metrics, session accounting, data-quality indicators,
  and evidence-status labeling. Includes conditional deployment so it is only
  provisioned when pilot parameters are defined.

### Modified Capabilities

- `grafana-metrics`: The Grafana metrics task file
  (`tasks/configure_grafana_metrics.yml`) needs modification to conditionally
  deploy the pilot dashboard template alongside the existing operational
  dashboard when pilot variables are defined.

## Impact

- **Templates**: New file `templates/opencode_pilot_dashboard.json.j2`.
- **Defaults**: New variables in `defaults/main.yml` for pilot budget, dates,
  and approved repos (all with safe defaults that result in no deployment when
  unconfigured).
- **Tasks**: `tasks/configure_grafana_metrics.yml` gains a conditional task to
  template and deploy the pilot dashboard.
- **Grafana provisioning**: The existing dashboard provider
  (`files/grafana/provisioning/dashboards/provider.yaml`) already scans a
  directory, so a second JSON file will be auto-discovered without changes.
- **Existing dashboard**: No changes to `opencode_metrics_dashboard.json.j2`.
- **Data model**: No changes to the SQLite schema or metrics plugin. The pilot
  dashboard queries the same `sessions`, `measurements`, `v_measurements`,
  `v_measurement_deltas`, `v_sessions`, `v_session_artifacts`, and `projects`
  tables/views already populated by the metrics plugin.
- **Controls/governance panels**: Panels for blocked prompts, hard stops,
  unmatched sessions, missing metadata, reconciliation failures, and
  unauthorized activity will be structurally present in the dashboard as
  placeholder panels. They will display "No data" until upstream data
  collection is implemented in the metrics plugin or a guardrail system.
  This proposal does not include implementing those upstream data sources.
