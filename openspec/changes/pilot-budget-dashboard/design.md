# Design

## Context

See proposal.md for motivation. The existing Grafana metrics stack consists of:

- A single dashboard template (`opencode_metrics_dashboard.json.j2`) with
  approximately 50 panels organized around a **monthly recurring budget**
  derived from `ai_grafana_metrics_monthly_budget`.
- A SQLite datasource (`frser-sqlite-datasource`) reading from a single-user
  local database at `~/.local/share/opencode-metrics/metrics.db`.
- A dashboard provider (`files/grafana/provisioning/dashboards/provider.yaml`)
  that auto-discovers all JSON files under `/var/lib/grafana/dashboards/`,
  so a second dashboard file requires no provisioning changes.
- A deployment task (`tasks/configure_grafana_metrics.yml`) that templates
  the dashboard and deploys provisioning files into
  `~/.config/opencode/grafana/`.

The pilot has a **fixed total budget** (e.g., $500 working / $1,000 review)
over a **defined time window** scoped to **named repositories**, which is
fundamentally different from the existing monthly-budget model.

## Goals / Non-Goals

**Goals:**

- Provide a self-contained pilot governance dashboard that can be deployed
  alongside the operational dashboard without modifying it.
- Support fixed-duration budget tracking with pilot-specific thresholds and
  date-range scoping.
- Surface repository-scoped cost attribution for the approved repositories.
- Include structurally complete rows for data quality and evidence status,
  even where upstream data sources do not yet exist.
- Make deployment conditional so the pilot dashboard only appears when pilot
  variables are defined.

**Non-Goals:**

- Modifying the existing operational dashboard.
- Implementing upstream data collection for controls/governance metrics
  (blocked prompts, hard stops, reconciliation failures). Placeholder
  panels are acceptable.
- Implementing GCP billing reconciliation or a reconciliation pipeline.
  The dashboard will clearly label all values as OpenCode local estimates.
- Building a push-notification or alerting system. Visual thresholds in
  the dashboard are sufficient; Grafana alerting rules are out of scope.
- Replacing the written weekly report. The dashboard complements the report
  by providing real-time data; narrative items (outcomes, blockers, status)
  remain in the written report.

## Decisions

### Decision 1: Separate template, not a mode switch in the existing one

**Choice**: Create `opencode_pilot_dashboard.json.j2` as a new file.

**Alternatives considered**:
- **Grafana template variables** to switch between monthly and pilot mode
  within one dashboard. Rejected because the panel sets are substantially
  different (pilot needs repo-scoped attribution, pilot-to-date budget
  gauge, evidence status row) and interleaving both modes increases
  complexity without benefiting either audience.
- **Conditional Jinja blocks** within the existing template to inject pilot
  panels. Rejected for the same complexity reason and because it couples
  two independent lifecycles -- the pilot dashboard has a 60-day lifespan
  while the operational dashboard is evergreen.

**Rationale**: Two templates have independent lifecycles, can be reviewed
and tested separately, and do not risk regressions in the existing
dashboard. The Grafana dashboard provider auto-discovers both files.

### Decision 2: Pilot variables with safe defaults

**Choice**: New variables in `defaults/main.yml`:

```yaml
# Pilot budget dashboard (disabled by default)
# Define these variables to deploy the pilot governance dashboard
# alongside the operational metrics dashboard.
ai_grafana_pilot_budget: 0
ai_grafana_pilot_review_threshold: 0
ai_grafana_pilot_start_date: ""
ai_grafana_pilot_end_date: ""
ai_grafana_pilot_repos: []
```

When `ai_grafana_pilot_repos` is empty or `ai_grafana_pilot_start_date`
is empty, the deployment task skips the pilot dashboard template entirely.

**Alternatives considered**:
- A single boolean `ai_grafana_pilot_enabled`. Rejected because the pilot
  parameters themselves are sufficient to determine enablement (empty list
  and empty date = not configured). An extra boolean adds a redundant knob.
- Embedding pilot parameters inside `ai_opencode_metrics_config`. Rejected
  because the pilot dashboard is a Grafana artifact, not a metrics plugin
  configuration concern.

**Rationale**: Safe defaults (zero budget, empty date, empty repo list)
mean the pilot dashboard is never deployed unless explicitly configured.
No new task file is needed -- a conditional block in
`configure_grafana_metrics.yml` handles it.

### Decision 3: Pilot-to-date scoping via date-filtered queries

