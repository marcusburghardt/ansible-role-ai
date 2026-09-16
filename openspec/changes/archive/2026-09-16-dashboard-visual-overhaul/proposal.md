## Why

The initial Grafana dashboard shipped with the `configure_grafana_metrics`
task has three functional bugs and lacks visual polish. Pie charts render
as a single slice (wrong reduceOptions), time-series panels show no data
(date() output is not RFC3339-compatible), and project bar charts are
unreadable with 29+ entries. The dashboard also has no auto-refresh, no
color coding by section, and no KPI summary row -- making it a raw data
dump rather than an at-a-glance analytics tool.

## What Changes

- Fix pie chart panels: switch `reduceOptions` to `values: true` so
  each row renders as a separate slice instead of collapsing to one sum
- Fix time-series panels: return `MIN(recorded_at)/1000` as the time
  column (epoch seconds) instead of `date()` strings that fail RFC3339
  parsing in the frser-sqlite-datasource plugin
- Fix project bar charts: limit to top 10 entries plus an "Other"
  aggregate bucket to prevent chart overcrowding
- Add auto-refresh (30s interval) and `liveNow` indicator so the
  dashboard reflects new sessions without manual reload
- Expand from 9 panels to ~30 panels organized in 8 collapsible rows:
  KPIs (always visible), Cost Overview, Token Efficiency, Session
  Analytics, Efficiency Metrics, Code Impact, Top Sessions, Trends
- Add 6 stat KPI panels at the top: Total Sessions, Total Cost, Avg
  Session Cost, Cache Hit %, Output Tokens (M), Active Projects
- Add new analytical panels: Cost per 1K Output Tokens, Cache Hit by
  Classification, Token Distribution pie, Sessions by Agent Type,
  Sessions by Classification Over Time (stacked), Duration Distribution
  (bucketed bar chart), Avg Duration by Classification, Messages per
  Classification, Weekly Cost Trend, 7-Day Rolling Average Cost, Lines
  Changed Over Time, Files Changed by Project, Cost per File Changed
- Apply section-specific color palettes: green/amber for cost,
  blue/cyan for tokens, purple for sessions, orange for efficiency,
  teal for code impact, yellow/gold for trends
- Use gradient fills, explicit series color overrides, and threshold
  color steps for a polished dark-theme appearance
- Set all detail rows (rows 2-8) to collapsed by default, keeping only
  the KPI row expanded for a clean initial view

## Capabilities

### New Capabilities

None. This change improves the existing dashboard artifact within the
`grafana-metrics` capability.

### Modified Capabilities

- `grafana-metrics`: Dashboard panel count increases from 9 to ~30,
  organized in collapsible rows with bug fixes, auto-refresh, color
  theming, and new analytical panels. Helper script and provisioning
  file structure are unchanged.

## Impact

- **Files modified**: `files/grafana/dashboards/opencode-metrics.json`
  (complete rewrite of the panels array)
- **Files unchanged**: `tasks/configure_grafana_metrics.yml`,
  `templates/opencode_grafana.sh.j2`, `files/grafana/provisioning/*`,
  `defaults/main.yml`, `vars/configure_grafana_metrics.yml`
- **Backward compatibility**: Full. The dashboard UID and datasource UID
  are preserved. Users with an existing named volume will see the new
  dashboard on next container restart (provisioned dashboards are
  reloaded by Grafana on file change).
- **Dependencies**: No new dependencies. Same Grafana container image,
  same frser-sqlite-datasource plugin.
- **Breaking changes**: None.
