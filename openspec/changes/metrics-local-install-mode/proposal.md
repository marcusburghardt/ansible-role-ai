# Proposal

## Why

As the maintainer of both `ansible-role-ai` and `@mburghardt/opencode-metrics`, there
is a frequent need to test local, unreleased plugin changes before cutting a new npm
release. Currently this is done by running `make install` inside the local
`opencode-metrics` repo, which silently overrides the npm entry managed by the role —
breaking the role's source-of-truth guarantee and creating a state the role cannot
observe or restore.

## What Changes

- Extend `ai_opencode_metrics_version` to accept the special value `"local"` in
  addition to version strings and `"latest"`.
- Add a new variable `ai_opencode_metrics_local_path` (default: `""`) that specifies
  the path to the local `opencode-metrics` repository when using local mode.
- In **npm mode** (`version` is a semver string or `"latest"`): the role ensures
  `~/.config/opencode/plugins/opencode-metrics.ts` is absent and the npm entry is
  present in `opencode.json`.
- In **local mode** (`version == "local"`): the role writes
  `~/.config/opencode/plugins/opencode-metrics.ts` pointing to the local repo's
  `dist/index.js`, and excludes the npm entry from `opencode.json`.
- The role fails with a clear message when `version == "local"` but
  `ai_opencode_metrics_local_path` is empty.
- Tilde (`~`) in `ai_opencode_metrics_local_path` is expanded by the role to the
  target user's home directory.
- A `debug` task reports the resolved plugin mode, version, source, and config
  status during playbook execution, following the pattern established by
  `install_ollama` and `install_cursor`.

## Capabilities

### New Capabilities

- `metrics-local-install-mode`: Controls whether the opencode-metrics plugin is loaded
  from npm (pinned or latest) or from a local repository path, with the role enforcing
  mutual exclusivity and idempotent cleanup between the two modes.

### Modified Capabilities

- `metrics-plugin-config`: The `ai_opencode_metrics_version` variable gains the
  additional accepted value `"local"`, and a companion variable
  `ai_opencode_metrics_local_path` is introduced. The existing version-pinning
  behavior is unchanged.
- `opencode-configuration`: The `ai_opencode_plugins` list in `opencode.json` is
  conditionally built: in local mode the metrics npm entry is excluded; in npm mode
  it is present as before.

## Impact

- `defaults/main.yml`: two variable additions (`ai_opencode_metrics_local_path` and
  updated comment for `ai_opencode_metrics_version`).
- `tasks/configure_opencode.yml`: two new conditional tasks (write or remove the
  loader `.ts` file) plus one informational debug task.
- `templates/opencode.json.j2`: conditional exclusion of the metrics npm entry when
  version is `"local"`.
- `vars/configure_opencode.yml`: new computed variable for the expanded local path.
- No dependency on external tools beyond what the role already requires (`ansible`).
- No changes to the npm install path (`install_openspec.yml` is unaffected).
