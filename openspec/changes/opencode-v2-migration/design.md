# Design

## Context

The role currently generates OpenCode V1 configuration. V2 renames most
top-level config keys, restructures the permission system from nested dicts to
an ordered array, retires the `google-vertex-anthropic` provider ID, removes
several config fields, and changes the npm package from `opencode-ai` to
`@opencode/cli`. See proposal.md for the full motivation.

The opencode-metrics plugin (`@mburghardt/opencode-metrics`) uses the V1 plugin
API (`@opencode-ai/plugin`) and must be ported separately. Until then, it is
excluded from the default plugins list.

## Goals / Non-Goals

**Goals:**

- Generate valid OpenCode V2 configuration from the role.
- Preserve all existing security hardening (permission rules, denied commands,
  denied credential file reads, denied system paths).
- Keep the user-facing variable interface as close to V1 as possible, only
  changing where the V2 schema forces it.
- Simplify where V2 enables it (permission merge via concatenation, GCP
  settings in config instead of env vars).

**Non-Goals:**

- Dual V1/V2 support. This is a clean break; use git to rollback if needed.
- Migrating the opencode-metrics plugin (separate change in that repo).
- Adopting new V2-only features (policies, references, worktrees, websearch,
  formatter, snapshots). These can be added incrementally later.

## Decisions

### 1. Permission system: dict-to-array conversion with list concatenation

**Decision:** Convert `_ai_opencode_permissions_default` from a nested dict to
a flat list of `{action, resource, effect}` objects. Change the merge from
`combine(recursive=True)` to simple list concatenation (`defaults + overrides`).
Add an explicit `external_directory` catch-all `ask` rule before existing path
exceptions: V2 allows external directories by default, unlike V1.

**Rationale:** V2 uses last-match-wins on an ordered array. Appending user
rules at the end gives them natural override precedence -- identical semantics
to the V1 dict merge but with a simpler mechanism.

**Alternative considered:** A custom Jinja filter to convert dicts to arrays at
render time. Rejected because it hides the actual data format from users and
makes debugging harder.

### 2. `ai_small_model` removal

**Decision:** Remove `ai_small_model` entirely. Change all per-agent model
variable defaults from `{{ ai_small_model }}` to `{{ ai_model }}`.

**Rationale:** V2 has no `small_model` concept. Users who want different models
per agent already have `ai_opencode_agent_*_model` variables. Defaulting
everything to `ai_model` is the simplest correct behavior -- Ollama users
(same model everywhere) see no change, and paid-provider users can still
override per-agent variables independently.

**Alternative considered:** Keeping `ai_small_model` as a convenience alias
that defaults to `ai_model`. Rejected because it adds a variable with no V2
backing and would confuse users reading the V2 docs.

### 3. GCP settings: move from env vars to provider config

**Decision:** Put `project` and `location` inside
`providers.google-vertex.settings` instead of exporting them as `GCP_PROJECT`
and `VERTEX_LOCATION` in the wrapper script.

**Rationale:** V2 supports both env vars and config settings, but config is
self-documenting and doesn't require a wrapper script. The wrapper script
(`skynet`) still exists for `TRUSTED_GITHUB_ORGS` but no longer needs the
conditional GCP block.

### 4. Metrics plugin: temporarily disable

**Decision:** Set `ai_opencode_plugins` default to `[]` until the metrics
plugin is ported to V2. Keep all metrics-related infrastructure (local loader,
config deployment, data directory) functional for development.

**Rationale:** The V1 plugin API (`Plugin` function, `PluginInput`, `Hooks.event`)
is incompatible with V2 (`Plugin.define`, `PluginContext`, `ctx.event.subscribe`).
Including an incompatible plugin would cause startup errors.

### 5. Commands directory: rename to plural

**Decision:** Change `ai_opencode_command_dir` from `command/` to `commands/`.

**Rationale:** V2 convention uses plural `commands/`. The legacy singular is
still discovered but is deprecated.

### 6. Provider schema: key renames only, preserve structure

