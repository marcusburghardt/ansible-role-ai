## 1. Add Variables and Task Entry

- [x] 1.1 Add `{ enabled: false, name: 'configure_grafana_metrics' }`
  to `ai_tasks` in `defaults/main.yml`
- [x] 1.2 Add Grafana metrics variables to `defaults/main.yml`:
  `ai_grafana_metrics_port` (default: 3033),
  `ai_grafana_metrics_container_name` (default: "opencode-grafana"),
  `ai_grafana_metrics_script_name` (default: "opencode-grafana"),
  `ai_grafana_metrics_data_dir`
  (default: "{{ ai_user_home_dir }}/.local/share/opencode-metrics"),
  `ai_grafana_metrics_provisioning_dir`
  (default: "{{ ai_opencode_config_dir }}/grafana")
- [x] 1.3 Create empty `vars/configure_grafana_metrics.yml` placeholder

## 2. Create Provisioning Files

- [x] 2.1 Create `files/grafana/provisioning/datasources/sqlite.yaml`
  with SQLite datasource configuration pointing to
  `/data/metrics/metrics.db` with query_only mode
- [x] 2.2 Create `files/grafana/provisioning/dashboards/provider.yaml`
  with file-based dashboard provider pointing to
  `/var/lib/grafana/dashboards/`
- [x] 2.3 Create `files/grafana/dashboards/opencode-metrics.json` with
  pre-built Grafana dashboard containing 9 panels:
  (1) Daily Cost time-series,
  (2) Cost by Classification pie chart,
  (3) Cost by Project bar chart,
  (4) Cost by Model bar chart,
  (5) Cache Hit Ratio time-series,
  (6) Session Count by Day bar chart,
  (7) Token Usage time-series (input/output/cache_read),
  (8) Duration Distribution histogram,
  (9) Top Sessions table (title, classification, model, cost).
  All time-series queries SHALL divide timestamp columns by 1000 to
  convert from epoch milliseconds to epoch seconds. Use the SQLite
  datasource UID "opencode-metrics-sqlite".

## 3. Create Helper Script Template

- [x] 3.1 Create `templates/opencode_grafana.sh.j2` with subcommands:
  start (podman run with all mounts, env vars, and port binding),
  stop (podman stop and rm),
  status (podman ps filter),
  logs (podman logs --follow).
  Include pre-flight checks: verify podman is installed, verify
  metrics data directory exists, verify container is not already
  running (for start) or is running (for stop/logs).
  Use these container settings:
  - Image: docker.io/grafana/grafana:latest
  - Port: {{ ai_grafana_metrics_port }}:3000
  - Volume: opencode-grafana-data:/var/lib/grafana
  - Bind mounts:
    {{ ai_grafana_metrics_data_dir }}:/data/metrics:ro
    {{ ai_grafana_metrics_provisioning_dir }}/provisioning:/etc/grafana/provisioning:ro
    {{ ai_grafana_metrics_provisioning_dir }}/dashboards:/var/lib/grafana/dashboards:ro
  - Environment:
    GF_INSTALL_PLUGINS=frser-sqlite-datasource
    GF_SECURITY_ADMIN_PASSWORD=admin
    GF_AUTH_ANONYMOUS_ENABLED=true
    GF_AUTH_ANONYMOUS_ORG_ROLE=Admin

## 4. Create Ansible Task File

- [x] 4.1 Create `tasks/configure_grafana_metrics.yml` with tasks:
  (a) Create provisioning directory structure
  ({{ ai_grafana_metrics_provisioning_dir }}/provisioning/datasources,
  {{ ai_grafana_metrics_provisioning_dir }}/provisioning/dashboards,
  {{ ai_grafana_metrics_provisioning_dir }}/dashboards),
  (b) Deploy datasource YAML from files/grafana/provisioning/datasources/,
  (c) Deploy dashboard provider YAML from files/grafana/provisioning/dashboards/,
  (d) Deploy dashboard JSON from files/grafana/dashboards/,
  (e) Deploy helper script to {{ ai_user_scripts_dir }} with mode 0755.
  All task names SHALL follow the role convention:
  "{{ role_name }} | configure_grafana_metrics | <description>"

## 5. Update Documentation

- [x] 5.1 Document `configure_grafana_metrics` task in README.md task
  table. Document all `ai_grafana_metrics_*` variables with types,
  defaults, and descriptions in the variables table.
- [x] 5.2 Add a "Metrics Visualization" section to README.md with usage
  instructions: enable the task, run the playbook, then use
  `opencode-grafana start` to launch Grafana at localhost:3033.
  Include prerequisites (podman installed, opencode-metrics plugin
  collecting data).

## 6. Update Spec

- [x] 6.1 Create `openspec/specs/grafana-metrics/spec.md` with the
  requirements and scenarios from the delta spec.

## 7. Verification

- [x] 7.1 Run `yamllint .` to verify all YAML files pass linting
- [x] 7.2 Run `ansible-lint` to verify the new task file passes linting
- [x] 7.3 Manually test: enable the task, run the playbook, verify
  provisioning files and helper script are deployed, run
  `opencode-grafana start`, open http://localhost:3033, verify the
  dashboard loads with panels (data may be empty if no metrics exist)
