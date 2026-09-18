## MODIFIED Requirements

### Requirement: Deploy OpenCode configuration file from template
The role SHALL deploy the OpenCode configuration file to `ai_opencode_config_file` (default: `~/.config/opencode/opencode.json`) using a Jinja2 template. The template SHALL incorporate variables for model, small_model, agent routing (`ai_opencode_agents`), plugin list (`ai_opencode_plugins`), provider settings, disabled providers, permissions, compaction settings (`ai_opencode_compaction`), and a variable-driven instructions file list (`ai_opencode_instructions`).

#### Scenario: Configuration file is deployed with default settings
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** the role creates or overwrites `~/.config/opencode/opencode.json` from the `opencode.json.j2` template with the values from role variables, with file mode `0600`

#### Scenario: Configuration file reflects variable overrides
- **WHEN** the consumer overrides `ai_model` to `anthropic/claude-sonnet-4-5` and `ai_gcp_project` to `my-project`
- **THEN** the deployed `opencode.json` SHALL contain the overridden model and GCP project values

#### Scenario: Instructions list includes org governance files by default
- **WHEN** the role deploys with default `ai_opencode_instructions` value
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["~/.config/opencode/commit.md", "~/.config/opencode/coding-standards.md", ".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]`, with global baseline files preceding repository-relative paths

#### Scenario: Instructions list is customizable
- **WHEN** the consumer overrides `ai_opencode_instructions` to `["CUSTOM.md"]`
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["CUSTOM.md"]`

#### Scenario: Configuration directory is created if missing
- **WHEN** the parent directory of `ai_opencode_config_file` does not exist
- **THEN** the role SHALL create the directory structure before deploying the config file

#### Scenario: Agent routing block is rendered from variable
- **WHEN** the role deploys with default `ai_opencode_agents` value and default `ai_model` / `ai_small_model` (both `ollama/qwen3:8b`)
- **THEN** the deployed `opencode.json` SHALL contain an `"agent"` block with `build`, `plan`, `explore`, and `general` keys, all with `model` set to `ollama/qwen3:8b`

#### Scenario: Agent routing reflects per-agent model overrides
- **WHEN** the consumer sets `ai_opencode_agent_plan_model` to `google-vertex-anthropic/claude-sonnet-4-6@default` and `ai_opencode_agent_explore_model` to `google-vertex-anthropic/claude-haiku-4-5@20251001`
- **THEN** the deployed `opencode.json` SHALL contain an `"agent"` block where `plan.model` is `google-vertex-anthropic/claude-sonnet-4-6@default` and `explore.model` is `google-vertex-anthropic/claude-haiku-4-5@20251001`, while `build` and `general` retain their defaults

#### Scenario: Plugin list renders metrics plugin by default
- **WHEN** the role deploys with default `ai_opencode_plugins` value
- **THEN** the deployed `opencode.json` SHALL contain `"plugin": ["@mburghardt/opencode-metrics@0.3.0"]`

#### Scenario: Compaction settings are rendered from variable
- **WHEN** the role deploys with default `ai_opencode_compaction` value
- **THEN** the deployed `opencode.json` SHALL contain `"compaction": {"auto": true, "prune": true, "reserved": 10000}`

#### Scenario: Compaction settings reflect user overrides
- **WHEN** the consumer overrides `ai_opencode_compaction` to `{"auto": true, "prune": false, "reserved": 5000}`
- **THEN** the deployed `opencode.json` SHALL contain the overridden compaction values

## ADDED Requirements

### Requirement: Per-agent model variables for independent routing control
The role SHALL provide individual default variables for each OpenCode built-in agent's model assignment: `ai_opencode_agent_build_model` (default: `{{ ai_model }}`), `ai_opencode_agent_plan_model` (default: `{{ ai_small_model }}`), `ai_opencode_agent_explore_model` (default: `{{ ai_small_model }}`), and `ai_opencode_agent_general_model` (default: `{{ ai_small_model }}`). These variables SHALL be referenced by the `ai_opencode_agents` dict and SHALL allow consumers to override individual agent models without replacing the entire agent configuration dict.

#### Scenario: Default agent models resolve to primary model variables
- **WHEN** the consumer does not override any `ai_opencode_agent_*_model` variables
- **THEN** `ai_opencode_agent_build_model` SHALL resolve to the value of `ai_model`, and `ai_opencode_agent_plan_model`, `ai_opencode_agent_explore_model`, and `ai_opencode_agent_general_model` SHALL resolve to the value of `ai_small_model`

#### Scenario: Individual agent model override does not affect other agents
- **WHEN** the consumer overrides only `ai_opencode_agent_plan_model` to a Sonnet model
- **THEN** only the `plan` agent's model SHALL change; `build`, `explore`, and `general` SHALL retain their defaults

### Requirement: Plugin deployment list
The role SHALL provide an `ai_opencode_plugins` list variable that is rendered
directly as the `"plugin"` array in the deployed `opencode.json`. The default
value SHALL include `@mburghardt/opencode-metrics` at the version specified by
`ai_opencode_metrics_version` when that version is a semver string or `"latest"`.
When `ai_opencode_metrics_version` is `"local"`, the default list SHALL NOT
include any `@mburghardt/opencode-metrics` npm entry. Users MAY override this list
entirely to add, remove, or replace plugins in their playbook.

#### Scenario: Default plugins include metrics in npm mode
- **WHEN** the consumer does not override `ai_opencode_plugins` and `ai_opencode_metrics_version` is `"0.3.0"`
- **THEN** the deployed `opencode.json` SHALL contain `"plugin": ["@mburghardt/opencode-metrics@0.3.0"]`

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

### Requirement: Data-driven compaction settings
The role SHALL provide an `ai_opencode_compaction` dict variable (default: `{auto: true, prune: true, reserved: 10000}`) that is rendered directly as the `"compaction"` block in the deployed `opencode.json`. This replaces the previously hardcoded compaction block in the template.

#### Scenario: Default compaction matches previous behavior
- **WHEN** the consumer does not override `ai_opencode_compaction`
- **THEN** the deployed `opencode.json` SHALL contain `"compaction": {"auto": true, "prune": true, "reserved": 10000}`, matching the previously hardcoded values

#### Scenario: User tunes compaction
- **WHEN** the consumer overrides `ai_opencode_compaction` to `{"auto": false, "prune": true, "reserved": 20000}`
- **THEN** the deployed `opencode.json` SHALL contain the overridden compaction values
