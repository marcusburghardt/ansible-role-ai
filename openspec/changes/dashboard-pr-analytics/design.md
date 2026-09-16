## Context

The Grafana dashboard template at
`templates/opencode_metrics_dashboard.json.j2` defines all panels
as JSON objects within a Jinja2 template. The template uses
variables from `ai_grafana_metrics_monthly_budget` to compute
threshold colors. The dashboard uses the `frser-sqlite-datasource`
plugin to query the opencode-metrics SQLite database directly.

The dashboard currently has 8 collapsible rows (Key Metrics, Cost
Overview, Token Efficiency, Session Analytics, Efficiency, Code
Impact, Top Sessions, Trends). Adding PR & Issue Analytics as row 9
follows the established pattern.

## Goals / Non-Goals

### Goals

- Add a "PR & Issue Analytics" row to the Grafana dashboard
- Show KPI stats for PR activity (total PRs, cost per PR)
- Show trends over time (PR creation rate, cost per PR trend)
- Show drill-down analytics (most expensive PRs, PR distribution)
- Maintain backward compatibility with older plugin versions

### Non-Goals

- Modifying existing dashboard panels or rows
- Adding alerting rules for PR activity
- Adding Grafana variables or template variables for PR filtering
- Real-time PR status tracking (open/merged/closed)

## Decisions

### Decision 1: Row placement

**Choice**: Place the "PR & Issue Analytics" row as row 9 (after
Trends, before any future rows). Collapsed by default, matching the
existing pattern for detail rows.

**Rationale**: Follows the established dashboard structure. PR
analytics is a new dimension that complements but doesn't replace
existing cost/token/session analytics.

### Decision 2: Graceful degradation for missing tables

**Choice**: Use standard SQL queries against `session_artifacts`
and `v_session_artifacts`. If the tables don't exist (older plugin),
Grafana's frser-sqlite-datasource returns an error that renders as
"No data" in panels. No special handling needed.

**Rationale**: The dashboard template is deployed independently of
the plugin. Users who haven't upgraded the plugin will see empty
panels, which is self-documenting (upgrade the plugin to see data).
Adding `CREATE TABLE IF NOT EXISTS` or error-handling SQL would add
complexity for a transient state.

### Decision 3: Query patterns

**Choice**: Use the same query patterns as existing panels:
- KPI stats: `SELECT SUM/AVG/COUNT FROM v_measurements WHERE ...`
- Time series: `SELECT date(...) as time, SUM(...) FROM
  v_measurement_deltas WHERE ... GROUP BY 1`
- Tables: `SELECT ... FROM v_session_artifacts JOIN v_measurements
  ... ORDER BY ... LIMIT N`

**Rationale**: Consistency with existing panels. The
frser-sqlite-datasource plugin handles these patterns reliably.
Using `v_measurement_deltas` for time series ensures accurate
daily aggregation for multi-day sessions.

### Decision 4: Color scheme

**Choice**: Use a distinct color palette for the PR row to
differentiate it from existing sections. Suggested: coral/salmon
tones for PR-created, teal for PR-reviewed, amber for issues.

**Rationale**: The existing dashboard uses section-specific colors
(green for cost, blue for tokens, purple for sessions). A distinct
palette for PRs maintains visual clarity.

## Risks / Trade-offs

- **Panel count**: Adding ~10 panels increases the dashboard JSON
  size and initial load time. Mitigated by keeping the row collapsed
  by default.
- **Data availability**: PR data requires the opencode-metrics
  plugin with the pr-issue-tracking change AND a backfill run.
  Users who don't upgrade will see empty panels. This is acceptable
  and self-documenting.
- **Dashboard version**: The dashboard JSON template is versioned
  via git. Existing deployed dashboards need to be re-provisioned
  (re-run the Ansible role or `make grafana-provision`) to pick up
  the new panels.
