## 1. Ollama Task Files and Variables

- [x] 1.1 Create `vars/install_ollama.yml` (can be empty placeholder to satisfy dispatcher)
- [x] 1.2 Create `vars/configure_ollama.yml` (can be empty placeholder to satisfy dispatcher)
- [x] 1.3 Create `tasks/install_ollama.yml` -- download official install script, execute with `become: true` and `creates: /usr/local/bin/ollama` guard, manage systemd service using `ai_ollama_service_state` and `ai_ollama_service_enabled`
- [x] 1.4 Create `tasks/configure_ollama.yml` -- check if Ollama service is running, loop through `ai_ollama_models` where `enabled` is true, run `ollama pull` for each, skip gracefully with debug message when service is not running

## 2. Update defaults/main.yml

- [x] 2.1 Add `install_ollama` and `configure_ollama` entries to `ai_tasks` (both `enabled: true`), positioned after `install_dependencies` and before `install_opencode`
- [x] 2.2 Add Ollama service variables: `ai_ollama_service_enabled` (default: `false`) and `ai_ollama_service_state` (default: `started`)
- [x] 2.3 Add curated model list variable `ai_ollama_models` with `qwen3:8b` enabled by default and `qwen3:32b`, `devstral`, `qwen3-coder:a3b`, `llama3.1:8b` disabled
- [x] 2.4 Add `ai_opencode_ollama_models` variable with `qwen3:8b` mapped to display name `Qwen 3 8B (local)`
- [x] 2.5 Add `ai_opencode_providers` variable containing both `ollama` (with `npm`, `name`, `options.baseURL`, and models from `ai_opencode_ollama_models`) and `google-vertex-anthropic` (with thinking options for `claude-opus-4-6@default`)
- [x] 2.6 Add `ai_opencode_disabled_providers` variable (default: `[]`)
- [x] 2.7 Change `ai_model` default from `google-vertex-anthropic/claude-opus-4-6@default` to `ollama/qwen3:8b`
- [x] 2.8 Change `ai_small_model` default from `anthropic/claude-sonnet-4-5` to `ollama/qwen3:8b`

## 3. Refactor OpenCode Configuration Template

- [x] 3.1 Update `templates/opencode.json.j2` -- replace hardcoded `provider` block with `{{ ai_opencode_providers | to_json }}`
- [x] 3.2 Update `templates/opencode.json.j2` -- replace hardcoded `disabled_providers` list with `{{ ai_opencode_disabled_providers | to_json }}`
- [x] 3.3 Update `templates/ai_agent_script.sh.j2` -- wrap GCP environment variable exports in `{% if 'google-vertex-anthropic' in ai_opencode_providers %}` conditional block

## 4. Documentation and Verification

- [x] 4.1 Update `README.md` with Ollama variables, migration guidance for existing users, and example playbook snippets for Ollama-only, Vertex-only, and mixed setups
- [x] 4.2 Run `ansible-lint` against the role and fix any issues
- [x] 4.3 Run the smoke test (`tests/test.yml`) to verify the role executes without errors
