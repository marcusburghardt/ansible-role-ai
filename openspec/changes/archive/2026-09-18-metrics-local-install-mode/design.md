# Design

## Context

OpenCode supports two plugin loading mechanisms:

1. **npm entry in `opencode.json`** — OpenCode fetches and installs the package at
   startup via Bun into `~/.config/opencode/node_modules/`.
2. **TypeScript loader file in `~/.config/opencode/plugins/`** — OpenCode imports the
   file directly at startup, bypassing npm entirely.

When both exist for the same plugin, the loader file takes precedence (it is an
explicit local import). Currently the role only manages mechanism 1. Mechanism 2 is
created externally by `make install` inside the `opencode-metrics` repo. The role has
no visibility into mechanism 2 and cannot restore a consistent state if the two
conflict.

See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals**
- The role becomes the sole authority for how the plugin is loaded on each run.
- Switching between npm and local mode requires only a variable change + playbook run.
- The role does not take on a dependency on `bun`, `npm`, or `make`.

**Non-Goals**
- Building `dist/` — the maintainer builds before running the playbook.
- Supporting local mode for plugins other than opencode-metrics (not needed yet).
- Validating that `dist/index.js` actually exists at the given path (keeps the role
  simple; a missing `dist/` fails at OpenCode startup, which is clear enough).

## Decisions

### Decision 1: Sentinel value `"local"` on the existing variable

**Chosen**: Extend `ai_opencode_metrics_version` with a sentinel value `"local"`.
A companion variable `ai_opencode_metrics_local_path` holds the repository path.

**Alternative considered**: A separate boolean flag `ai_opencode_metrics_local: true`.
Rejected because it requires keeping two variables in sync (version + flag) and
offers no benefit over a sentinel value on the single variable that already drives
mode selection.

**Alternative considered**: A separate install task (`install_opencode_metrics_local`).
Rejected because the loader file management logically belongs in `configure_opencode`,
where all OpenCode configuration state is controlled.

### Decision 2: Mutual exclusivity enforced on every run

**Chosen**: In npm mode, the role actively removes the loader `.ts` file. In local
mode, the role writes the loader file and the npm entry is excluded from the plugins
list. Both directions are idempotent.

**Why**: Without active cleanup, a switch from local → npm leaves the loader file in
place, and OpenCode continues using the local copy silently. The role must enforce the
desired state, not just add to it.

### Decision 3: Tilde expansion via Ansible variable substitution

**Chosen**: Accept `~` in `ai_opencode_metrics_local_path` and expand it using
`ai_user_home_dir` (already available as `ansible_facts['user_dir']`) in
`vars/configure_opencode.yml`. A new computed variable
`_ai_metrics_local_path_expanded` holds the expanded absolute path.

**Why**: The TypeScript `import` statement in the loader file requires an absolute
path. Tilde notation is idiomatic for Ansible playbook authors and should not be left
as-is in generated files.

### Decision 4: Loader file managed by `ansible.builtin.template`

**Chosen**: The loader `.ts` file is rendered from a Jinja2 template
(`opencode_metrics_plugin_loader.ts.j2`) using the expanded local path variable.

**Alternative considered**: `ansible.builtin.copy` with `content:` inline. Rejected
because a template file is easier to read, version, and lint.

### Decision 5: Conditional plugin list via `ai_opencode_plugins` default

**Chosen**: The `ai_opencode_plugins` default in `defaults/main.yml` is expressed as
a Jinja2 conditional:

```yaml
ai_opencode_plugins: >-
  {{ [] if ai_opencode_metrics_version == 'local'
     else ['@mburghardt/opencode-metrics@' + ai_opencode_metrics_version] }}
```

This makes the default list automatically correct for both modes without touching
the template. Users who override `ai_opencode_plugins` entirely are unaffected.

**Alternative considered**: Conditional logic inside `opencode.json.j2`. Rejected
because the template should remain a dumb renderer of variables; logic belongs in
defaults and vars.

### Decision 6: Workflow documentation in README

**Chosen**: The local mode workflow (build → set variables → run playbook → restart
OpenCode) is documented in `README.md` under a dedicated "Local development of
opencode-metrics" section.

**Why**: The spec requires this to be discoverable without reading role source code.
The README is the canonical first-read document for the role.

## Risks / Trade-offs

- **Stale `dist/`** — If the maintainer forgets to run `make build` before the
  playbook, OpenCode loads outdated plugin code silently. Mitigation: the workflow
  documentation makes `make build` the first step.
- **Path typo** — A wrong `ai_opencode_metrics_local_path` writes a loader pointing
  to a non-existent file. OpenCode will fail at startup with an import error, which
  is visible and actionable. No mitigation needed beyond the error itself.
- **Conditional default complexity** — The Jinja2 conditional in `defaults/main.yml`
  is slightly unusual. Mitigation: a comment explains it, and the behavior is covered
  by scenarios in the spec.

## Migration Plan

No migration needed. The change is additive:
- Existing users with `ai_opencode_metrics_version: "0.2.0"` (or any semver) see no
  behavioral change — the loader file cleanup task is a no-op when no loader exists.
- Users who previously ran `make install` and have a stale loader file will have it
  removed on the next playbook run in npm mode. This is the desired correction.

## Open Questions

None.
