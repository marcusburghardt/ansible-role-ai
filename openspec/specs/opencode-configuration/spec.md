## Purpose

Deploy customizable OpenCode configuration, agent routing, plugins, and compaction settings.

## Requirements

### Requirement: Deploy OpenCode configuration file from template
The role SHALL deploy the OpenCode configuration file to `ai_opencode_config_file` (default: `~/.config/opencode/opencode.json`) using a Jinja2 template. The template SHALL incorporate variables for model, default agent (`default_agent`), update policy, agent configuration (`ai_opencode_agents`), plugin list (`ai_opencode_plugins`), provider settings (`ai_opencode_providers`), permissions (`ai_opencode_permissions`), compaction settings (`ai_opencode_compaction`), instruction file list (`ai_opencode_instructions`), and watcher ignore patterns. The template SHALL use OpenCode V2 config key names: `plugins` (not `plugin`), `agents` (not `agent`), `providers` (not `provider`), `permissions` (not `permission`), and `update` (not `autoupdate`). The template SHALL NOT include V1-only keys `small_model`, `share`, `options`, or `disabled_providers`.

#### Scenario: Configuration file is deployed with default settings
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** the role creates or overwrites `~/.config/opencode/opencode.json` from the `opencode.json.j2` template with the values from role variables, with file mode `0600`

#### Scenario: Configuration file reflects variable overrides
- **WHEN** the consumer overrides `ai_model` to `anthropic/claude-sonnet-4-5` and `ai_gcp_project` to `my-project`
- **THEN** the deployed `opencode.json` SHALL contain the overridden model value and the GCP project in `providers.google-vertex.settings.project`

#### Scenario: Instructions list includes org governance files by default
- **WHEN** the role deploys with default `ai_opencode_instructions` value
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["~/.config/opencode/commit.md", "~/.config/opencode/coding-standards.md", ".specify/memory/constitution.md", "AGENTS.md"]`, with global baseline files preceding repository-relative paths

#### Scenario: Instructions list is customizable
- **WHEN** the consumer overrides `ai_opencode_instructions` to `["CUSTOM.md"]`
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["CUSTOM.md"]`

#### Scenario: Configuration directory is created if missing
- **WHEN** the parent directory of `ai_opencode_config_file` does not exist
- **THEN** the role SHALL create the directory structure before deploying the config file

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

#### Scenario: V1-only keys are absent
- **WHEN** the role deploys the configuration file
- **THEN** the deployed `opencode.json` SHALL NOT contain the keys `small_model`, `share`, `options`, `disabled_providers`, `autoupdate`, `permission`, `plugin`, `agent`, or `provider`

### Requirement: Per-agent model variables for independent routing control
The role SHALL provide individual default variables for each OpenCode built-in agent's model assignment: `ai_opencode_agent_build_model` (default: `{{ ai_model }}`), `ai_opencode_agent_plan_model` (default: `{{ ai_model }}`), `ai_opencode_agent_explore_model` (default: `{{ ai_model }}`), and `ai_opencode_agent_general_model` (default: `{{ ai_model }}`). These variables SHALL be referenced by the `ai_opencode_agents` dict and SHALL allow consumers to override individual agent models without replacing the entire agent configuration dict.

#### Scenario: Default agent models resolve to primary model variables
- **WHEN** the consumer does not override any `ai_opencode_agent_*_model` variables
- **THEN** all four agent model variables SHALL resolve to the value of `ai_model`

#### Scenario: Individual agent model override does not affect other agents
- **WHEN** the consumer overrides only `ai_opencode_agent_plan_model` to a Sonnet model
- **THEN** only the `plan` agent's model SHALL change; `build`, `explore`, and `general` SHALL retain their defaults

### Requirement: Plugin deployment list
The role SHALL provide an `ai_opencode_plugins` list variable that is rendered directly as the `"plugins"` array in the deployed `opencode.json`. The default value SHALL be an empty list `[]` while the opencode-metrics plugin is pending V2 migration. Users MAY override this list to add plugins. When the metrics plugin is ported to V2, the default SHALL be restored to include `@mburghardt/opencode-metrics` at the pinned version.

#### Scenario: Default plugins include metrics in npm mode
- **WHEN** the consumer does not override `ai_opencode_plugins` and `ai_opencode_metrics_version` is `"0.3.0"`
- **THEN** the deployed `opencode.json` SHALL contain `"plugins": []`, replacing the previous npm-mode default until the metrics plugin is ported to V2

#### Scenario: Default plugins exclude metrics npm entry in local mode
- **WHEN** the consumer does not override `ai_opencode_plugins` and `ai_opencode_metrics_version` is `"local"`
- **THEN** the deployed `opencode.json` SHALL contain `"plugins": []`

#### Scenario: User removes the default plugin
- **WHEN** the consumer sets `ai_opencode_plugins` to `[]`
- **THEN** the deployed `opencode.json` SHALL contain `"plugins": []`

