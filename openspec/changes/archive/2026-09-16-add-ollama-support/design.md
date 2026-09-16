## Context

The role currently defaults to Google Vertex Anthropic as the sole configured provider
in `opencode.json.j2`. The provider block, disabled providers list, and wrapper script
environment variables are all hardcoded to this single provider. Users without GCP
credentials get a non-functional setup.

Ollama is a popular open-source tool for running LLMs locally. It installs as a systemd
service on Linux, exposes an OpenAI-compatible API at `localhost:11434`, and manages model
downloads via `ollama pull`. OpenCode supports Ollama through the
`@ai-sdk/openai-compatible` npm package with a custom provider entry.

The role already has a well-established dispatcher pattern (`ai_tasks` list with
`enabled`/`name` entries) and follows consistent conventions for variable naming (`ai_`
prefix), task naming (`{{ role_name }} | {{ task.name }} | <description>`), and per-task
variable files.

## Goals / Non-Goals

**Goals:**
- Every user gets a working OpenCode setup out of the box, without paid credentials.
- Ollama full lifecycle management: install, service control, model pulling.
- Multi-provider support: users can configure any combination of providers.
- The `opencode.json` template becomes fully data-driven -- no hardcoded provider blocks.
- Existing patterns (dispatcher, variable naming, task naming) are preserved.

**Non-Goals:**
- GPU driver installation or CUDA setup (system-level concern outside this role).
- Ollama configuration tuning (context size, GPU layers, etc.) -- users configure Ollama
  directly for advanced settings.
- Supporting Ollama on macOS or Windows (this role targets Linux per `meta/main.yml`).
- Auto-detecting available hardware to choose model sizes -- users choose via variables.

## Decisions

### D1: Multi-method Ollama installation with OS-aware auto-detection

**Decision**: Prefer native OS packages (dnf/apt) when available, fall back to the
official install script on distros without Ollama packages. Controlled by
`ai_ollama_install_method` (default: `auto`) following the same pattern as Cursor's
`ai_cursor_install_method`.

**Rationale**: Native packages integrate with the system's package manager (tracked
dependencies, standard updates via `dnf update`, clean uninstall). The install script
bypasses all of this -- it downloads a binary tarball and manually creates systemd units.
On distros like Fedora where `dnf install ollama` works, the package manager is the
correct tool. The script remains as a fallback for distros without native packages.

**Alternatives considered**:
- *Install script only (original approach)*: Works everywhere but bypasses system package
  management entirely. Binary goes to `/usr/local/bin/` instead of `/usr/bin/`, systemd
  unit is manually created instead of package-managed.
- *Package only*: Cleanest but fails on distros without Ollama in their repos.

**Implementation**: A `_ollama_method_map` in `vars/install_ollama.yml` maps OS families
to install methods (RedHat: `package`, Debian: `package`). The `auto` method resolves via
this map with `script` as the default fallback. The user can override with
`ai_ollama_install_method: script` (or `package`) to force a specific method. The
idempotency check uses `which ollama` to handle both `/usr/bin/ollama` (package) and
`/usr/local/bin/ollama` (script) locations.

### D2: Two separate tasks for install and configure

**Decision**: Split Ollama into `install_ollama` (install + service management) and
`configure_ollama` (model pulling) as separate `ai_tasks` entries.

**Rationale**: Model pulling is a long-running network operation (multi-GB downloads). Users
may want to run `install_ollama` once and then toggle `configure_ollama` off for subsequent
playbook runs where they do not want to wait for model state checks. The dispatcher pattern
supports this naturally.

**Alternatives considered**:
- *Single task*: Simpler to reason about, but couples fast operations (install, service
  start) with slow ones (model pulling). The Cursor task is a single task, but Cursor
  downloads a single binary -- Ollama may pull multiple models.

### D3: Service lifecycle defaults -- started but not enabled

**Decision**: Default to `ai_ollama_service_state: started` and
`ai_ollama_service_enabled: false`.

