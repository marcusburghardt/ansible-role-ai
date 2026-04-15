## Why

OpenCode supports 75+ LLM providers, but the role currently defaults to Google Vertex
Anthropic -- a paid provider that requires GCP credentials. Users without paid provider
access or GCP projects get a non-functional setup out of the box. Ollama enables running
open models locally at zero cost, giving every user an immediately working OpenCode
experience while still allowing paid providers alongside it.

## What Changes

- **Add Ollama lifecycle management**: New `install_ollama` task installs Ollama via the
  official install script and manages the systemd service. New `configure_ollama` task
  pulls user-selected models from a curated list. Both tasks are enabled by default.
- **Curated open model list**: Ship a default list of recommended open models with
  `enabled` flags, defaulting to `qwen3:8b` as the only enabled model (runs on virtually
  any modern hardware). Users override the list to enable larger models for beefier
  hardware.
- **Refactor OpenCode provider configuration to be data-driven**: **BREAKING** -- Replace
  the hardcoded `google-vertex-anthropic` provider block in `opencode.json.j2` with a
  fully templated block driven by a new `ai_opencode_providers` variable. Both Ollama and
  Vertex are configured by default; users can add, remove, or customize providers by
  overriding this single variable.
- **New variable for OpenCode-visible Ollama models**: A separate
  `ai_opencode_ollama_models` variable controls which pulled models appear in the OpenCode
  provider config, independent of the pull list.
- **Default model changes**: **BREAKING** -- `ai_model` and `ai_small_model` default to
  `ollama/qwen3:8b` instead of Vertex Anthropic models. Users with paid providers override
  these in their playbooks.
- **Conditional wrapper script**: The `skynet` wrapper script only exports GCP environment
  variables when the `google-vertex-anthropic` provider is configured, eliminating noise
  for Ollama-only users.
- **Data-driven disabled providers**: Replace the hardcoded `disabled_providers` list with
  a new `ai_opencode_disabled_providers` variable (defaults to empty).

## Capabilities

### New Capabilities

- `ollama-management`: Covers Ollama installation, systemd service lifecycle (enabled vs
  started), and model pulling from a curated list with graceful skipping when the service
  is not running.

### Modified Capabilities

- `opencode-configuration`: The provider block in `opencode.json.j2` becomes data-driven
  via `ai_opencode_providers`. The wrapper script becomes conditional based on configured
  providers. The `disabled_providers` list becomes variable-driven.
- `tool-installation`: New `install_ollama` entry added to `ai_tasks` (enabled by default).
  Follows existing version/idempotency patterns but uses the official install script
  instead of a package manager.

## Impact

- **defaults/main.yml**: New variables for Ollama (`ai_ollama_*`), new provider variables
  (`ai_opencode_providers`, `ai_opencode_ollama_models`, `ai_opencode_disabled_providers`),
  changed defaults for `ai_model` and `ai_small_model`, two new entries in `ai_tasks`.
- **templates/opencode.json.j2**: Provider block and disabled_providers list become
  Jinja-rendered from variables instead of hardcoded JSON.
- **templates/ai_agent_script.sh.j2**: GCP env var exports become conditional on Vertex
  provider presence.
- **New files**: `tasks/install_ollama.yml`, `tasks/configure_ollama.yml`,
  `vars/install_ollama.yml`, `vars/configure_ollama.yml`.
- **Existing users**: Users with playbooks that rely on the current Vertex-centric defaults
  must update their playbooks to either override `ai_model`/`ai_small_model` back to
  Vertex models or override `ai_opencode_providers` to match their setup. The README
  should document migration guidance.
- **Dependencies**: No new Ansible collection or Python dependencies. Ollama install script
  requires `curl` and internet access.