#### Scenario: User adds plugins alongside the default
- **WHEN** the consumer sets `ai_opencode_plugins` to a list of V2-compatible plugin packages
- **THEN** the deployed `opencode.json` SHALL contain exactly those packages in the `"plugins"` array, with no default metrics entry added

#### Scenario: Plugin list reflects user additions
- **WHEN** the consumer sets `ai_opencode_plugins` to `["@angdrew/opencode-hashline-plugin"]`
- **THEN** the deployed `opencode.json` SHALL contain `"plugins": ["@angdrew/opencode-hashline-plugin"]`

### Requirement: Data-driven compaction settings
The role SHALL provide an `ai_opencode_compaction` dict variable (default: `{auto: true, keep: {tokens: 15000}, buffer: 10000}`) that is rendered directly as the `"compaction"` block in the deployed `opencode.json`. The V2 schema renames V1's `reserved` to `buffer`, adds `keep.tokens` for retained context, and removes `prune`.

#### Scenario: Default compaction matches previous behavior
- **WHEN** the consumer does not override `ai_opencode_compaction`
- **THEN** the deployed `opencode.json` SHALL preserve automatic compaction and the 10000-token reserve using `"compaction": {"auto": true, "keep": {"tokens": 15000}, "buffer": 10000}`

#### Scenario: User tunes compaction
- **WHEN** the consumer overrides `ai_opencode_compaction` to `{"auto": false, "keep": {"tokens": 24000}, "buffer": 16000}`
- **THEN** the deployed `opencode.json` SHALL contain the overridden compaction values

### Requirement: Restart the shared background service after changes
The role SHALL provide `ai_opencode_restart_service` (default: `true`) and SHALL restart the OpenCode shared background service after it changes the installation or configuration. The restart SHALL run only when a service is already running, so the role never starts a stopped service. A restarted service SHALL receive `ai_opencode_server_env`.

#### Scenario: Configuration change restarts a running service
- **WHEN** `configure_opencode` changes a managed file and the shared service is running
- **THEN** the role SHALL restart the service once at the end of the play, with `ai_opencode_server_env` in its environment

#### Scenario: Installation change restarts a running service
- **WHEN** the npm installation of `@opencode/cli` changes and the shared service is running
- **THEN** the role SHALL restart the service so the new binary is used

#### Scenario: Stopped service is not started
- **WHEN** no shared service is running
- **THEN** the role SHALL NOT start or restart one

#### Scenario: Restart can be disabled
- **WHEN** the consumer sets `ai_opencode_restart_service` to `false`
- **THEN** the role SHALL NOT query or restart the shared service

#### Scenario: Launcher and handler share the server environment
- **WHEN** the consumer overrides `ai_trusted_github_orgs`
- **THEN** both the launcher script and a role-driven restart SHALL use the same `TRUSTED_GITHUB_ORGS` value

### Requirement: Launcher renders the shared server environment
The launcher script SHALL render its environment exports from `ai_opencode_server_env` and SHALL NOT export `GCP_PROJECT` or `VERTEX_LOCATION`.

#### Scenario: Launcher uses the shared environment dict
- **WHEN** the role deploys the launcher script
- **THEN** every entry of `ai_opencode_server_env` SHALL be exported by the script

### Requirement: Verify the OpenCode launcher after installation
After installing `@opencode/cli`, the role SHALL report every `opencode` and `opencode2` launcher found on `PATH`. When `opencode` does not resolve, the role SHALL remove dangling `opencode` symlinks and SHALL recreate `opencode` as a symlink to the `opencode2` alias when that alias resolves. When it still does not resolve, the role SHALL fail with the discovered launcher paths rather than deploy a launcher that cannot start. The launcher script SHALL execute `opencode`.

#### Scenario: Dangling launcher is repaired
- **WHEN** `opencode` does not resolve because an earlier `PATH` entry contains a dangling `opencode` symlink
- **THEN** the role SHALL remove the dangling symlink and verify that `opencode` resolves afterwards

#### Scenario: Missing launcher is recreated from the alias
- **WHEN** `opencode` does not resolve and `opencode2` resolves
- **THEN** the role SHALL create `opencode` as a symlink to `opencode2` in the same directory

#### Scenario: Unresolvable launcher fails the play
- **WHEN** `opencode` still does not resolve after removing dangling symlinks
- **THEN** the play SHALL fail with the discovered `opencode` and `opencode2` paths

#### Scenario: Launcher executes the opencode command
- **WHEN** the role deploys the launcher script
- **THEN** the script SHALL execute `opencode` with forwarded arguments

### Requirement: Permission rules as ordered array
The role SHALL define `_ai_opencode_permissions_default` as ordered `{action, resource, effect}` rules using `shell` instead of `bash`. The `ai_opencode_permissions` override list SHALL default to `[]`. Merged permissions SHALL concatenate defaults followed by user rules, giving users last-match precedence and preserving existing default effects, including external-directory approvals.

#### Scenario: Default permissions use V2 array format
- **WHEN** the role deploys with default permissions
- **THEN** the `permissions` array in the deployed `opencode.json` SHALL contain objects with `action`, `resource`, and `effect` keys