**Rationale**: This gives users Ollama during the session without assuming it should
persist across reboots, where it would consume memory/GPU resources. The
`ansible.builtin.systemd_service` module supports both settings independently.

### D4: Data-driven provider configuration (Path B)

**Decision**: Replace the hardcoded provider block in `opencode.json.j2` with
`{{ ai_opencode_providers | to_json }}`. A single `ai_opencode_providers` dict in
`defaults/main.yml` is the sole source of truth for the provider block.

**Rationale**: One variable controls one config block. No dual system, no hardcoded
sections alongside variable-driven sections. Users override `ai_opencode_providers` to
add, remove, or customize any provider.

**Alternatives considered**:
- *Path A (old vars + new dict)*: Keep the hardcoded Vertex block and add
  `ai_opencode_providers` for additional providers. Simpler migration but creates two
  systems for the same config block -- confusing for users.

**Implementation**: The default `ai_opencode_providers` dict includes both `ollama` and
`google-vertex-anthropic`. The Ollama entry uses a Jinja reference
(`{{ ai_opencode_ollama_models }}`) for its models sub-key, which Ansible resolves at
template rendering time. This keeps the pull list (`ai_ollama_models`) separate from the
OpenCode-visible list (`ai_opencode_ollama_models`).

### D5: Separate variables for pulled models vs OpenCode-visible models

**Decision**: `ai_ollama_models` controls what gets pulled onto the machine.
`ai_opencode_ollama_models` controls what appears in the OpenCode provider config.

**Rationale**: Users may pull models for experimentation or other tools without wanting
all of them in OpenCode's model list. Keeping these separate avoids cluttering the
OpenCode UI with unused models.

### D6: Default model set -- qwen3:8b only

**Decision**: Default `ai_ollama_models` enables only `qwen3:8b`. Default
`ai_opencode_ollama_models` registers only `qwen3:8b`.

**Rationale**: The `qwen3:8b` model runs on virtually any modern machine (~5 GB VRAM or
CPU-only), has tool-calling support (required for OpenCode's agentic features), and
provides reasonable coding assistance. Larger models are available in the curated list
but disabled by default.

### D7: Conditional wrapper script

**Decision**: The `ai_agent_script.sh.j2` template conditionally exports GCP environment
variables only when `google-vertex-anthropic` is present in `ai_opencode_providers`.

**Rationale**: Ollama-only users should not see irrelevant GCP exports in their wrapper
script. The Jinja `{% if %}` block checks the providers dict at template rendering time.

### D8: Default ai_model and ai_small_model point to Ollama

**Decision**: Change defaults to `ai_model: "ollama/qwen3:8b"` and
`ai_small_model: "ollama/qwen3:8b"`.

**Rationale**: Aligns with the goal of a zero-cost out-of-box experience. Users with paid
providers override these in their playbooks.

## Risks / Trade-offs

- **[Breaking change for existing users]** → Users relying on the current Vertex-centric
  defaults must update their playbooks. Mitigation: document migration in README, provide
  example playbook snippets for Vertex-only and mixed setups.

- **[Ollama install script is a third-party dependency]** → The script URL could change or
  break. Mitigation: the script is only used as a fallback on distros without native
  packages. On RedHat/Debian families, the native package manager is used instead. For
  the fallback case, the `creates:` guard ensures failures only affect first-run installs.

- **[Model quality varies]** → Open models are less capable than frontier paid models.
  Mitigation: the default `qwen3:8b` is chosen for broad compatibility, not peak
  performance. Users who need better quality can enable larger models or use paid
  providers. Both are available simultaneously.

- **[Disk space for models]** → Even `qwen3:8b` uses ~5 GB of disk. Pulling multiple
  models can consume significant space. Mitigation: only one model enabled by default.
  The curated list makes the trade-off visible.

- **[Jinja reference in defaults]** → The `{{ ai_opencode_ollama_models }}` reference
  inside `ai_opencode_providers` is resolved at render time, which works correctly but
  may surprise users who inspect `defaults/main.yml` and expect pure static YAML.
  Mitigation: add comments explaining the lazy evaluation.
