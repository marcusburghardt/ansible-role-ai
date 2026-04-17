## Why

The `ai_ollama_models` variable allows users to enable or disable model pulling,
but disabled models that were previously pulled remain on disk indefinitely.
On resource-constrained machines (e.g., laptops with 30 GB RAM and no discrete
GPU), large models consume significant disk space while providing no practical
value. Users need a way to declaratively remove unwanted models through the
same variable they already use to manage them.

## What Changes

- Add an optional `removed` field (default: `false`) to each entry in
  `ai_ollama_models`, allowing users to mark models for deletion.
- Add a validation step that fails the playbook if a model has both
  `enabled: true` and `removed: true`, instructing the user to fix the
  conflict.
- Add a removal step that lists installed models and runs `ollama rm` only
  for models that are both marked `removed: true` and actually present on
  disk.
- Update `defaults/main.yml` documentation to describe the new field and
  the three-state lifecycle (enabled / disabled / removed).

## Capabilities

### New Capabilities
- `model-removal`: Declarative removal of Ollama models via the `removed`
  field in `ai_ollama_models`, including input validation and idempotent
  deletion.

### Modified Capabilities

(none -- no existing spec-level requirements change)

## Impact

- `tasks/configure_ollama.yml`: three new task blocks (validate, list, remove).
- `defaults/main.yml`: comment updates documenting the new `removed` field.
- Fully backward-compatible: existing playbooks that omit `removed` default
  to `false` and see no behavior change.
