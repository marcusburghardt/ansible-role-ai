## 1. Validation

- [x] 1.1 Add a task at the start of `tasks/configure_ollama.yml` that fails the playbook if any entry in `ai_ollama_models` has both `enabled: true` and `removed: true` (using `item.removed | default(false)`). The failure message must name the conflicting model and instruct the user to fix it.

## 2. Model Removal

- [x] 2.1 Add a task to run `ollama list` and register its output, conditionally executed only when at least one model has `removed: true`.
- [x] 2.2 Add a task that loops over models with `removed: true` and runs `ollama rm` for each, with a `when` condition that checks the model name appears in the registered `ollama list` output. Use `changed_when` to reflect whether a removal actually occurred.

## 3. Defaults Documentation

- [x] 3.1 Update the comment block above `ai_ollama_models` in `defaults/main.yml` to document the `removed` field, its default value of `false`, and the three-state lifecycle (enabled / disabled / removed).
