# Design

## Context

See proposal.md for motivation. The role currently treats plugins as a purely
opt-in, user-provided list (`ai_opencode_plugins: []`). The Grafana metrics
visualization task (`configure_grafana_metrics`) references a data directory
variable named `ai_grafana_metrics_data_dir`, which semantically belongs to the
metrics plugin rather than Grafana. The archived change
`2026-09-16-configure-grafana-metrics` originally introduced this variable.

## Goals / Non-Goals

**Goals:**

- Ship `@mburghardt/opencode-metrics` as a default plugin with a pinned version
- Allow users to customize the plugin's classification and budget rules via
  playbook variables
- Rename the data directory variable to reflect its true owner (the plugin)
- Maintain backward compatibility for users who explicitly set
  `ai_opencode_plugins`

**Non-Goals:**

- Backfill automation -- users run `make backfill` on their own
- Coupling metrics plugin enablement with Grafana task enablement -- these remain
  independent controls
- Templating the plugin's full feature set (e.g., metric definitions) -- only
  `config.yaml` structure is exposed

## Decisions

### 1. Version variable defined before plugins list

**Decision:** Define `ai_opencode_metrics_version` before `ai_opencode_plugins` in
`defaults/main.yml` so Ansible resolves the Jinja reference at template time.

**Rationale:** Ansible resolves nested Jinja in defaults lazily, but defining the
version first makes the dependency explicit and readable. The default plugins
entry becomes:

```yaml
ai_opencode_metrics_version: "0.2.0"

ai_opencode_plugins:
  - "@mburghardt/opencode-metrics@{{ ai_opencode_metrics_version }}"
```

**Alternative considered:** Hardcoding the version directly in the plugins list.
Rejected because it creates two places to update on each release and breaks the
single-source-of-truth principle.

### 2. Config deployment in configure_opencode task

**Decision:** Add the metrics config deployment (directory creation + template) to
`tasks/configure_opencode.yml` rather than creating a new task file.

**Rationale:** The metrics config is part of the OpenCode plugin ecosystem. Adding
it to `configure_opencode` keeps all OpenCode-related configuration in one place
and avoids adding a new entry to `ai_tasks`. The tasks are conditional on
`ai_opencode_metrics_config | length > 0`, so they are no-ops by default.

**Alternative considered:** A dedicated `configure_opencode_metrics` task file
with its own `ai_tasks` entry. Rejected because it adds a new task toggle for
what amounts to two conditional tasks, increasing user-facing complexity.

### 3. Pass-through config variable (full struct override)

**Decision:** `ai_opencode_metrics_config` takes the complete config structure as a
dict. When set, the entire dict is serialized to YAML and deployed as
`config.yaml`. No merge with defaults.

**Rationale:** This follows the established pattern in the role
(`ai_opencode_providers`, `ai_opencode_agents`, `ai_opencode_compaction` all work
this way). Full override is simpler to reason about, avoids complex merge logic,
and gives users complete control. Since both projects share a maintainer, default
rule changes can be coordinated across releases.

**Alternative considered:** Merge strategy (user provides additional rules, role
merges with built-in defaults). Rejected due to merge complexity, difficulty
reordering rules, and inability to remove default rules cleanly.

### 4. Variable rename with clean break

**Decision:** Rename `ai_grafana_metrics_data_dir` to `ai_opencode_metrics_data_dir`
as a clean break (no deprecation alias).

**Rationale:** The role is pre-1.0, the variable was introduced recently (archived
change `2026-09-16-configure-grafana-metrics`), and the user base is small. A
clean rename is simpler than maintaining a compatibility alias. The BREAKING
change is documented in the proposal and will be noted in release notes.

**Alternative considered:** Adding a deprecation alias that falls back to the old
name. Rejected as over-engineering for the current project maturity.

### 5. Template uses `to_nice_yaml` for config rendering

**Decision:** The `opencode_metrics_config.yaml.j2` template renders the config
variable using Ansible's `to_nice_yaml` filter.

**Rationale:** Produces human-readable YAML output. The filter handles nested
dicts (classification rules with conditions/exclude blocks) cleanly. The
`---` YAML document marker is added explicitly in the template for consistency.

## Risks / Trade-offs

**[Risk] Users on old variable name break on upgrade**
Playbooks referencing `ai_grafana_metrics_data_dir` directly will fail.
Mitigation: documented as BREAKING in proposal; release notes will include the
migration step (rename the variable).

**[Risk] Plugin version drift**
If the role maintainer forgets to bump `ai_opencode_metrics_version` after a
plugin release, users get an older version.
Mitigation: both projects share a maintainer; version bump is part of the plugin
release checklist.

**[Risk] Config schema version mismatch**
If the plugin changes its `config.yaml` schema (currently `version: 1`), a
user-provided config with the old schema could cause plugin errors.
Mitigation: the plugin validates config on load and logs warnings for
unrecognized fields. Schema changes will be coordinated between projects.

**[Trade-off] Default-on plugin increases network activity**
New role users automatically pull the npm package on first OpenCode startup.
Accepted: the plugin is lightweight, and the value (immediate metrics collection)
outweighs the cost of a small npm install.
