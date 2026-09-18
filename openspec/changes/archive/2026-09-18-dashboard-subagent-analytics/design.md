## Context

The dashboard template (`templates/opencode_metrics_dashboard.json.j2`)
is a single Jinja2 file producing a Grafana JSON model. It currently
has 44 panels in 9 rows. The opencode-metrics plugin Schema V4 added
`parent_session_id` to the `sessions` table and documented 5 SQL
query templates in `GRAFANA_MIGRATION.md` for sub-agent cost analysis.
See proposal.md for motivation.

The Grafana instance uses the `frser-sqlite-datasource` plugin which
supports standard SQLite SQL including `WITH RECURSIVE` CTEs. All
queries run against a local SQLite database mounted read-only into
the container.

## Goals / Non-Goals

### Goals
- Restructure the dashboard into 8 question-based rows that follow
  the engineer's daily cost-review workflow.
- Add 6 new panels for sub-agent cost analysis and budget trends.
- Augment the Top Sessions table with own/total/sub-agent cost
  columns using a recursive CTE.
- Preserve all existing panel styles (colors, thresholds, gradients,
  fill opacities, overrides).
- Maintain backward compatibility with Schema V3 databases (sub-agent
  panels show "No data" without breaking other panels).

### Non-Goals
- Adding Grafana template variables for drill-down (e.g., session_id
  picker). Engineers who need per-session investigation will use
  SQLite CLI directly.
- Changing the Grafana container configuration, datasource setup, or
  helper script.
- Adding new Jinja2 variables beyond the existing budget thresholds.
- Modifying any panel's visual style (colors, gradients, fill
  opacities) unless the panel is being moved to a new row context
  where the color accent must match.

## Decisions

### D1: Question-based row titles

**Decision**: Use plain-language questions as row titles (e.g.,
"How much have I spent?" instead of "Key Metrics").

**Rationale**: Row titles are the primary navigation element in a
collapsed dashboard. Questions make the dashboard self-documenting --
an engineer scanning collapsed rows immediately knows what information
each section provides. This aligns with the dashboard's purpose as a
daily decision-support tool, not a data catalog.

**Alternative considered**: Descriptive labels (e.g., "Budget Pulse",
"Cost Distribution"). Rejected because they require the user to infer
what question each section answers.

### D2: Daily Cost and Rolling Average in Row 1

**Decision**: Move the Daily Cost timeseries (from old Cost Overview)
and the 7-Day Rolling Average (from old Trends) into Row 1 alongside
the budget KPI stats.

**Rationale**: Row 1 answers "How much have I spent?" -- the daily
cost trend and rolling average are direct answers to this question.
Placing them next to the KPI stats creates a complete budget pulse
view: current spend (stats) + recent trajectory (timeseries). In the
old layout, the Daily Cost panel was hidden in a collapsed row while
the Rolling Average was buried in row 8.

**Trade-off**: Row 1 becomes taller (stats + 2 timeseries). Accepted
because Row 1 is the always-expanded row and engineers start every
session here.

### D3: Recursive CTE for Top Sessions table

**Decision**: Augment the existing Top Sessions query with a
`WITH RECURSIVE` CTE to compute `own_cost`, `total_cost` (recursive
sum), and `subagent_cost` (total - own) for each root session.

**Rationale**: This is the pivot point in the engineer's workflow --
seeing a session with high `subagent_cost` triggers investigation
into Row 3's "Most Expensive Sub-Agents" table. The CTE walks the
parent-child tree per root session and aggregates cost across all
descendants.

