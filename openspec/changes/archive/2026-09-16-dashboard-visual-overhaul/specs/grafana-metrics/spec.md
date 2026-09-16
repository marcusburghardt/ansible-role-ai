## MODIFIED Requirements

### Requirement: Pre-built dashboard with 9 panels
The deployed dashboard JSON SHALL contain approximately 30 panels
organized in 8 collapsible row sections covering cost overview, token
efficiency, session analytics, efficiency metrics, code impact, top
sessions, and trends from the opencode-metrics database. A KPI summary
row SHALL be permanently expanded at the top of the dashboard.

#### Scenario: Dashboard panels query the correct metrics
- **GIVEN** the Grafana container is running
- **AND** the opencode-metrics database contains session data
- **WHEN** the user opens the dashboard at http://localhost:3033
- **THEN** the dashboard SHALL display a KPI row with stat panels for:
  Total Sessions, Total Cost, Avg Session Cost, Cache Hit %,
  Output Tokens (M), Active Projects
- **AND** SHALL display collapsible sections for:
  Cost Overview (Daily Cost, Cost by Classification, Cost by Model,
  Cost by Project, Avg Cost by Classification),
  Token Efficiency (Token Usage Over Time, Token Distribution,
  Cache Hit Ratio Over Time),
  Session Analytics (Sessions by Day, Sessions by Classification
  Over Time, Duration Distribution, Sessions by Agent Type,
  Avg Duration by Classification, Messages per Classification),
  Efficiency (Cost per 1K Output Tokens, Cache Hit by Classification,
  Cost per File Changed),
  Code Impact (Lines Changed Over Time, Files Changed by Project),
  Top Sessions (table with title, classification, model, agent,
  project, cost, date),
  Trends (Weekly Cost, 7-Day Rolling Average Cost)

#### Scenario: Dashboard handles empty database gracefully
- **GIVEN** the Grafana container is running
- **AND** the opencode-metrics database exists but has no data
- **WHEN** the user opens the dashboard
- **THEN** the panels SHALL display "No data" without errors

#### Scenario: Dashboard auto-refreshes to show new data
- **GIVEN** the Grafana container is running
- **AND** the dashboard is open in a browser
- **WHEN** new sessions are recorded in the metrics database
- **THEN** the dashboard SHALL auto-refresh at a 30-second interval
- **AND** SHALL display a live indicator showing it is auto-refreshing

#### Scenario: Time-series panels render data correctly
- **GIVEN** the opencode-metrics database stores timestamps as epoch
  milliseconds
- **WHEN** the dashboard queries time-series data
- **THEN** all time-series panels SHALL use epoch seconds (numeric) as
  the time column to avoid RFC3339 parsing failures
- **AND** panels SHALL respect the Grafana time range picker

#### Scenario: Pie chart panels render multiple slices
- **GIVEN** the opencode-metrics database contains sessions with
  multiple distinct classifications
- **WHEN** the user views a pie chart panel
- **THEN** each distinct category SHALL render as a separate slice
- **AND** the legend SHALL display value and percentage for each slice

#### Scenario: Project charts remain readable with many projects
- **GIVEN** the opencode-metrics database contains more than 10
  distinct projects
- **WHEN** the user views a project bar chart
- **THEN** the chart SHALL display the top 10 projects individually
- **AND** SHALL aggregate remaining projects into an "Other" bucket

#### Scenario: Detail sections are collapsed by default
- **GIVEN** the user opens the dashboard for the first time
- **WHEN** the dashboard loads
- **THEN** only the KPI row SHALL be expanded
- **AND** all detail sections (Cost, Tokens, Sessions, Efficiency,
  Code Impact, Top Sessions, Trends) SHALL be collapsed

#### Scenario: Dashboard uses section-specific color accents
- **GIVEN** the dashboard is viewed on a dark-theme Grafana instance
- **WHEN** the user expands any section
- **THEN** panels in the Cost section SHALL use green/amber tones
- **AND** panels in the Token section SHALL use blue/cyan tones
- **AND** panels in the Session section SHALL use purple tones
- **AND** panels in the Efficiency section SHALL use orange tones
- **AND** panels in the Code Impact section SHALL use teal tones
- **AND** panels in the Trends section SHALL use yellow/gold tones
