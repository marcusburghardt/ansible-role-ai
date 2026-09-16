## MODIFIED Requirements

### Requirement: Deploy OpenCode configuration file from template
The role SHALL deploy the OpenCode configuration file to `ai_opencode_config_file`
(default: `~/.config/opencode/opencode.json`) using a Jinja2 template. The template SHALL
incorporate variables for `model`, `small_model`, and a variable-driven instructions file
list (`ai_opencode_instructions`). The provider block SHALL be rendered entirely from the
`ai_opencode_providers` variable using `{{ ai_opencode_providers | to_json }}` with no
hardcoded provider entries. The disabled providers list SHALL be rendered from the
`ai_opencode_disabled_providers` variable using `{{ ai_opencode_disabled_providers | to_json }}`.
Permissions, compaction settings, and watcher configuration remain in the template as
static content.

#### Scenario: Configuration file is deployed with default settings
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** the role creates or overwrites `~/.config/opencode/opencode.json` from the
  `opencode.json.j2` template with the values from role variables, with file mode `0600`

#### Scenario: Configuration file reflects variable overrides
- **WHEN** the consumer overrides `ai_model` to `google-vertex-anthropic/claude-opus-4-6@default`
- **THEN** the deployed `opencode.json` SHALL contain the overridden model value

#### Scenario: Provider block reflects ai_opencode_providers variable
- **WHEN** `ai_opencode_providers` contains both `ollama` and `google-vertex-anthropic`
  entries
- **THEN** the deployed `opencode.json` SHALL contain a `provider` block with both
  providers and their respective model and option configurations

#### Scenario: Provider block reflects Ollama-only configuration
- **WHEN** the consumer overrides `ai_opencode_providers` to contain only the `ollama`
  entry
- **THEN** the deployed `opencode.json` SHALL contain a `provider` block with only the
  Ollama provider and no `google-vertex-anthropic` entry

#### Scenario: Disabled providers list reflects variable
- **WHEN** `ai_opencode_disabled_providers` is set to `["openai"]`
- **THEN** the deployed `opencode.json` SHALL contain
  `"disabled_providers": ["openai"]`

#### Scenario: Empty disabled providers list
- **WHEN** `ai_opencode_disabled_providers` is set to `[]`
- **THEN** the deployed `opencode.json` SHALL contain `"disabled_providers": []`

#### Scenario: Instructions list includes org governance files by default
- **WHEN** the role deploys with default `ai_opencode_instructions` value
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain
  `["~/.config/opencode/commit.md", "~/.config/opencode/coding-standards.md", ".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]`,
  with global baseline files preceding repository-relative paths

#### Scenario: Instructions list is customizable
- **WHEN** the consumer overrides `ai_opencode_instructions` to `["CUSTOM.md"]`
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain
  `["CUSTOM.md"]`

#### Scenario: Configuration directory is created if missing
- **WHEN** the parent directory of `ai_opencode_config_file` does not exist
- **THEN** the role SHALL create the directory structure before deploying the config file

### Requirement: Deploy AI agent wrapper script from template
The role SHALL deploy a wrapper script to `ai_user_scripts_dir/ai_agent_script_name`
using a Jinja2 template. The script SHALL conditionally export GCP environment variables
(`GCP_PROJECT`, `VERTEX_LOCATION`) only when `google-vertex-anthropic` is present as a
key in `ai_opencode_providers`. The script SHALL always export a `TRUSTED_GITHUB_ORGS`
variable (comma-separated list from `ai_trusted_github_orgs`) and launch `opencode`.

#### Scenario: Wrapper script is deployed
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** the role creates or overwrites the wrapper script at
  `{{ ai_user_scripts_dir }}/{{ ai_agent_script_name }}` with mode `0750`

#### Scenario: Wrapper script includes GCP variables when Vertex is configured
- **WHEN** `ai_opencode_providers` contains a `google-vertex-anthropic` key and
  `ai_gcp_project` is set to `my-gcp-project`
- **THEN** the script SHALL contain `export GCP_PROJECT="my-gcp-project"` and
  `export VERTEX_LOCATION="us-central1"`

