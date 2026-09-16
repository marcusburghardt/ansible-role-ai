## ADDED Requirements

### Requirement: Validate model list for conflicting flags
The role SHALL validate `ai_ollama_models` at the start of
`configure_ollama` and SHALL fail the playbook if any model entry has both
`enabled` set to `true` and `removed` set to `true`. The failure message
SHALL name the conflicting model and instruct the user to set either
`enabled` to `false` or `removed` to `false`.

#### Scenario: Conflicting enabled and removed flags
- **WHEN** `ai_ollama_models` contains an entry with `enabled: true` and `removed: true`
- **THEN** the playbook SHALL fail with a message identifying the model name and instructing the user to resolve the conflict

#### Scenario: No conflicts in model list
- **WHEN** no entry in `ai_ollama_models` has both `enabled: true` and `removed: true`
- **THEN** validation SHALL pass and execution SHALL continue to the pull and removal steps

### Requirement: Remove models marked with removed flag
The role SHALL remove models that have `removed` set to `true` (and
`enabled` set to `false`) by running `ollama rm` for each such model,
but only if the model is currently installed on the target host.

#### Scenario: Remove a model that is installed
- **WHEN** a model entry has `enabled: false` and `removed: true` and the model is present in the output of `ollama list`
- **THEN** the role SHALL run `ollama rm <model_name>` to delete it

#### Scenario: Skip removal for a model not installed
- **WHEN** a model entry has `enabled: false` and `removed: true` but the model is NOT present in the output of `ollama list`
- **THEN** the role SHALL skip the removal and report no change

#### Scenario: Skip removal when removed is not set
- **WHEN** a model entry does not include the `removed` field
- **THEN** the role SHALL treat `removed` as `false` and SHALL NOT attempt to remove the model

### Requirement: Default value for removed field
The `removed` field SHALL default to `false` when omitted from a model
entry. Existing playbooks that do not set `removed` SHALL see no behavior
change.

#### Scenario: Omitted removed field defaults to false
- **WHEN** a model entry in `ai_ollama_models` does not include the `removed` key
- **THEN** the role SHALL treat the entry as `removed: false` and SHALL NOT attempt removal

### Requirement: List installed models before removal
The role SHALL query the currently installed models via `ollama list` and
register the output before attempting any removal operations. Removal
tasks SHALL use this registered output to determine whether a model is
present on disk.

#### Scenario: Installed models are queried
- **WHEN** any model in `ai_ollama_models` has `removed: true`
- **THEN** the role SHALL run `ollama list` and register its output before executing any `ollama rm` commands
