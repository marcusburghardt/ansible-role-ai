## 1. Add New Variables to Defaults

- [x] 1.1 Add per-agent model variables (`ai_opencode_agent_build_model`, `ai_opencode_agent_plan_model`, `ai_opencode_agent_explore_model`, `ai_opencode_agent_general_model`) to `defaults/main.yml` with defaults referencing `ai_model` / `ai_small_model`. Add `ai_opencode_agents` dict that aggregates them. Verify by inspecting the file and confirming Jinja references are syntactically correct.
- [x] 1.2 Add `ai_opencode_plugins` list variable (default: `[]`) to `defaults/main.yml`. Verify the variable is present and defaults to an empty list.
- [x] 1.3 Add `ai_opencode_compaction` dict variable (default: `{auto: true, prune: true, reserved: 10000}`) to `defaults/main.yml`. Verify values match the current hardcoded compaction block in the template.

## 2. Update Configuration Template

- [x] 2.1 Add `"plugin": {{ ai_opencode_plugins | to_json }}` to `templates/opencode.json.j2`. Verify the rendered output contains `"plugin": []` with default values.
- [x] 2.2 Add `"agent": {{ ai_opencode_agents | to_json }}` to `templates/opencode.json.j2`. Verify the rendered output contains the agent block with model assignments matching defaults.
- [x] 2.3 Replace the hardcoded `"compaction"` block in `templates/opencode.json.j2` with `{{ ai_opencode_compaction | to_json }}`. Verify the rendered output is identical to the previous hardcoded values.

## 3. Update Documentation

- [x] 3.1 Document `ai_opencode_agent_build_model`, `ai_opencode_agent_plan_model`, `ai_opencode_agent_explore_model`, `ai_opencode_agent_general_model`, `ai_opencode_agents`, `ai_opencode_plugins`, and `ai_opencode_compaction` in the variables table in `README.md`. Include types, defaults, and descriptions.
- [x] 3.2 Add a "Cost Optimization" section to `README.md` with an example playbook snippet for Vertex users showing three-tier model routing and optional plugin configuration. Credit the [OpenCode Token Efficiency Configuration Guide](https://gist.github.com/jflowers/c54514358abf892df84d5e6b8e7d7772) by jflowers as the reference source.

## 4. Update Spec

- [x] 4.1 Update `openspec/specs/opencode-configuration/spec.md` to include requirements and scenarios for agent routing, plugin deployment, and data-driven compaction. Verify by running `openspec validate --change token-efficiency-config`.

## 5. Verification

- [x] 5.1 Run the role's smoke test (`tests/test.yml`) to confirm the template renders without errors and the configure_opencode task completes successfully.