**Query approach**: Use query 4 from the opencode-metrics
`GRAFANA_MIGRATION.md` ("Own cost vs fully-loaded cost per root
session") adapted to the dashboard's existing table column
conventions.

**Performance note**: SQLite recursive CTEs are efficient for the
expected dataset size (thousands of sessions). The `idx_sessions_parent`
index on `parent_session_id` ensures each recursion level uses an
index lookup.

### D4: Sub-agent panels use cumulative metrics, daily split uses deltas

**Decision**: The "Cost per Sub-Agent Type" and "Most Expensive
Sub-Agents" panels query `measurements` (cumulative totals). The
"Daily Cost: Root vs Sub-Agent" panel queries `v_measurement_deltas`
(incremental changes).

**Rationale**: Follows the same principle established in the
`GRAFANA_MIGRATION.md`: cumulative totals are correct for aggregate
breakdowns (by type, by session), while deltas are required for
time-series panels to accurately attribute cost to the day it was
incurred.

### D5: Merge Token Efficiency + Efficiency into one row

**Decision**: Combine the old "Token Efficiency" row (3 panels) and
"Efficiency" row (3 panels) into a single row titled "How efficient
is my token usage?". Move Cache Hit % and Output Tokens (M) stat
panels from old Row 1 into this merged row.

**Rationale**: Both old rows answer the same question about
efficiency. Separating them created a false distinction between
"token metrics" and "derived efficiency metrics." The merged row
has 8 panels -- a manageable density.

### D6: Merge Code Impact + PR Analytics into one row

**Decision**: Combine the old "Code Impact" row (2 panels) and
"PR & Issue Analytics" row (11 panels) into a single row titled
"What am I getting for the money?".

**Rationale**: Both rows answer questions about outcomes and
deliverables. Code impact (lines/files changed) and PR metrics
(PRs created, cost per PR) are complementary views of engineering
output. A 2-panel row was too thin to justify its own section.

### D7: Monthly and Yearly Trend panels use delta-based aggregation

**Decision**: New Monthly Cost Trend and Yearly Cost Trend panels
query `v_measurement_deltas` with `SUM(delta)` grouped by
`strftime('%Y-%m', ...)` and `strftime('%Y', ...)` respectively.

**Rationale**: Same principle as D4 -- multi-day sessions must have
their cost attributed to the period the work actually occurred, not
the period of the last idle event. Delta-based aggregation ensures
monthly totals accurately reflect the budget period.

### D8: Panel ID allocation for new panels

**Decision**: Allocate IDs in the 90-99 range for new panels to
avoid conflicts with existing IDs (1-89, 100-108).

**Rationale**: Existing panels use IDs 1-89 for content panels and
100-108 for row panels. The 90-99 range is unused and provides
room for all 6 new panels. Row panels keep their existing IDs but
are renumbered sequentially (100-107) to reflect the new 8-row
structure.

### D9: Preserve existing panel styles during reorganization

**Decision**: When moving a panel to a different row, preserve its
existing `fieldConfig`, `options`, and `overrides` exactly as-is.
Do not change colors to match the destination row's accent unless
the panel's current color is semantically wrong in the new context.

**Rationale**: The user explicitly requested that formatting
decisions be preserved. Changing colors during a reorganization
risks introducing visual regressions and makes the diff harder to
review.

## Risks / Trade-offs

### Risk: Schema V3 query errors on sub-agent panels

Sub-agent panels reference `parent_session_id` which does not exist
in Schema V3 databases. SQLite returns an error for queries
referencing non-existent columns.

**Mitigation**: The frser-sqlite-datasource plugin handles SQL errors
by displaying "No data" in the panel. This is the same behavior seen
when PR analytics panels query tables that don't exist on older
plugin versions. No special error handling needed.

### Risk: Recursive CTE performance on large databases

The Top Sessions table uses a recursive CTE that walks the entire
session tree. For databases with tens of thousands of sessions, this
could be slow.

**Mitigation**: The `idx_sessions_parent` index ensures each
recursion level uses an index lookup rather than a full table scan.
The query is limited to the top 20 sessions by cost, and the CTE
only walks descendants of root sessions. At current dataset sizes
(thousands of sessions), this is a non-issue.

### Trade-off: Row 1 density

Moving Daily Cost and 7-Day Rolling Average into Row 1 makes it
taller (5 stats + 2 timeseries = ~20 grid units). This is accepted
because Row 1 is always expanded and serves as the primary landing
view. The alternative (keeping timeseries in collapsed rows) would
force engineers to expand rows for the most basic cost check.

### Trade-off: Row 7 density

Merging Code Impact (2 panels) and PR Analytics (11 panels) creates
a 13-panel row. This is the densest row in the dashboard but is
collapsed by default. Engineers who expand it are specifically looking
for outcome metrics and will benefit from seeing code and PR data
together.
