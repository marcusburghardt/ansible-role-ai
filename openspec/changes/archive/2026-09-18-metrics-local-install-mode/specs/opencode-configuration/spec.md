# Spec Delta

## MODIFIED Requirements

### Requirement: Plugin deployment list
The role SHALL provide an `ai_opencode_plugins` list variable that is rendered
directly as the `"plugin"` array in the deployed `opencode.json`. The default
value SHALL include `@mburghardt/opencode-metrics` at the version specified by
`ai_opencode_metrics_version` when that version is a semver string or `"latest"`.
When `ai_opencode_metrics_version` is `"local"`, the default list SHALL NOT
include any `@mburghardt/opencode-metrics` npm entry. Users MAY override this list
entirely to add, remove, or replace plugins in their playbook.

#### Scenario: Default plugins include metrics in npm mode
- **WHEN** the consumer does not override `ai_opencode_plugins` and `ai_opencode_metrics_version` is `"0.2.0"`
- **THEN** the deployed `opencode.json` SHALL contain `"plugin": ["@mburghardt/opencode-metrics@0.2.0"]`

#### Scenario: Default plugins exclude metrics npm entry in local mode
- **WHEN** the consumer does not override `ai_opencode_plugins` and `ai_opencode_metrics_version` is `"local"`
- **THEN** the deployed `opencode.json` SHALL contain `"plugin": []` (or a list without any `@mburghardt/opencode-metrics` entry)

#### Scenario: User removes the default plugin
- **WHEN** the consumer sets `ai_opencode_plugins` to `[]`
- **THEN** the deployed `opencode.json` SHALL contain `"plugin": []`

#### Scenario: User adds plugins alongside the default
- **WHEN** the consumer sets `ai_opencode_plugins` to `["@mburghardt/opencode-metrics@{{ ai_opencode_metrics_version }}", "@angdrew/opencode-hashline-plugin"]`
- **THEN** the deployed `opencode.json` SHALL contain both plugins in the `"plugin"` array

#### Scenario: Plugin list reflects user additions
- **WHEN** the consumer sets `ai_opencode_plugins` to `["@angdrew/opencode-hashline-plugin"]`
- **THEN** the deployed `opencode.json` SHALL contain `"plugin": ["@angdrew/opencode-hashline-plugin"]` (metrics plugin is not present because the user replaced the entire list)
