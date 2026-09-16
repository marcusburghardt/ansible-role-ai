## 1. Rebuild Dashboard JSON

- [x] 1.1 Rewrite `files/grafana/dashboards/opencode-metrics.json` with
  the full 8-row, ~30-panel layout. Set `"refresh": "30s"` and
  `"liveNow": true` at the dashboard level. Set `"version": 2`.
  Verify: JSON is valid (`python3 -m json.tool < file`).

- [x] 1.2 Add KPI row (row 1, collapsed: false) with 6 stat panels:
  Total Sessions, Total Cost, Avg Session Cost, Cache Hit %, Output
  Tokens (M), Active Projects. Apply per-KPI threshold colors. Verify:
  panel count is 6, all use `"type": "stat"`.

- [x] 1.3 Add Cost Overview row (row 2, collapsed: true) with 5 panels:
  Daily Cost (timeseries), Cost by Classification (piechart), Cost by
  Model (barchart), Cost by Project (barchart), Avg Cost per Session
  by Classification (barchart). Use green/amber color overrides
  (`#73BF69`). Verify: Daily Cost uses `MIN(recorded_at)/1000` as
  time column; pie chart uses `reduceOptions.values: true`; Cost by
  Project uses Top 10 + "Other" UNION query.

- [x] 1.4 Add Token Efficiency row (row 3, collapsed: true) with 3
  panels: Token Usage Over Time (timeseries), Token Distribution
  (piechart), Cache Hit Ratio Over Time (timeseries). Use blue/cyan
  color overrides (`#5794F2`). Verify: Token Usage uses multi-series
  via `metric_name` column; pie chart uses `reduceOptions.values: true`.

- [x] 1.5 Add Session Analytics row (row 4, collapsed: true) with 6
  panels: Sessions by Day (timeseries), Sessions by Classification
  Over Time (timeseries, stacked), Duration Distribution (barchart
  with bucketed CASE query), Sessions by Agent Type (piechart), Avg
  Duration by Classification (barchart), Messages per Classification
  (barchart). Use purple color overrides (`#B877D9`). Verify: Duration
  Distribution uses CASE WHEN buckets; pie chart uses
  `reduceOptions.values: true`.

- [x] 1.6 Add Efficiency row (row 5, collapsed: true) with 3 panels:
  Cost per 1K Output Tokens (stat), Cache Hit by Classification
  (barchart), Cost per File Changed (stat). Use orange color overrides
  (`#FF9830`). Verify: stat panels use NULLIF to avoid division by zero.

- [x] 1.7 Add Code Impact row (row 6, collapsed: true) with 2 panels:
  Lines Changed Over Time (timeseries, stacked), Files Changed by
  Project (barchart). Use teal color overrides (`#36A2EB`). Verify:
  Lines Changed uses multi-series via `metric_name` column; Files
  by Project uses Top 10 + "Other" UNION query.

- [x] 1.8 Add Top Sessions row (row 7, collapsed: true) with 1 panel:
  Top Sessions by Cost (table, full width). Columns: title,
  classification, model, agent, project, cost, date. Verify: query
  JOINs sessions, measurements, and projects tables; LIMIT 20.

- [x] 1.9 Add Trends row (row 8, collapsed: true) with 2 panels:
  Weekly Cost Trend (timeseries), 7-Day Rolling Average Cost
  (timeseries). Use yellow/gold color overrides (`#FADE2A`). Verify:
  Rolling Average uses OVER() window function; Weekly Cost uses
  strftime for week grouping.

## 2. Update Spec

- [x] 2.1 Update `openspec/specs/grafana-metrics/spec.md` to reflect
  the new panel count (~30), row structure, auto-refresh, and bug fixes.
  Verify: spec mentions approximately 30 panels, 8 rows, auto-refresh,
  and collapsed-by-default behavior.

## 3. Verification

- [x] 3.1 Run `python3 -m json.tool` on the dashboard JSON to verify
  it is syntactically valid. Verify: exit code 0.

- [x] 3.2 Run `yamllint .` and `ansible-lint` to verify no regressions
  in the role. Verify: no new errors.

- [x] 3.3 Redeploy via playbook (only `configure_grafana_metrics` task),
  restart Grafana (`opencode-grafana stop && opencode-grafana start`),
  open http://localhost:3033 and verify: KPI row is visible, detail
  sections are collapsed, expanding Cost section shows Daily Cost with
  data, Cost by Classification shows multiple pie slices, Cost by
  Project shows top 10 + Other.
