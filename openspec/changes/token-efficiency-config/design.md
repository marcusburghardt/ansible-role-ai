## Context

The OpenCode configuration template (`templates/opencode.json.j2`) currently hardcodes the `compaction` block and has no `agent` or `plugin` blocks. The `defaults/main.yml` provides `ai_model` and `ai_small_model` as the only model controls. See proposal.md for motivation and the referenced [token efficiency guide](https://gist.github.com/jflowers/c54514358abf892df84d5e6b8e7d7772) by jflowers for background.

The role already uses a data-driven pattern for providers (`ai_opencode_providers` dict rendered via `to_json`), options (`ai_opencode_options` dict), and disabled providers (`ai_opencode_disabled_providers` list). The new variables follow the same pattern.

## Goals / Non-Goals

**Goals:**

- Enable per-agent model routing through individual variables that can be overridden independently
- Support opt-in plugin deployment via a list variable
- Make compaction settings tunable via a dict variable
- Preserve backward compatibility: default output is identical for Ollama users
- Follow the existing data-driven rendering pattern used by providers and options

**Non-Goals:**

- Deploying plugin-specific configuration files (e.g., `dcp.jsonc`) -- out of scope, user-managed
- Defaulting any plugins to enabled -- the role stays neutral on plugin choices
- Providing MCP server configuration -- separate concern
- Validating model IDs against available providers -- OpenCode handles that at runtime

## Decisions

### Decision 1: Two-level agent model control (individual variables + aggregate dict)

**Choice**: Provide four `ai_opencode_agent_*_model` scalar variables that feed into an `ai_opencode_agents` dict.

**Rationale**: Users frequently change individual agent models. Scalar variables let them override a single agent without rewriting the entire dict. The dict provides full control for future agent config knobs beyond `model`.

**Alternatives considered**:
- *Dict only*: Requires overriding the entire dict to change one agent's model. Poor ergonomics for the most common use case.
- *Scalars only*: No path to support future non-model agent configuration.

### Decision 2: Default agent routing uses ai_model / ai_small_model

**Choice**: `build` defaults to `{{ ai_model }}`, all others default to `{{ ai_small_model }}`.

**Rationale**: For Ollama users where both variables are the same model, this is a no-op. For Vertex users who set different primary and small models, routing activates automatically. Users who want three-tier routing (e.g., Opus / Sonnet / Haiku) override individual agent variables.

**Alternatives considered**:
- *All agents default to ai_model*: Misses the cost optimization opportunity for users who already set distinct `ai_model` / `ai_small_model`.
- *Empty dict by default*: Routing doesn't activate when users change `ai_model` / `ai_small_model` -- requires explicit opt-in to a feature that should work by convention.

### Decision 3: Plugins as an empty list, not conditional rendering

**Choice**: Always render `"plugin": []` in the config, even when empty.

**Rationale**: Consistent with how `disabled_providers` is rendered (always present, even if empty). Avoids conditional Jinja logic in the template. An empty array is a valid no-op for OpenCode.

### Decision 4: Compaction as a dict variable replacing hardcoded block

**Choice**: Move `compaction` from hardcoded template values to `ai_opencode_compaction` dict with the same defaults.

**Rationale**: Follows the same pattern as `ai_opencode_options` and `ai_opencode_providers`. Users can tune `reserved` tokens, disable `prune`, or turn off `auto` compaction from their playbook without forking the template. Default output is byte-identical to current behavior.

## Risks / Trade-offs

- **[Risk] Agent block present for all users, even when all models are the same** -- Minimal. The block is small, valid, and explicitly documents the routing even when it's a no-op. No mitigation needed.
- **[Risk] Jinja cross-references in defaults** -- `ai_opencode_agents` references `ai_opencode_agent_*_model` variables, which in turn reference `ai_model` / `ai_small_model`. Ansible resolves these lazily at template time. This is the same pattern used by `ai_opencode_providers.ollama.models` referencing `ai_opencode_ollama_models`. Well-tested.
- **[Risk] Users override ai_opencode_agents dict directly, losing per-agent variable resolution** -- Expected behavior. If a user overrides the entire dict, they own the full configuration. Documented in README.
