## Context

The current dashboard JSON (`files/grafana/dashboards/opencode-metrics.json`)
has three functional bugs identified during testing and lacks visual polish.
See proposal.md for full motivation. The opencode-metrics plugin stores
timestamps as epoch milliseconds (INTEGER), and the frser-sqlite-datasource
Grafana plugin expects either epoch seconds (numeric) or RFC3339 strings
for time columns. The dashboard must work around this mismatch.

## Goals / Non-Goals

**Goals:**

- Fix the three functional bugs (pie chart single slice, time-series
  no data, project chart overcrowding)
- Rebuild the dashboard with ~30 panels in 8 collapsible rows
- Apply a cohesive dark-theme color palette with section-specific accents
- Enable auto-refresh so the dashboard reflects new data without manual
  reload

**Non-Goals:**

- Modifying the opencode-metrics plugin's timestamp format (proposed
  separately as an upstream improvement)
- Adding Grafana template variables (e.g., project/model dropdowns) --
  this is a v1 static dashboard
- Changing the helper script, provisioning files, or Ansible task
- Supporting Grafana light theme optimization

## Decisions

### Decision 1: Epoch seconds via MIN(recorded_at)/1000 for time columns

**Choice**: Use `MIN(recorded_at)/1000` as the time column in time-series
queries, grouping by `date(recorded_at/1000, 'unixepoch')` for daily
aggregation.

**Rationale**: The `date()` function returns `YYYY-MM-DD` strings that
fail RFC3339 parsing in the frser-sqlite-datasource plugin, breaking all
time-series panels. Returning raw epoch seconds as a numeric column
bypasses the string parsing entirely. `MIN()` picks the first timestamp
in each daily bucket, giving a valid epoch anchor for the time axis.

**Alternatives considered**:
- *Append T00:00:00Z to date() output*: Works but fragile -- depends on
  string concatenation and plugin parsing behavior.
- *Use recorded_at/1000 directly without daily grouping*: Shows per-session
  granularity instead of daily aggregation -- too noisy for overview panels.

### Decision 2: reduceOptions.values: true for pie charts

**Choice**: Set `reduceOptions: { values: true, calcs: [] }` on all
piechart panels.

**Rationale**: The default `calcs: ["sum"]` collapses all table rows
into a single aggregate value, producing one slice instead of multiple.
Setting `values: true` tells Grafana to use each row as a separate slice,
which is the correct behavior for categorical data from SQL queries.

### Decision 3: Top 10 + "Other" bucket for project charts

**Choice**: Use a UNION ALL query that selects the top 10 projects by
the metric value, then aggregates all remaining projects into a single
"Other" row.

**Rationale**: With 29+ projects, horizontal bar charts become unreadable.
Top 10 covers the most relevant data while "Other" ensures no data is
silently dropped. The UNION approach works in a single SQL query without
Grafana transformations.

**Alternatives considered**:
- *Simple LIMIT 10*: Silently discards data from remaining projects.
- *Grafana transformations*: Adds complexity in the JSON config and may
  not work consistently with the SQLite plugin.

### Decision 4: Collapsed rows with expanded KPI row

**Choice**: Use Grafana row panels with `collapsed: true` for all detail
sections (rows 2-8). The KPI row (row 1) uses `collapsed: false`.
Collapsed rows contain their child panels in the `panels` array of the
row panel itself.

**Rationale**: ~30 panels on a single scroll would be overwhelming. The
KPI row provides an at-a-glance summary. Users expand only the sections
they care about, reducing cognitive load and scroll distance.

### Decision 5: Section-specific color palettes via overrides

**Choice**: Apply explicit color overrides at the panel or field level
using Grafana's `overrides` and `thresholds` mechanisms. Each section
uses a distinct hue family:

| Section    | Primary hex | Used for                     |
|------------|-------------|------------------------------|
| KPIs       | mixed       | Each KPI matches its section |
| Cost       | #73BF69     | Green/amber tones            |
| Tokens     | #5794F2     | Blue/cyan tones              |
| Sessions   | #B877D9     | Purple tones                 |
| Efficiency | #FF9830     | Orange tones                 |
| Code       | #36A2EB     | Teal tones                   |
| Trends     | #FADE2A     | Yellow/gold tones            |

**Rationale**: Grafana's auto-assigned colors are inconsistent across
panels. Explicit colors create a cohesive visual identity and help users
orient by section at a glance. The chosen palette provides good contrast
on dark backgrounds.

### Decision 6: 30-second auto-refresh

**Choice**: Set `"refresh": "30s"` and `"liveNow": true` in the
dashboard JSON.

**Rationale**: The opencode-metrics plugin writes to SQLite on every
session idle event. A 30-second refresh balances data freshness with
container resource usage. The `liveNow` flag shows a visual indicator
that the dashboard is auto-updating.

## Risks / Trade-offs

- **Risk**: ~30 panels with complex SQL queries may slow dashboard load
  on large databases. **Mitigation**: Collapsed rows defer query
  execution until expanded. The SQLite database is local with indexed
  timestamp columns.
- **Risk**: The UNION ALL query for "Top 10 + Other" is more complex
  and could break if the SQLite plugin has UNION limitations.
  **Mitigation**: UNION ALL is standard SQL and supported by SQLite.
  Tested against the actual metrics database.
- **Trade-off**: Hardcoded color hex values mean the palette won't
  adapt to custom Grafana themes. Acceptable for a single-user
  local analytics tool.
- **Trade-off**: Collapsed rows require an extra click to see details.
  Users who prefer everything visible can manually expand and Grafana
  persists the state in the named volume.
