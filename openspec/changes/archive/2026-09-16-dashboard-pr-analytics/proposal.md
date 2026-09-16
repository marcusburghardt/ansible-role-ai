## Why

The opencode-metrics plugin now tracks PR and issue activity per
session via the `session_artifacts` table and three new count metrics
(`prs_created`, `prs_reviewed`, `issues_referenced`). This data
enables cost-per-deliverable analytics -- answering "how much does
it cost to create a PR?" or "which PRs consumed the most resources?"

The Grafana dashboard currently has no panels for this data. Users
who upgrade the plugin and re-run backfill will have artifact data
in their database but no way to visualize it without writing raw
SQL queries. Adding a dedicated "PR & Issue Analytics" row to the
dashboard closes this gap and transforms the dashboard from pure
cost tracking into ROI measurement.

Evidence from a real database (933 sessions):
- 141 sessions created PRs
- 149 sessions reviewed PRs
- 95 sessions referenced issues

## What Changes

Add a new collapsible row "PR & Issue Analytics" to the Grafana
dashboard template (`opencode_metrics_dashboard.json.j2`) with
panels covering:

### KPI panels (stat type)
- **PRs Created** -- total count from `v_measurements` where
  `metric_name = 'prs_created'`
- **PRs Reviewed** -- total count from `v_measurements` where
  `metric_name = 'prs_reviewed'`
- **Avg Cost per PR** -- `SUM(cost) / SUM(prs_created)` for
  sessions with at least one PR created
- **Sessions with PRs** -- count of sessions where
  `prs_created > 0 OR prs_reviewed > 0`

### Analytical panels
- **PR Activity Over Time** (timeseries) -- daily PRs created and
  reviewed using `v_measurement_deltas`, dual Y-axis or stacked
- **Cost per PR Trend** (timeseries) -- weekly average cost per PR
  created, showing whether AI-assisted PR creation is getting
  cheaper over time
- **PR Activity by Classification** (horizontal bar) -- which
  session classifications (pr-creation, implementation, etc.)
  produce the most PRs
- **Most Expensive PRs** (table) -- top 10 PRs by total cost
  across all sessions, using `v_session_artifacts` joined with
  `v_measurements` for cost
- **PRs per Session Distribution** (bar chart) -- histogram of how
  many PRs sessions typically create (1, 2, 3+), showing batching
  efficiency
- **Non-Deliverable Spend** (stat or pie) -- percentage of total
  cost from sessions with zero PRs and zero issues, highlighting
  sessions that consumed resources without producing trackable
  deliverables

### Dashboard tables queried
- `v_measurements` -- existing: cost, tokens; new: prs_created,
  prs_reviewed, issues_referenced
- `v_measurement_deltas` -- for time-series aggregation of new
  metrics
- `v_session_artifacts` -- new: artifact detail for drill-down
  queries (most expensive PRs, sessions per PR)
- `v_sessions` -- existing: classification, project, model joins

## Capabilities

### New Capabilities

- `pr-issue-dashboard`: Grafana panels for PR/issue analytics
  including KPIs, trends, cost-per-PR, and drill-down tables.

### Modified Capabilities

- `grafana-metrics`: Dashboard gains a new collapsible row (row 9)
  with ~10 panels. Existing rows and panels are unchanged.

### Removed Capabilities

(none)

## Impact

- **Files modified**: `templates/opencode_metrics_dashboard.json.j2`
  (add new row and panels)
- **Files added**: (none)
- **Backward compatibility**: Full. The new panels query tables and
  views (`session_artifacts`, `v_session_artifacts`) that only exist
  after the opencode-metrics plugin is updated. If the tables don't
  exist (older plugin version), the panels will show "No data" --
  this is the standard Grafana behavior for missing tables and does
  not break the dashboard.
- **Dependencies**: Requires opencode-metrics plugin with PR/issue
  tracking (the `opsx/pr-issue-tracking` change). No new Grafana
  plugins or data sources needed.
- **Breaking changes**: None.
