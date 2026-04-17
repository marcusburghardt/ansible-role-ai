## Context

The `configure_ollama` task file currently only pulls models that have
`enabled: true` in `ai_ollama_models`. Models set to `enabled: false` are
silently skipped, but any previously-pulled copy remains on disk. There is
no mechanism to declaratively remove a model.

The existing variable schema is:

```yaml
ai_ollama_models:
  - { enabled: true,  name: 'qwen3:8b' }
  - { enabled: false, name: 'qwen3:32b' }
```

The role is pre-1.0, so minor schema additions are acceptable without a
breaking-change process.

## Goals / Non-Goals

**Goals:**
- Allow users to mark individual models for removal via a new `removed`
  field in `ai_ollama_models`.
- Fail fast with a clear message when a model entry has conflicting flags
  (`enabled: true` and `removed: true`).
- Only attempt `ollama rm` for models that are actually present on disk,
  avoiding unnecessary errors.
- Maintain full backward compatibility: existing playbooks that omit
  `removed` must see zero behavior change.

**Non-Goals:**
- Purging models not listed in `ai_ollama_models` (e.g., manually-pulled
  models). The role manages only the models it knows about.
- Introducing a fundamentally different variable schema (e.g., replacing
  `enabled` with `state: present/absent`). The current boolean approach is
  extended, not replaced.

## Decisions

### 1. Extend the existing schema with an optional `removed` field

Add an optional boolean `removed` (default `false`) rather than migrating
to a `state: present/absent` pattern.

**Rationale**: Preserves backward compatibility with zero migration effort.
The `enabled` + `removed` combination covers all three lifecycle states
(pull / skip / delete). A `state`-based schema was considered but rejected
because it would break every existing playbook overriding `ai_ollama_models`.

### 2. "Removed wins" on conflict -- enforced by validation failure

If a model has both `enabled: true` and `removed: true`, the playbook SHALL
fail immediately with an actionable error message before any pull or remove
work begins.

**Rationale**: Silently resolving the conflict (in either direction) hides
a user mistake. Failing early forces the user to express clear intent. This
was chosen over "removed wins silently" to avoid surprising side effects.

### 3. List installed models before removing

The removal task SHALL register the output of `ollama list` and only run
`ollama rm` for models that appear in that output.

**Rationale**: Running `ollama rm` on a model that is not installed would
produce an error. Pre-checking avoids unnecessary failures and makes the
task cleanly idempotent. This mirrors the robustness pattern of
checking state before acting.

### 4. Removal runs after pulls

The removal block is placed after the pull block in `configure_ollama.yml`.

**Rationale**: Ordering does not matter for non-conflicting entries (a model
is either pulled or removed, never both, due to validation). Placing removal
after pulls keeps the file's logical flow: validate -> pull -> clean up.

## Risks / Trade-offs

- **[Risk] User sets `removed: true` without `enabled: false`** --
  Mitigated by the validation step that fails the playbook with a clear
  message.
- **[Risk] `ollama list` output format changes across versions** --
  Mitigated by matching on the model name string within stdout, which has
  been stable across Ollama releases. If the format changes, the `when`
  condition is a single line to update.
- **[Trade-off] Two booleans instead of one enum** -- Slightly more complex
  schema than `state: present/absent`, but avoids a breaking change. The
  validation step catches the one invalid combination.