#### Scenario: Wrapper script omits GCP variables when Vertex is not configured
- **WHEN** `ai_opencode_providers` does not contain a `google-vertex-anthropic` key
- **THEN** the script SHALL NOT contain `export GCP_PROJECT` or `export VERTEX_LOCATION`
  lines

#### Scenario: Wrapper script exports trusted GitHub organizations
- **WHEN** `ai_trusted_github_orgs` is set to `["myorg", "partnerorg"]`
- **THEN** the wrapper script SHALL contain
  `export TRUSTED_GITHUB_ORGS="myorg,partnerorg"`

## ADDED Requirements

### Requirement: OpenCode-visible Ollama models variable
The role SHALL provide an `ai_opencode_ollama_models` variable that defines which Ollama
models appear in the OpenCode provider configuration. This variable SHALL be a dict
mapping model names to their display configuration (at minimum a `name` key for the
display name). This variable is independent of `ai_ollama_models` (which controls what
is pulled) and is referenced by the Ollama entry in `ai_opencode_providers`.

#### Scenario: Default OpenCode-visible Ollama models
- **WHEN** `ai_opencode_ollama_models` uses its default value
- **THEN** the Ollama provider block in the deployed `opencode.json` SHALL list `qwen3:8b`
  with display name `Qwen 3 8B (local)`

#### Scenario: User adds models to OpenCode visibility
- **WHEN** the user overrides `ai_opencode_ollama_models` to include both `qwen3:8b` and
  `qwen3:32b`
- **THEN** the Ollama provider block in the deployed `opencode.json` SHALL list both
  models with their respective display names

### Requirement: Data-driven provider catalog variable
The role SHALL provide an `ai_opencode_providers` variable as a dict that maps provider
IDs to their full configuration (including `npm`, `name`, `options`, and `models` keys as
applicable). The default value SHALL include both `ollama` (with `npm`, `name`,
`options.baseURL`, and models from `ai_opencode_ollama_models`) and
`google-vertex-anthropic` (with model-specific options). Users SHALL be able to override
this variable entirely to add, remove, or customize providers.

#### Scenario: Default providers include Ollama and Vertex
- **WHEN** `ai_opencode_providers` uses its default value
- **THEN** the variable SHALL contain entries for both `ollama` and
  `google-vertex-anthropic`

#### Scenario: User configures Ollama-only setup
- **WHEN** the user overrides `ai_opencode_providers` to contain only the `ollama` entry
- **THEN** the deployed `opencode.json` SHALL contain only the Ollama provider in its
  `provider` block

#### Scenario: User adds a custom provider
- **WHEN** the user overrides `ai_opencode_providers` to include a `lmstudio` entry with
  `npm`, `name`, `options.baseURL`, and `models`
- **THEN** the deployed `opencode.json` SHALL contain the `lmstudio` provider alongside
  any other configured providers

### Requirement: Data-driven disabled providers variable
The role SHALL provide an `ai_opencode_disabled_providers` variable as a list of provider
IDs that OpenCode should not auto-detect. The default value SHALL be an empty list.

#### Scenario: No providers disabled by default
- **WHEN** `ai_opencode_disabled_providers` uses its default value
- **THEN** the deployed `opencode.json` SHALL contain `"disabled_providers": []`

#### Scenario: User disables specific providers
- **WHEN** `ai_opencode_disabled_providers` is set to `["openai", "gemini"]`
- **THEN** the deployed `opencode.json` SHALL contain
  `"disabled_providers": ["openai", "gemini"]`

### Requirement: Default model selection points to Ollama
The default values for `ai_model` and `ai_small_model` SHALL be `ollama/qwen3:8b`,
ensuring a zero-cost out-of-box experience. Users with paid providers SHALL override
these in their playbooks.

#### Scenario: Default model is Ollama
- **WHEN** `ai_model` and `ai_small_model` use their default values
- **THEN** both SHALL be `ollama/qwen3:8b`

#### Scenario: User overrides to paid provider
- **WHEN** the user sets `ai_model` to
  `google-vertex-anthropic/claude-opus-4-6@default`
- **THEN** the deployed `opencode.json` SHALL use the overridden model value
