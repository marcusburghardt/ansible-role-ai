# Proposal

## Why

OpenCode 2.0 has been released with breaking changes to the configuration
schema, npm package name, provider IDs, and permission system. The role must be
updated to generate valid V2 configuration and install the V2 CLI package so
that managed workstations run the current version of OpenCode. The
opencode-metrics plugin has not yet been ported to the V2 plugin API, so it
must be temporarily disabled until migrated.

## What Changes

- **BREAKING**: npm package changes from `opencode-ai` to `@opencode/cli`.
  Remove the global V1 package before installing V2 to avoid executable conflicts.
- **BREAKING**: Config key renames -- `permission` to `permissions`, `plugin` to
  `plugins`, `agent` to `agents`, `provider` to `providers`, `autoupdate` to
  `update`.
- **BREAKING**: Remove `small_model` from config (no V2 equivalent). Per-agent
  model variables now all default to `ai_model`.
- **BREAKING**: Remove `share` and `options` keys from config (no V2 equivalent).
- **BREAKING**: Remove `disabled_providers` from config (no V2 equivalent;
  default was `[]`, a no-op).
- **BREAKING**: Permission system restructured from nested dicts to ordered
  array of rule objects; `bash` action renamed to `shell`; merge strategy
  changes from `combine(recursive=True)` to list concatenation.
  An explicit external-directory catch-all `ask` preserves V1 approvals.
- **BREAKING**: Provider `google-vertex-anthropic` retired; replaced by
  `google-vertex` with `settings.project` and `settings.location`.
- **BREAKING**: Provider schema keys `npm` to `package`, `options` to `settings`.
- **BREAKING**: Compaction schema changes -- `prune` removed, `reserved` becomes
  `buffer`, new `keep.tokens` field added.
- **BREAKING**: `CLAUDE.md` removed from default instructions list (V2 only
  recognizes `AGENTS.md`).
- Commands directory renamed from `command/` to `commands/` (V2 convention).
- GCP project and location moved from wrapper script env vars into provider
  config settings, simplifying the wrapper script.
- Metrics plugin temporarily disabled in default `plugins` list until the
  plugin is ported to the V2 API.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `opencode-configuration`: Config template restructured for V2 schema --
  renamed keys, permission system overhauled from dict to array, provider schema
  updated, compaction schema updated, removed V1-only fields (`small_model`,
  `share`, `options`, `disabled_providers`).
- `tool-installation`: OpenCode npm package name changes from `opencode-ai`
  to `@opencode/cli`.
- `command-autodiscovery`: Deploy directory changes from `command/` to
  `commands/`.
- `metrics-plugin-config`: Default plugins list temporarily excludes the
  metrics plugin until it is ported to the V2 plugin API.

## Impact

- **Files modified**: `templates/opencode.json.j2`, `defaults/main.yml`,
  `vars/configure_opencode.yml`, `tasks/install_opencode.yml`,
  `tasks/configure_opencode.yml`, `templates/ai_agent_script.sh.j2`,
  `tests/test.yml`.
- **Variables removed**: `ai_small_model`, `ai_opencode_options`,
  `ai_opencode_disabled_providers`.
- **Variables restructured**: `ai_opencode_permissions` changes from `{}` (dict)
  to `[]` (list), `ai_opencode_providers` schema updated,
  `ai_opencode_compaction` schema updated.
- **User-facing**: Any playbook that overrides `ai_small_model`,
  `ai_opencode_permissions`, `ai_opencode_providers`, or
  `ai_opencode_compaction` must update to the new formats.
- **Dependencies**: Requires `@opencode/cli` to be published on npm. The
  `opencode-metrics` plugin will be non-functional until separately migrated.
