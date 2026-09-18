# Tasks

## 1. Default Variables

- [x] 1.1 Add `ai_opencode_metrics_version: "0.2.0"` to `defaults/main.yml` before the `ai_opencode_plugins` definition. Verify the variable appears before the plugins list.
- [x] 1.2 Change `ai_opencode_plugins` default from `[]` to `["@mburghardt/opencode-metrics@{{ ai_opencode_metrics_version }}"]`. Verify Ansible resolves the Jinja reference by running `ansible -m debug -a "var=ai_opencode_plugins" localhost` against a test playbook.
- [x] 1.3 Rename `ai_grafana_metrics_data_dir` to `ai_opencode_metrics_data_dir` in `defaults/main.yml`. Verify the old name no longer appears in the file.
- [x] 1.4 Add `ai_opencode_metrics_config: {}` to `defaults/main.yml` in the new metrics plugin variable group. Verify the variable is defined and defaults to an empty dict.

## 2. Variable Rename Propagation

- [x] 2.1 Update `templates/opencode_grafana.sh.j2` to reference `ai_opencode_metrics_data_dir` instead of `ai_grafana_metrics_data_dir`. Verify by grepping the template for the old variable name (should return zero matches).

## 3. Metrics Config Template and Tasks

- [x] 3.1 Create `templates/opencode_metrics_config.yaml.j2` that renders `ai_opencode_metrics_config` using `to_nice_yaml`. The template SHALL include the `---` YAML document marker. Verify the file exists and contains the expected Jinja expression.
- [x] 3.2 Add a conditional task to `tasks/configure_opencode.yml` that ensures `ai_opencode_metrics_data_dir` exists (mode `0755`) when `ai_opencode_metrics_config | length > 0`. Verify the task has the correct `when` condition.
- [x] 3.3 Add a conditional task to `tasks/configure_opencode.yml` that deploys `opencode_metrics_config.yaml.j2` to `{{ ai_opencode_metrics_data_dir }}/config.yaml` (mode `0644`) when `ai_opencode_metrics_config | length > 0`. Verify the task has the correct source, destination, and `when` condition.

## 4. Documentation

- [x] 4.1 Update the variable table in `README.md`: add `ai_opencode_metrics_version`, `ai_opencode_metrics_data_dir`, and `ai_opencode_metrics_config`; update `ai_opencode_plugins` default value; remove `ai_grafana_metrics_data_dir`. Verify the old variable name no longer appears in the README.
- [x] 4.2 Update the plugin section in `README.md` to reflect that the metrics plugin is included by default, with examples showing how to customize or remove it. Verify the section documents the new default behavior.

## 5. Validation

- [x] 5.1 Run `yamllint` on `defaults/main.yml` to verify YAML validity. Verify zero lint errors.
- [x] 5.2 Run `ansible-lint` on the role to verify no Ansible lint violations. Verify zero errors.
