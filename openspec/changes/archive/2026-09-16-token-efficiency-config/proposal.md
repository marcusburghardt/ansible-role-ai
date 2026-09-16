## Why

OpenCode sessions using paid API providers (e.g., Google Vertex with Anthropic models) can consume significant tokens on tasks that don't require the most capable model. The role currently offers `ai_model` and `ai_small_model` as the only model controls, with no per-agent routing, no plugin support, and hardcoded compaction settings. Users who want to optimize cost must manually edit the deployed `opencode.json` after the role runs, which is fragile and not idempotent.

This change adds data-driven configuration for agent model routing, plugin deployment, and compaction tuning -- enabling cost-optimized OpenCode sessions through the role's standard variable override mechanism. The design is informed by the [OpenCode Token Efficiency Configuration Guide](https://gist.github.com/jflowers/c54514358abf892df84d5e6b8e7d7772) by jflowers.

## What Changes

- Add per-agent model variables (`ai_opencode_agent_build_model`, `ai_opencode_agent_plan_model`, `ai_opencode_agent_explore_model`, `ai_opencode_agent_general_model`) for independent routing control.
- Add `ai_opencode_agents` dict that aggregates per-agent model variables and is rendered as the `"agent"` block in `opencode.json`.
- Add `ai_opencode_plugins` list (default empty) rendered as the `"plugin"` block in `opencode.json`, enabling opt-in plugin deployment.
- Replace the hardcoded `"compaction"` block in `opencode.json.j2` with an `ai_opencode_compaction` dict variable, preserving current defaults while making them tunable.
- Document all new variables in `README.md`, including a cost optimization section with example playbook snippets and credit to the reference guide.

## Capabilities

### New Capabilities

None. All changes extend the existing opencode-configuration capability.

### Modified Capabilities

- `opencode-configuration`: Adding requirements for agent model routing (per-agent model variables and the `agent` config block), plugin deployment (`plugin` config block), and data-driven compaction settings.

## Impact

- **Files modified**: `defaults/main.yml`, `templates/opencode.json.j2`, `README.md`, `openspec/specs/opencode-configuration/spec.md`
- **Backward compatibility**: Full. Default values produce identical `opencode.json` output for Ollama users. Vertex users see an `agent` block that routes all agents to the same model they already use. `plugin: []` and `compaction` with current defaults are no-ops.
- **Dependencies**: None. No new Ansible modules, no new role dependencies.
- **Breaking changes**: None.
