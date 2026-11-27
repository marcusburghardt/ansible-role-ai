# Spec Delta

## MODIFIED Requirements

### Requirement: Template incorporates role variables
The template SHALL incorporate variables for model, default agent
(`default_agent`), update policy, agent configuration (`ai_opencode_agents`),
plugin list (`ai_opencode_plugins`), provider settings (`ai_opencode_providers`),
permissions (`ai_opencode_permissions`), compaction settings
(`ai_opencode_compaction`), instruction file list (`ai_opencode_instructions`),
MCP server list (`ai_opencode_mcp_servers`), and watcher ignore patterns.

#### Scenario: Configuration file reflects variable overrides
- **WHEN** the consumer overrides `ai_model` to `anthropic/claude-sonnet-4-5` and `ai_gcp_project` to `my-project`
- **THEN** the deployed `opencode.json` SHALL contain the overridden model value and the GCP project in `providers.google-vertex.settings.project`

#### Scenario: Instructions list includes org governance files by default
- **WHEN** the role deploys with default `ai_opencode_instructions` value
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["~/.config/opencode/commit.md", "~/.config/opencode/pr.md", "~/.config/opencode/coding-standards.md", "~/.config/opencode/agent-operating-rules.md", ".specify/memory/constitution.md", "AGENTS.md"]`, with global baseline files preceding repository-relative paths

#### Scenario: Instructions list is customizable
- **WHEN** the consumer overrides `ai_opencode_instructions` to `["CUSTOM.md"]`
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["CUSTOM.md"]`

#### Scenario: Agent routing block is rendered from variable
- **WHEN** the role deploys with default `ai_opencode_agents` value and default `ai_model` (`ollama/qwen3:8b`)
- **THEN** the deployed `opencode.json` SHALL contain an `"agents"` block with `build`, `plan`, `explore`, and `general` keys, all with `model` set to `ollama/qwen3:8b`

#### Scenario: Agent routing reflects per-agent model overrides
- **WHEN** the consumer sets `ai_opencode_agent_plan_model` to `google-vertex/claude-sonnet-4-6@default` and `ai_opencode_agent_explore_model` to `google-vertex/claude-haiku-4-5@20251001`
- **THEN** the deployed `opencode.json` SHALL contain an `"agents"` block where `plan.model` is `google-vertex/claude-sonnet-4-6@default` and `explore.model` is `google-vertex/claude-haiku-4-5@20251001`, while `build` and `general` retain their defaults

#### Scenario: Plugin list renders metrics plugin by default
- **WHEN** the role deploys with default `ai_opencode_plugins` value
- **THEN** the deployed `opencode.json` SHALL contain `"plugins": []`, replacing the previous metrics-enabled default while the plugin awaits V2 migration

#### Scenario: Compaction settings are rendered from variable
- **WHEN** the role deploys with default `ai_opencode_compaction` value
- **THEN** the deployed `opencode.json` SHALL contain `"compaction": {"auto": true, "keep": {"tokens": 15000}, "buffer": 10000}`

#### Scenario: Compaction settings reflect user overrides
- **WHEN** the consumer overrides `ai_opencode_compaction` to `{"auto": false, "keep": {"tokens": 24000}, "buffer": 16000}`
- **THEN** the deployed `opencode.json` SHALL contain the overridden compaction values

## ADDED Requirements

### Requirement: Render MCP server configuration
The role SHALL provide an `ai_opencode_mcp_servers` dict variable, defaulting to
`{}`, whose entries are rendered unchanged as the OpenCode V2 `mcp.servers`
block. The block SHALL always be present so an empty value cannot inherit a
server from a previous hand edit.

#### Scenario: Empty default renders an explicit empty block
- **WHEN** the consumer does not override `ai_opencode_mcp_servers`
- **THEN** the deployed `opencode.json` SHALL contain `"mcp": {"servers": {}}`

#### Scenario: Consumer declares a local server
- **WHEN** the consumer sets `ai_opencode_mcp_servers` to a single entry with `type: local` and a `command` list
- **THEN** the deployed `opencode.json` SHALL contain that entry under `mcp.servers` with its type and command unchanged

#### Scenario: Server names are not placed directly under mcp
- **WHEN** the role deploys a configuration with one configured server
- **THEN** the server name SHALL appear only under `mcp.servers`, never as a direct child of `mcp`

#### Scenario: A disabled server is still rendered
- **WHEN** a consumer entry sets `disabled: true`
- **THEN** the deployed `opencode.json` SHALL include that entry with `disabled` set to `true`
