<!-- All tasks are sequential — each panel group builds on the row
     structure established in task 1.1. No [P] markers. -->

## 1. Row Structure

- [x] 1.1 Add a new collapsed row panel "PR & Issue Analytics" to
  the dashboard template after the Trends row (row 8). Follow the
  existing row pattern: type=row, collapsed=true, panels array
  containing all child panels. Assign panel IDs that don't conflict
  with existing panels (start from the next available ID).

## 2. KPI Panels

- [x] 2.1 Add "PRs Created" stat panel:
  SELECT SUM(value) FROM v_measurements
  WHERE metric_name = 'prs_created'
  AND recorded_at_epoch BETWEEN $__from/1000 AND $__to/1000
- [x] 2.2 Add "PRs Reviewed" stat panel:
  SELECT SUM(value) FROM v_measurements
  WHERE metric_name = 'prs_reviewed'
  AND recorded_at_epoch BETWEEN $__from/1000 AND $__to/1000
- [x] 2.3 Add "Avg Cost per PR" stat panel:
  SELECT printf('$%.2f', SUM(c.value) / SUM(p.value))
  FROM v_measurements c
  JOIN v_measurements p ON c.session_id = p.session_id
  WHERE c.metric_name = 'cost' AND p.metric_name = 'prs_created'
  AND p.value > 0
  AND c.recorded_at_epoch BETWEEN $__from/1000 AND $__to/1000
- [x] 2.4 Add "Sessions with PRs" stat panel:
  SELECT COUNT(DISTINCT session_id) FROM v_measurements
  WHERE metric_name = 'prs_created' AND value > 0
  AND recorded_at_epoch BETWEEN $__from/1000 AND $__to/1000

## 3. Time Series Panels

- [x] 3.1 Add "PR Activity Over Time" timeseries panel:
  Two queries (PRs Created, PRs Reviewed) using
  v_measurement_deltas with daily grouping, following the existing
  Daily Cost panel pattern. Coral for created, teal for reviewed.
- [x] 3.2 Add "Cost per PR Trend" timeseries panel:
  Weekly average cost per PR created. Query:
  SELECT strftime('%Y-W%W', recorded_at_epoch, 'unixepoch') as week,
  SUM(c.delta) / NULLIF(SUM(p.delta), 0) as cost_per_pr
  FROM v_measurement_deltas c
  JOIN v_measurement_deltas p ON c.session_id = p.session_id
    AND c.metric_name = 'cost' AND p.metric_name = 'prs_created'
  GROUP BY 1

## 4. Analytical Panels

- [x] 4.1 Add "PR Activity by Classification" horizontal bar panel:
  SELECT s.classification, SUM(m.value) as prs
  FROM v_measurements m JOIN v_sessions s ON m.session_id = s.session_id
  WHERE m.metric_name = 'prs_created' AND m.value > 0
  GROUP BY 1 ORDER BY 2 DESC
- [x] 4.2 Add "Most Expensive PRs" table panel (top 10):
  SELECT a.reference, SUM(c.value) as total_cost,
  COUNT(DISTINCT a.session_id) as sessions
  FROM v_session_artifacts a
  JOIN v_measurements c ON a.session_id = c.session_id
  WHERE a.artifact_type IN ('pr-created', 'pr-reviewed')
  AND c.metric_name = 'cost'
  GROUP BY 1 ORDER BY 2 DESC LIMIT 10
- [x] 4.3 Add "PRs per Session" bar chart panel:
  Distribution of how many PRs each session creates (0, 1, 2, 3+).
  SELECT CASE WHEN value >= 3 THEN '3+' ELSE CAST(value AS TEXT) END
  as prs, COUNT(*) as sessions
  FROM v_measurements WHERE metric_name = 'prs_created'
  GROUP BY 1 ORDER BY 1
- [x] 4.4 Add "Non-Deliverable Spend" stat panel:
  Percentage of cost from sessions with zero PRs and zero issues.
  SELECT printf('%.0f%%', 100.0 * SUM(CASE WHEN p.value = 0
  AND i.value = 0 THEN c.value ELSE 0 END) / SUM(c.value))
  FROM v_measurements c
  JOIN v_measurements p ON c.session_id = p.session_id
  JOIN v_measurements i ON c.session_id = i.session_id
  WHERE c.metric_name = 'cost' AND p.metric_name = 'prs_created'
  AND i.metric_name = 'issues_referenced'

## 5. Styling

- [x] 5.1 Apply color scheme: coral/salmon for PR-created metrics,
  teal for PR-reviewed, amber for issues, following the existing
  section-specific color palette pattern. Use gradient fills on
  time-series panels and threshold steps on stat panels.
- [x] 5.2 Set panel grid positions (gridPos) to arrange panels in
  a 2-column or 3-column layout matching the existing row patterns.
  KPI stats in a row of 4, time series full-width, analytical
  panels in 2-column layout, table full-width.

## 6. Verification

- [x] 6.1 Run make lint — YAML lint passes on the template
- [x] 6.2 Validate the JSON template renders correctly:
  ensure no Jinja2 syntax errors and valid JSON output
- [x] 6.3 Visual verification: provision the dashboard in a local
  Grafana instance and confirm all panels render with data from a
  backfilled database
