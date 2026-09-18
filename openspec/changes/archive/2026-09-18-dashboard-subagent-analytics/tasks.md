# Tasks

<!--
  [P] marks tasks eligible for parallel execution.
  Add [P] when a task: (a) touches different files from
  other [P] tasks in the group, (b) has no dependency
  on prior tasks in the group, (c) can safely execute
  without ordering constraints.
  Do NOT add [P] when tasks modify the same file --
  parallel workers will cause merge conflicts.
  Tasks without [P] run sequentially first, then [P]
  tasks run in parallel.
-->

## 1. Row Restructuring

All tasks in this group modify
`templates/opencode_metrics_dashboard.json.j2`. They MUST run
sequentially to avoid merge conflicts.

- [x] 1.1 Rename all 9 existing row panels to question-based titles.
  Row 100 "Key Metrics" -> "How much have I spent?",
  Row 101 "Cost Overview" -> "Where is the money going?",
  Row 103 "Session Analytics" -> "What does my session activity look like?",
  Row 106 "Top Sessions" -> "Which sessions are the most expensive?".
  New rows for sub-agent patterns, merged efficiency, merged outcomes,
  and trends are created in subsequent tasks. Verify by searching the
  template for old row titles -- none SHALL remain.

- [x] 1.2 Restructure Row 1 ("How much have I spent?"). Keep the 5
  budget-focused stat panels (Today's Cost, Active This Week, Active
  This Month, Active This Year, Total Cost). Move "Total Sessions",
  "Avg Session Cost", "Cache Hit %", "Output Tokens (M)", and
  "Active Projects" stat panels out of Row 1 (they will be placed
  in tasks 1.4, 1.5, 1.3). Move the "Daily Cost" timeseries panel
  (id 10) from old Row 2 into Row 1 as a child panel. Move the
  "7-Day Rolling Average Cost" timeseries panel (id 71) from old
  Row 8 into Row 1 as a child panel. Set Row 1 `collapsed: false`.
  Update `gridPos` values so the 5 stats fill the first two visual
  rows and the two timeseries sit below them side by side. Verify
  Row 1 contains exactly 7 panels (5 stats + 2 timeseries) and
  `collapsed` is `false`.

- [x] 1.3 Restructure Row 2 ("Where is the money going?"). Keep
  existing panels: Cost by Classification (id 11), Cost by Model
  (id 12), Cost by Project (id 13), Avg Cost per Session by
  Classification (id 14). Move "Active Projects" stat (id 6) from
  old Row 1 into this row. Set Row 2 `collapsed: true`. Update
  `gridPos` values to arrange panels in the row. Verify Row 2
  contains exactly 5 existing panels and `collapsed` is `true`.