**Choice**: All pilot dashboard queries include a
`WHERE recorded_at_epoch >= <pilot_start_epoch> AND recorded_at_epoch <= <pilot_end_epoch>`
clause, computed from `ai_grafana_pilot_start_date` and
`ai_grafana_pilot_end_date` at template render time using Jinja epoch
conversion.

**Alternatives considered**:
- Using Grafana's time picker as the sole date range mechanism. Rejected
  because users could accidentally change the time range, breaking the
  pilot-to-date budget comparison. The pilot dates should be baked into
  the queries as constants.
- Adding a Grafana template variable for start/end dates. Rejected for
  the same reason -- pilot dates are fixed, not user-adjustable.

**Rationale**: Baked-in date constants ensure the pilot dashboard always
shows the correct pilot window regardless of the Grafana time picker
state. The time picker can still be used to zoom into sub-ranges, but
the budget KPIs always reflect the full pilot window.

### Decision 4: Approved-repo filtering via SQL IN clause

**Choice**: Jinja renders `ai_grafana_pilot_repos` into a SQL `IN (...)`
clause used by all repository-scoped panels. An additional
"Excluded/Unattributed Activity" stat panel shows the cost of sessions
NOT matching any approved repo.

**Alternatives considered**:
- Grafana template variable with a multi-select dropdown. Rejected because
  the approved repos are fixed by the pilot agreement, not user-selectable.
  Baking them into the queries prevents accidental scope changes.

**Rationale**: The pilot scope is contractual. Hardcoding the repo list
in queries ensures the dashboard always reflects the agreed scope.

### Decision 5: Evidence status via text panel and data-freshness stat

**Choice**: A "Data Quality & Evidence" row containing:
- A text panel with a static disclaimer: all values are OpenCode local
  estimates, not GCP-reconciled billing.
- A "Last Data Point" stat panel showing the most recent
  `recorded_at_epoch` in the database.
- Placeholder stat panels (showing "No data") for controls metrics
  (blocked prompts, unmatched sessions, missing metadata) that can be
  activated when upstream data sources become available.

**Alternatives considered**:
- Omitting the evidence row entirely until reconciliation is implemented.
  Rejected because the weekly reporting requirements explicitly call for
  evidence labeling, and having the structural placeholder communicates
  the intent even before the data exists.

**Rationale**: Placeholder panels with clear descriptions document the
reporting intent and make it trivial to activate controls metrics later
by changing only the SQL query when the data becomes available.

### Decision 6: Dashboard row structure

**Choice**: Six rows organized around the weekly report sections:

| Row | Title | Expanded |
|-----|-------|----------|
| 1 | Pilot Budget | Yes (always visible) |
| 2 | Repository Attribution | Collapsed |
| 3 | Work Output | Collapsed |
| 4 | Session Breakdown | Collapsed |
| 5 | Model & Token Detail | Collapsed |
| 6 | Data Quality & Evidence | Collapsed |

**Rationale**: Maps directly to the weekly report structure (spend,
per-repo attribution, work completed, session accounting, model
breakdown, evidence status). The budget row is permanently expanded
because the primary use case is a quick glance at budget burn.

## Risks / Trade-offs

- **[Risk] Pilot dates become stale after the pilot ends.** If the pilot
  dashboard is not removed after 60 days, queries continue to filter by
  the old date range, showing static data. Mitigation: document in the
  README that the pilot dashboard should be disabled (clear
  `ai_grafana_pilot_repos`) after the pilot concludes, or the template
  can be removed entirely.

- **[Risk] Project names in SQLite may not match repo names exactly.**
  The metrics plugin records project names from the working directory,
  which may differ from the repository name (e.g., directory name vs
  GitHub repo name). Mitigation: document the mapping requirement;
  users must ensure `ai_grafana_pilot_repos` values match the `name`
  column in the `projects` table.

- **[Risk] Controls/governance panels show "No data" indefinitely.**
  The upstream data sources (guardrail events, reconciliation status)
  do not exist yet. Mitigation: panels are clearly described as
  placeholders. The row can be collapsed by default so it does not
  distract from the functional panels.

- **[Trade-off] Baked-in dates prevent ad-hoc date range exploration.**
  Budget KPIs always show the full pilot window. Users who want to see
  a specific week must use the Grafana time picker, which affects the
  time-series panels but not the budget stat panels. This is intentional
  -- the budget stats should always reflect the full pilot.

## Open Questions

- What are the exact names of the five approved repositories as they
  appear in the `projects` table of the metrics SQLite database? This
  must be verified before deployment to ensure the SQL `IN` clause
  matches correctly.