#### Scenario: Shell action name is used instead of bash
- **WHEN** the role deploys with default permissions
- **THEN** all permission rules that controlled shell commands SHALL use `action: "shell"` (not `action: "bash"`)

#### Scenario: External directory approvals preserve V1 behavior
- **WHEN** the role deploys with default permissions
- **THEN** an `{action: "external_directory", resource: "*", effect: "ask"}` rule SHALL precede the existing temporary-directory allow and system-path deny exceptions

#### Scenario: User appends override rules
- **WHEN** the consumer sets `ai_opencode_permissions` to `[{action: "shell", resource: "poetry *", effect: "allow"}]`
- **THEN** the deployed `opencode.json` SHALL contain the default rules followed by the user's rule, and `poetry *` commands SHALL be allowed because the user rule appears last

#### Scenario: User overrides a default rule
- **WHEN** the consumer sets `ai_opencode_permissions` to `[{action: "shell", resource: "git push *", effect: "allow"}]`
- **THEN** the user's `allow` rule for `git push *` SHALL appear after the default `ask` rule, making `git push *` allowed (last match wins)

### Requirement: V2 provider configuration schema
The role SHALL use V2 provider configuration keys: `package` (not `npm`), `settings` (not `options`). The provider ID `google-vertex-anthropic` SHALL NOT be used; `google-vertex` SHALL be used instead. The `google-vertex` provider SHALL include `settings.project` and `settings.location` sourced from `ai_gcp_project` and `ai_vertex_location` variables, replacing the previous env-var-based approach in the wrapper script.

#### Scenario: Ollama provider uses V2 keys
- **WHEN** the role deploys with default providers
- **THEN** the Ollama provider entry SHALL use `settings.baseURL` (not `options.baseURL`) and SHALL NOT contain an `npm` key

#### Scenario: Google Vertex provider replaces google-vertex-anthropic
- **WHEN** the role deploys with default providers including Vertex
- **THEN** the provider key SHALL be `google-vertex` (not `google-vertex-anthropic`) and SHALL include `settings.project` and `settings.location`

#### Scenario: Wrapper script no longer exports GCP env vars
- **WHEN** the `google-vertex` provider is configured
- **THEN** the wrapper script SHALL NOT export `GCP_PROJECT` or `VERTEX_LOCATION` environment variables (these are now in provider settings)

### Requirement: V1-only variables removed
The role SHALL NOT define or use the variables `ai_small_model`, `ai_opencode_options`, or `ai_opencode_disabled_providers`. These have no V2 equivalent.

#### Scenario: ai_small_model is not defined
- **WHEN** examining `defaults/main.yml`
- **THEN** `ai_small_model` SHALL NOT be present

#### Scenario: ai_opencode_disabled_providers is not defined
- **WHEN** examining `defaults/main.yml`
- **THEN** `ai_opencode_disabled_providers` SHALL NOT be present

#### Scenario: ai_opencode_options is not defined
- **WHEN** examining `defaults/main.yml`
- **THEN** `ai_opencode_options` SHALL NOT be present

### Requirement: Vertex service-account credentials file
The role SHALL provide an `ai_vertex_credentials_file` variable (default: `""`) with the path to a protected GCP service-account JSON key. When set, the role SHALL inject `GOOGLE_APPLICATION_CREDENTIALS` with the tilde-expanded path into the server environment used by both the launcher and the role-driven service restart, merged with `ai_opencode_server_env` so consumer entries are preserved. When empty, the environment SHALL be unchanged; the key file is never read by the role.

#### Scenario: Launcher exports the credentials path when configured
- **WHEN** the consumer sets `ai_vertex_credentials_file` to `~/.config/vertex/service-account.json`
- **THEN** the deployed launcher script SHALL export `GOOGLE_APPLICATION_CREDENTIALS` with the path expanded to `ai_user_home_dir`, and every entry of `ai_opencode_server_env` SHALL still be exported

#### Scenario: Launcher omits the variable when not configured
- **WHEN** `ai_vertex_credentials_file` is empty
- **THEN** the launcher script SHALL NOT export `GOOGLE_APPLICATION_CREDENTIALS`

#### Scenario: Service restart receives the credentials path
- **WHEN** `ai_vertex_credentials_file` is set and the role restarts a running shared service
- **THEN** the restarted service SHALL receive `GOOGLE_APPLICATION_CREDENTIALS` alongside every `ai_opencode_server_env` entry

#### Scenario: Consumer server environment entries are preserved
- **WHEN** the consumer overrides `ai_opencode_server_env` and sets `ai_vertex_credentials_file`
- **THEN** both the consumer entries and `GOOGLE_APPLICATION_CREDENTIALS` SHALL reach the launcher and the restarted service

#### Scenario: Credentials path is quoted and only the path is rendered
- **WHEN** the credentials path contains spaces or shell metacharacters
- **THEN** the launcher export SHALL be safely quoted, and the key file contents SHALL NOT appear in any deployed file
