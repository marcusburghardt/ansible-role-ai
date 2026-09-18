# Spec Delta

## MODIFIED Requirements

### Requirement: Pre-built dashboard with 9 panels
The deployed dashboard JSON SHALL contain approximately 50 panels
organized in 8 collapsible row sections. Each row title SHALL be
phrased as a question reflecting the information it answers. The rows
SHALL follow the engineer's daily cost-review workflow: budget pulse,
cost distribution, session investigation, sub-agent patterns, session
activity, token efficiency, outcomes, and trends. A budget-focused KPI
row SHALL be permanently expanded at the top of the dashboard.

#### Scenario: Dashboard panels query the correct metrics
- **GIVEN** the Grafana container is running
- **AND** the opencode-metrics database contains session data with
  Schema V4 (parent_session_id column present)
- **WHEN** the user opens the dashboard at http://localhost:3033
- **THEN** the dashboard SHALL display a row titled
  "How much have I spent?" with stat panels for: Today's Cost,
  Active This Week, Active This Month, Active This Year, Total Cost,
  plus a Daily Cost timeseries and a 7-Day Rolling Average timeseries
- **AND** SHALL display a collapsed row titled
  "Where is the money going?" with panels for: Cost by Classification,
  Cost by Model, Cost by Project (Top 10), Daily Cost Root vs
  Sub-Agent, Avg Cost per Session by Classification, Active Projects
- **AND** SHALL display a collapsed row titled
  "Which sessions are the most expensive?" with panels for:
  Top Sessions by Total Cost (table showing own_cost, total_cost,
  subagent_cost columns), Most Expensive Sub-Agents (table showing
  parent_title, parent_agent, subagent_type, subagent_model,
  subagent_cost)
- **AND** SHALL display a collapsed row titled
  "Are there sub-agent cost patterns?" with panels for:
  Cost per Sub-Agent Type, Invocations per Sub-Agent Type
- **AND** SHALL display a collapsed row titled
  "What does my session activity look like?" with panels for:
  Total Sessions, Avg Session Cost, Sessions by Day, Sessions by
  Classification Over Time, Duration Distribution, Sessions by
  Agent Type, Avg Duration by Classification, Messages per
  Classification
- **AND** SHALL display a collapsed row titled
  "How efficient is my token usage?" with panels for:
  Cache Hit %, Output Tokens (M), Token Usage Over Time, Token
  Distribution by Type, Cache Hit Ratio Over Time, Cost per 1K
  Output Tokens, Cache Hit by Classification, Cost per File Changed
- **AND** SHALL display a collapsed row titled
  "What am I getting for the money?" with panels for:
  Lines Changed Over Time, Files Changed by Project, PRs Created,
  PRs Reviewed, Avg Cost per PR, Sessions with PRs, PR Activity
  Over Time, Cost per PR Trend, PR Activity by Classification,
  PRs per Session, Non-Deliverable Spend, Most Expensive PRs
- **AND** SHALL display a collapsed row titled
  "What are the longer-term trends?" with panels for:
  Weekly Cost Trend, Monthly Cost Trend, Yearly Cost Trend

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
- **THEN** only the first row ("How much have I spent?") SHALL be
  expanded
- **AND** all other rows SHALL be collapsed

#### Scenario: Dashboard uses section-specific color accents
- **GIVEN** the dashboard is viewed on a dark-theme Grafana instance
- **WHEN** the user expands any section
- **THEN** panels in the Cost section SHALL use green/amber tones
- **AND** panels in the Token section SHALL use blue/cyan tones
- **AND** panels in the Session section SHALL use purple tones
- **AND** panels in the Efficiency section SHALL use orange tones
- **AND** panels in the Code Impact section SHALL use teal tones
- **AND** panels in the Trends section SHALL use yellow/gold tones

#### Scenario: Sub-agent panels degrade gracefully on Schema V3
- **GIVEN** the opencode-metrics database is on Schema V3
- **AND** the sessions table does NOT have a parent_session_id column
- **WHEN** the user opens a sub-agent panel
- **THEN** the panel SHALL display "No data" without errors
- **AND** all non-sub-agent panels SHALL continue to function normally

#### Scenario: Top Sessions table shows sub-agent cost breakdown
- **GIVEN** the opencode-metrics database contains root sessions that
  spawned sub-agent sessions
- **WHEN** the user expands the "Which sessions are the most
  expensive?" row
- **THEN** the Top Sessions table SHALL display columns for own_cost,
  total_cost, and subagent_cost
- **AND** total_cost SHALL equal own_cost plus the recursive sum of
  all descendant sub-agent costs
- **AND** sessions SHALL be ordered by total_cost descending

#### Scenario: Monthly and yearly trends support budget predictability
- **GIVEN** the opencode-metrics database contains data spanning
  multiple months
- **WHEN** the user expands the "What are the longer-term trends?" row
- **THEN** the Monthly Cost Trend panel SHALL display one data point
  per calendar month
- **AND** the Yearly Cost Trend panel SHALL display one data point
  per calendar year
- **AND** both panels SHALL use delta-based cost aggregation for
  accurate period attribution
