## Why

The opencode-metrics plugin (Schema V4) now stores `parent_session_id`
in the sessions table, enabling parent-child session linking for
sub-agent cost analysis. OpenCode's Task tool spawns sub-agent sessions
that each carry their own cost, but the Grafana dashboard has no panels
to visualize this relationship. Engineers cannot see the total cost of
an orchestrated task (parent + sub-agents), identify which sub-agent
types are the most expensive, or compare a session's own cost against
its fully-loaded cost.

Additionally, the dashboard has grown organically from 9 to 44 panels
across 9 rows without a coherent information hierarchy. Panels are
organized by data type (cost, tokens, sessions) rather than by the
questions an engineer asks during their daily cost review. The most
actionable panel -- "Top Sessions by Cost" -- is buried in row 7. KPI
stats mix budget awareness with unrelated metrics like cache hit ratio
and output token counts. Monthly and yearly trend panels are missing,
making budget predictability difficult when budgets reset monthly.

## What Changes

### Dashboard restructuring (8 question-based rows)

Reorganize all existing panels into 8 rows titled as the question
they answer, following the engineer's daily decision workflow:

1. **"How much have I spent?"** (always expanded) -- Budget-focused
   KPIs (Today, Week, Month, Year, Total Cost) plus Daily Cost
   timeseries and 7-Day Rolling Average. Moved from old rows 1, 2,
   and 8.
2. **"Where is the money going?"** (collapsed) -- Cost distribution
   by classification, model, project, avg cost by classification,
   active projects. Add daily cost split by root vs sub-agent.
3. **"Which sessions are the most expensive?"** (collapsed) -- Top
   Sessions table augmented with own cost, total cost, and sub-agent
   cost columns. Add most expensive sub-agents table with parent
   context.
4. **"Are there sub-agent cost patterns?"** (collapsed) -- Cost per
   sub-agent type and invocation count per sub-agent type bar charts.
5. **"What does my session activity look like?"** (collapsed) --
   Session analytics panels plus Total Sessions and Avg Session Cost
   stats moved from old row 1.
6. **"How efficient is my token usage?"** (collapsed) -- Merges old
   Token Efficiency and Efficiency rows. Cache Hit % and Output
   Tokens (M) stats moved from old row 1.
7. **"What am I getting for the money?"** (collapsed) -- Merges old
   Code Impact and PR & Issue Analytics rows. All existing panels
   unchanged.
8. **"What are the longer-term trends?"** (collapsed) -- Weekly
   Cost Trend (existing) plus new Monthly Cost Trend and Yearly
   Cost Trend panels.

### New panels (6 total)

- **Daily Cost: Root vs Sub-Agent** (stacked timeseries, Row 2) --
  Uses `v_measurement_deltas` joined with `sessions` to split daily
  cost by `parent_session_id IS NULL` (root) vs `IS NOT NULL`
  (sub-agent).
- **Most Expensive Sub-Agents** (table, Row 3) -- Top 20 sub-agent
  sessions with parent session context (title, agent, model, cost).
- **Cost per Sub-Agent Type** (horizontal bar, Row 4) -- Aggregates
  cost across all sub-agent sessions grouped by agent name.
- **Invocations per Sub-Agent Type** (horizontal bar, Row 4) --
  Count of distinct sub-agent sessions grouped by agent name.
- **Monthly Cost Trend** (timeseries, Row 8) -- Total cost per
  calendar month for budget-reset tracking.
- **Yearly Cost Trend** (timeseries, Row 8) -- Total cost per
  calendar year for long-term forecasting.

### Modified panel (1)

- **Top Sessions by Cost** (table, Row 3) -- Augmented with
  recursive CTE to show own cost, total cost (including all
  sub-agents), and sub-agent cost overhead per root session.

### Panel movements (7)

- Daily Cost timeseries: Row 2 -> Row 1
- 7-Day Rolling Average: Row 8 -> Row 1
- Total Sessions stat: Row 1 -> Row 5
- Avg Session Cost stat: Row 1 -> Row 5
- Cache Hit % stat: Row 1 -> Row 6
- Output Tokens (M) stat: Row 1 -> Row 6
- Active Projects stat: Row 1 -> Row 2

### Row merges (2)

- Token Efficiency + Efficiency -> Row 6
- Code Impact + PR & Issue Analytics -> Row 7

### Style preservation

All existing panels retain their current `fieldConfig`, `options`,
color overrides, thresholds, gradient modes, and fill opacities. New
panels adopt the closest existing panel's style conventions.

## Capabilities

### New Capabilities

(none -- all changes are within the existing `grafana-metrics`
capability)

### Modified Capabilities

- `grafana-metrics`: Dashboard restructured from 9 rows to 8
  question-based rows, panel count increases from 44 to 50, existing
  KPI stat panels redistributed to their natural row contexts, Top
  Sessions table augmented with sub-agent cost columns, 6 new panels
  added for sub-agent analytics and budget trends. Row titles changed
  to question format. Monthly and yearly trend panels added.

## Impact

- **Files modified**: `templates/opencode_metrics_dashboard.json.j2`
  (full restructure of panels array and row organization)
- **Spec modified**: `openspec/specs/grafana-metrics/spec.md`
  (updated to reflect new 8-row question-based structure, new panels,
  and sub-agent analytics scenarios)
- **Files unchanged**: `tasks/configure_grafana_metrics.yml`,
  `templates/opencode_grafana.sh.j2`, `files/grafana/provisioning/*`,
  `defaults/main.yml`
- **Backward compatibility**: Full. Dashboard UID and datasource UID
  preserved. Sub-agent panels query `parent_session_id` which exists
  in Schema V4. For databases still on Schema V3 (column absent),
  sub-agent panels will show "No data" without errors -- standard
  Grafana behavior for queries referencing missing columns.
- **Dependencies**: Requires opencode-metrics plugin with Schema V4
  (`parent_session_id` column in sessions table). No new Grafana
  plugins or data sources needed.
- **Breaking changes**: None. No panels are removed. Existing
  dashboard bookmarks continue to work.
