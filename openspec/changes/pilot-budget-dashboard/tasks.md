# Tasks

## 1. Ansible Variables

- [ ] 1.1 Add pilot budget variables to `defaults/main.yml`: `ai_grafana_pilot_budget` (default: 0), `ai_grafana_pilot_review_threshold` (default: 0), `ai_grafana_pilot_start_date` (default: ""), `ai_grafana_pilot_end_date` (default: ""), `ai_grafana_pilot_repos` (default: []). Verify by running `ansible-inventory --list` or inspecting the rendered defaults and confirming all five variables appear with their safe defaults.

## 2. Pilot Dashboard Template

- [ ] 2.1 Create `templates/opencode_pilot_dashboard.json.j2` with Jinja preamble that computes epoch timestamps from `ai_grafana_pilot_start_date` and `ai_grafana_pilot_end_date`, builds a SQL IN clause from `ai_grafana_pilot_repos`, and derives budget thresholds from `ai_grafana_pilot_budget` and `ai_grafana_pilot_review_threshold`. Verify by rendering the template with test variables and confirming the computed values are correct.
- [ ] 2.2 Implement the "Pilot Budget" row (permanently expanded) with panels: Pilot-to-Date Cost (stat with warn/crit thresholds), This Week cost (stat, Monday-Sunday), Budget Remaining (stat), Days Remaining (stat), Burn Rate (stat), and Excluded/Unattributed Cost (stat). All queries SHALL filter by pilot date range and approved repos via the SQL IN clause. Verify by loading the rendered JSON into Grafana with test data and confirming panel values match expected calculations.
- [ ] 2.3 Implement the "Repository Attribution" row (collapsed) with panels: Cost per Approved Repo (bar chart), Daily Cost per Repo (time-series), Sessions per Repo (stat). All panels scoped to approved repos and pilot dates. Verify by confirming non-approved repos do not appear in any panel.
- [ ] 2.4 Implement the "Work Output" row (collapsed) with panels: PRs Created (stat), PRs Reviewed (stat), Issues Referenced (stat), Non-Deliverable Spend (stat), Most Expensive PRs (table). All scoped to approved repos and pilot dates. Verify by confirming the panel queries join on project and filter by the repo list.
- [ ] 2.5 Implement the "Session Breakdown" row (collapsed) with panels: Root Session Count (stat), Child Session Count (stat), Daily Cost Root vs Sub-Agent (time-series), Classification Breakdown (pie/bar). All scoped to pilot. Verify root/child counts use `parent_session_id IS NULL` / `IS NOT NULL` correctly.
- [ ] 2.6 Implement the "Model & Token Detail" row (collapsed) with panels: Cost by Model (bar chart), Token Usage by Type (bar chart), Cost per 1K Output Tokens (stat). All scoped to pilot. Verify model panel excludes sessions from non-approved repos.
- [ ] 2.7 Implement the "Data Quality & Evidence" row (collapsed) with panels: Last Data Point (stat showing MAX recorded_at_epoch), Estimate Disclaimer (text panel), Sessions with Missing Metadata (stat), and placeholder panels for Blocked Prompts, Hard Stops, Unmatched Sessions, and Reconciliation Failures. Verify the Last Data Point panel returns a valid timestamp, the text panel renders the disclaimer, and placeholder panels show "No data" without errors.
- [ ] 2.8 Set dashboard metadata: UID `opencode-pilot-dashboard`, title `OpenCode Pilot`, tags `["opencode", "pilot"]`, auto-refresh `30s`, default time range from pilot start date to `now`, timezone `browser`. Verify the UID and title differ from the operational dashboard.

## 3. Conditional Deployment Task

- [ ] 3.1 Add a conditional task block to `tasks/configure_grafana_metrics.yml` that templates `opencode_pilot_dashboard.json.j2` into the dashboards directory only when `ai_grafana_pilot_repos | length > 0` and `ai_grafana_pilot_start_date | length > 0`. Verify by running the playbook with pilot variables unset and confirming no pilot dashboard file is created, then with pilot variables set and confirming the file appears.

## 4. Documentation

- [ ] 4.1 Add a "Pilot Budget Dashboard" section to `README.md` under the existing "Metrics Visualization" section, documenting: the five new variables, how to enable the pilot dashboard, what the six rows contain, the estimate-vs-reconciled disclaimer, and how to disable the dashboard after the pilot ends. Verify the documented variable names match `defaults/main.yml` and the documented steps work as described.

## 5. Integration Verification

- [ ] 5.1 Run the full playbook with both the operational dashboard and pilot dashboard enabled (all pilot variables configured). Verify both JSON files are present in the dashboards directory, the Grafana container starts and lists both dashboards, and panels render without query errors against a database with test data.