- [x] 1.4 Restructure Row 5 ("What does my session activity look
  like?"). Keep all 6 existing Session Analytics panels (ids 30-35).
  Move "Total Sessions" stat (id 1) and "Avg Session Cost" stat
  (id 3) from old Row 1 into this row as the first two panels.
  Set `collapsed: true`. Update `gridPos` values. Verify Row 5
  contains exactly 8 panels.

- [x] 1.5 Merge old "Token Efficiency" (Row 102, ids 20-22) and
  old "Efficiency" (Row 104, ids 40-42) into a single Row 6
  titled "How efficient is my token usage?". Move "Cache Hit %"
  stat (id 4) and "Output Tokens (M)" stat (id 5) from old Row 1
  into this row as the first two panels. Set `collapsed: true`.
  Verify Row 6 contains exactly 8 panels (2 moved stats +
  3 from Token Efficiency + 3 from Efficiency).

- [x] 1.6 Merge old "Code Impact" (Row 105, ids 50-51) and old
  "PR & Issue Analytics" (Row 108, ids 80-89) into a single Row 7
  titled "What am I getting for the money?". Preserve all existing
  panel styles unchanged. Set `collapsed: true`. Verify Row 7
  contains exactly 13 panels (2 + 11).

- [x] 1.7 Update Row 8 ("What are the longer-term trends?"). Remove
  the "7-Day Rolling Average Cost" panel (id 71, moved to Row 1 in
  task 1.2). Keep the "Weekly Cost Trend" panel (id 70). Set
  `collapsed: true`. Verify Row 8 contains exactly 1 existing panel
  (new panels added in group 2).

- [x] 1.8 Renumber row panel IDs sequentially (100-107) to match
  the new 8-row structure. Update all `gridPos.y` values on row
  panels so rows appear in order (y=0 through y=7 for collapsed
  rows, adjusting for Row 1's expanded height). Verify the JSON
  is valid by piping through `python3 -m json.tool` after Jinja2
  variable substitution.

## 2. New Panels

All tasks in this group modify
`templates/opencode_metrics_dashboard.json.j2`. They MUST run
sequentially after group 1 is complete.

- [x] 2.1 Add "Daily Cost: Root vs Sub-Agent" stacked timeseries
  panel to Row 2. ID: 90. Query:
  `SELECT date(d.recorded_at_epoch, 'unixepoch', 'localtime') AS day, CASE WHEN s.parent_session_id IS NULL THEN 'root' ELSE 'subagent' END AS session_type, ROUND(SUM(d.delta), 4) AS cost FROM v_measurement_deltas d JOIN sessions s ON d.session_id = s.session_id WHERE d.metric_name = 'cost' GROUP BY day, session_type ORDER BY day DESC LIMIT 28`.
  Use stacked bar style matching the existing Daily Cost panel
  (fillOpacity 40, gradientMode scheme). Apply color overrides:
  root series uses `#73BF69` (green, matching existing cost panels),
  subagent series uses `#FADE2A` (amber). Full width (w: 24).
  Verify the panel renders in Row 2 with `collapsed: true`.

- [x] 2.2 Modify the existing "Top Sessions by Cost" table (id 60)
  in Row 3 ("Which sessions are the most expensive?"). Replace the
  existing query with the recursive CTE from design decision D3:
  `WITH RECURSIVE tree(root_id, session_id) AS (SELECT session_id, session_id FROM sessions WHERE parent_session_id IS NULL UNION ALL SELECT t.root_id, s.session_id FROM sessions s JOIN tree t ON s.parent_session_id = t.session_id) SELECT r.title, r.classification, r.model, r.agent, p.name as project, ROUND(own.value, 4) as own_cost, ROUND(total.total, 4) as total_cost, ROUND(total.total - own.value, 4) as subagent_cost, r.started_at_iso as date FROM v_sessions r JOIN measurements own ON own.session_id = r.session_id AND own.metric_name = 'cost' JOIN (SELECT root_id, SUM(m.value) AS total FROM tree t JOIN measurements m ON m.session_id = t.session_id WHERE m.metric_name = 'cost' GROUP BY root_id) total ON total.root_id = r.session_id LEFT JOIN projects p ON r.project_id = p.project_id WHERE r.parent_session_id IS NULL AND own.value > 0 ORDER BY total.total DESC LIMIT 20`.
  Add field overrides for `own_cost`, `total_cost`, and
  `subagent_cost` columns with `unit: currencyUSD` and
  color-background gradient matching the existing `cost` column
  style. Verify the table panel has the new columns in the query.

- [x] 2.3 Add "Most Expensive Sub-Agents" table panel to Row 3.
  ID: 91. Query:
  `SELECT p.title AS parent_title, p.agent AS parent_agent, c.agent AS subagent_type, c.model AS subagent_model, ROUND(m.value, 4) AS subagent_cost FROM sessions c JOIN sessions p ON c.parent_session_id = p.session_id JOIN measurements m ON m.session_id = c.session_id WHERE m.metric_name = 'cost' ORDER BY m.value DESC LIMIT 20`.
  Apply field override for `subagent_cost` with `unit: currencyUSD`
  and color-background gradient matching the Top Sessions table
  style. Full width (w: 24). Verify the panel is a child of Row 3.

- [x] 2.4 Add Row 4 ("Are there sub-agent cost patterns?") with two
  new panels. Row panel ID: 103 (after renumbering). Set
  `collapsed: true`.
  Panel "Cost per Sub-Agent Type" (id 92): horizontal bar chart.
  Query: `SELECT s.agent, ROUND(SUM(m.value), 2) AS total_cost FROM sessions s JOIN measurements m ON m.session_id = s.session_id WHERE s.parent_session_id IS NOT NULL AND m.metric_name = 'cost' GROUP BY s.agent ORDER BY total_cost DESC`.
  Style: `fillOpacity: 80`, `gradientMode: scheme`, color
  `#73BF69`, horizontal orientation -- matching existing cost bar
  charts. Width: 12.
  Panel "Invocations per Sub-Agent Type" (id 93): horizontal bar
  chart. Query: `SELECT agent, COUNT(DISTINCT session_id) AS invocations FROM sessions WHERE parent_session_id IS NOT NULL GROUP BY agent ORDER BY invocations DESC`.
  Style: `fillOpacity: 80`, `gradientMode: scheme`, color
  `#B877D9` (purple, matching session panels), horizontal
  orientation. Width: 12. Verify Row 4 contains exactly 2 panels.

- [x] 2.5 Add "Monthly Cost Trend" timeseries panel to Row 8.
  ID: 94. Query:
  `SELECT MIN(recorded_at_epoch) as time, SUM(delta) as cost FROM v_measurement_deltas WHERE metric_name = 'cost' GROUP BY strftime('%Y-%m', datetime(recorded_at_epoch, 'unixepoch')) ORDER BY time`.
  Style: match existing Weekly Cost Trend (id 70) -- `unit:
  currencyUSD`, color `#FADE2A`, drawStyle line, fillOpacity 15,
  lineInterpolation smooth. Width: 12. Add budget threshold line
  at `{{ monthly_warn }}` (warn) and `{{ monthly_crit }}` (crit)
  using Jinja2 variables. Verify the panel is a child of Row 8.

- [x] 2.6 Add "Yearly Cost Trend" timeseries panel to Row 8.
  ID: 95. Query:
  `SELECT MIN(recorded_at_epoch) as time, SUM(delta) as cost FROM v_measurement_deltas WHERE metric_name = 'cost' GROUP BY strftime('%Y', datetime(recorded_at_epoch, 'unixepoch')) ORDER BY time`.
  Style: match Weekly Cost Trend -- `unit: currencyUSD`, color
  `#FADE2A`, drawStyle line, fillOpacity 15, lineInterpolation
  smooth. Width: 24 (full width). Add budget threshold line at
  `{{ yearly_warn }}` (warn) and `{{ yearly_crit }}` (crit).
  Verify Row 8 contains exactly 3 panels (Weekly + Monthly +
  Yearly).

## 3. Spec Update

- [x] 3.1 [P] Update `openspec/specs/grafana-metrics/spec.md` to
  reflect the new 8-row question-based structure, new panel list,
  sub-agent analytics scenarios, and monthly/yearly trend scenarios.
  Apply the delta from `specs/grafana-metrics/spec.md` in this
  change. Verify the updated spec lists all 8 row titles and
  mentions sub-agent panels.

## 4. Verification

- [x] 4.1 Render the Jinja2 template with default variables and
  validate the output is valid JSON:
  `python3 -c "from jinja2 import Template; import json; t=Template(open('templates/opencode_metrics_dashboard.json.j2').read()); out=t.render(ai_grafana_metrics_monthly_budget=300); json.loads(out); print('Valid JSON, panels:', len(json.loads(out)['panels']))"`.
  Verify the output reports approximately 50 panels (8 row panels
  + ~42 content panels in collapsed rows + content panels in
  expanded Row 1).

- [x] 4.2 Verify no existing panel IDs are duplicated. Extract all
  panel IDs from the rendered JSON and confirm uniqueness:
  `python3 -c "from jinja2 import Template; import json; t=Template(open('templates/opencode_metrics_dashboard.json.j2').read()); d=json.loads(t.render(ai_grafana_metrics_monthly_budget=300)); ids=[p['id'] for p in d['panels']]; [ids.extend(p2['id'] for p2 in p.get('panels',[])) for p in d['panels']]; assert len(ids)==len(set(ids)), f'Duplicate IDs: {[i for i in ids if ids.count(i)>1]}'; print(f'All {len(ids)} panel IDs unique')"`.

- [x] 4.3 Verify row titles are question-based. Extract all row
  panel titles and confirm each contains a question mark:
  `python3 -c "from jinja2 import Template; import json; t=Template(open('templates/opencode_metrics_dashboard.json.j2').read()); d=json.loads(t.render(ai_grafana_metrics_monthly_budget=300)); rows=[p for p in d['panels'] if p['type']=='row']; [print(p['title']) for p in rows]; assert all('?' in p['title'] for p in rows), 'Not all rows are questions'"`.

- [x] 4.4 Verify only Row 1 is expanded. Check that exactly one row
  has `collapsed: false` and it is the first row:
  `python3 -c "from jinja2 import Template; import json; t=Template(open('templates/opencode_metrics_dashboard.json.j2').read()); d=json.loads(t.render(ai_grafana_metrics_monthly_budget=300)); rows=[p for p in d['panels'] if p['type']=='row']; expanded=[r for r in rows if not r['collapsed']]; assert len(expanded)==1, f'Expected 1 expanded row, got {len(expanded)}'; assert expanded[0]['gridPos']['y']==0, 'Expanded row is not first'; print('OK: only Row 1 expanded')"`.