**Decision:** Rename `npm` to `package` and `options` to `settings` in provider
defaults. Keep `ai_opencode_ollama_models` for explicit model display names
even though V2 auto-discovers Ollama.
Use the documented `aisdk:` prefix for the migrated AI SDK package value.

**Rationale:** Explicit models give users control over display names and ensure
predictable model visibility regardless of Ollama discovery timing.

### 7. Remove the V1 npm package before installing V2

Both packages own the `opencode` executable. Remove global `opencode-ai` with
`state: absent` before installing `@opencode/cli`, preserving existing version
selection. This is idempotent on hosts where V1 is already absent.

### 8. Restart the shared service from the role

**Decision:** Add `ai_opencode_restart_service` (default `true`) and restart the
shared background service from a handler after installation or configuration
changes. The handler runs `opencode service status` first and restarts only when
a service is already running. Both the launcher template and the handler take
their environment from `ai_opencode_server_env`.

**Rationale:** V2 always uses a server, even when the user only opens the TUI.
The shared server keeps the environment it was started with, so configuration
edits, new binaries, and environment changes do not take effect until it
restarts. Users should not have to remember that. Checking status first avoids
starting a server the user intentionally stopped, and sharing one environment
dict keeps `TRUSTED_GITHUB_ORGS` available to commands after an
Ansible-driven restart.

**Alternative considered:** Documenting a manual `opencode service restart`.
Rejected because it is exactly the step users forget after a deployment.

**Alternative considered:** Running `skynet --standalone` by default. Rejected
because it abandons shared sessions and pairing, and it works around the
environment problem instead of fixing it.

### 9. Provider credentials: file substitution instead of environment variables

**Decision:** Document and test `apiKey: "{file:...}"` in provider settings for
EnMaaS keys. Keep the launcher's `ENMAAS_KEY` export for `--standalone` and
other tools.

**Rationale:** The server resolves `{env:...}` in its own process, so an
environment variable exported by a client launcher is invisible to an
already-running shared server. File substitution lets the server read the
protected file directly, regardless of how it was started, and keeps the key out
of `opencode.json` and the environment. `{file:...}` substitutes literally, so
documentation must require no trailing newline.

### 10. Launcher verification after installation

**Decision:** After installing `@opencode/cli`, report every `opencode` and
`opencode2` entry on `PATH`, remove dangling `opencode` symlinks left by earlier
installs, recreate `opencode` from the `opencode2` alias when needed, and fail
with the report when `opencode` still does not resolve.

**Rationale:** The V2 package publishes both names as aliases, so a broken
`opencode` entry is almost always a leftover V1 link earlier on `PATH`. Bash
reports a dangling symlink as `not found`, which makes `opencode2` appear to be
the only working binary. Removing only dangling symlinks is safe, and failing
early beats deploying a launcher that cannot start.

## Risks / Trade-offs

- **[Risk] Users with custom `ai_opencode_permissions` overrides break.**
  Mitigation: Document the format change (`{}` dict to `[]` array) in the role
  changelog and README. The new format is more explicit and self-documenting.

- **[Risk] Users referencing `ai_small_model` in their playbooks get undefined
  variable errors.** Mitigation: Document the removal. The fix is to use
  `ai_model` or set per-agent model variables directly.

- **[Risk] Users referencing `google-vertex-anthropic` in model strings get
  rejected by V2.** Mitigation: Document that `google-vertex` replaces
  `google-vertex-anthropic` in all model references.

- **[Risk] Metrics plugin is non-functional until separately migrated.**
  Mitigation: This is an accepted trade-off. Metrics data collection pauses
  but no data is lost (SQLite DB is untouched). The plugin migration is tracked
  as a separate change.

- **[Trade-off] No rollback path within the role.** Accepted: git tag before
  migration provides rollback. Dual-support was rejected due to ~60% code
  duplication.

## Migration Plan

1. Tag the current role state (e.g., `v0.3.2-opencode-v1`) before any changes.
2. Implement all changes on the `opencode-v2-migration` branch.
3. Test with `tests/test.yml` (configuration-only smoke test).
4. Manually validate the generated `opencode.json` against the V2 schema.
5. Test on a workstation with OpenCode V2 installed.
6. Merge and release as a new minor version.
