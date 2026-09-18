# Tasks

## 1. Variables

- [ ] 1.1 Add `ai_opencode_metrics_local_path: ""` to `defaults/main.yml` with a
  comment explaining it is only used when `ai_opencode_metrics_version` is `"local"`;
  verify `ansible-lint` passes and the variable appears in the defaults file.

- [ ] 1.2 Update the `ai_opencode_plugins` default in `defaults/main.yml` to the
  Jinja2 conditional that returns an empty list when `ai_opencode_metrics_version ==
  "local"` and the npm specifier list otherwise; verify that with version `"0.2.0"`
  the rendered list contains `@mburghardt/opencode-metrics@0.2.0` and with `"local"`
  it is empty.

- [ ] 1.3 Add the computed variable `_ai_metrics_local_path_expanded` to
  `vars/configure_opencode.yml` that replaces a leading `~` with `ai_user_home_dir`;
  verify the variable resolves to an absolute path when a tilde path is supplied and
  is empty when `ai_opencode_metrics_local_path` is empty.

## 2. Template

- [ ] 2.1 Create `templates/opencode_metrics_plugin_loader.ts.j2` containing the
  SPDX header, managed-by comment, and `import` statement using
  `_ai_metrics_local_path_expanded`; verify the rendered output matches the expected
  loader format.

## 3. Tasks

- [ ] 3.1 Add a validation task to `tasks/configure_opencode.yml` (before any loader
  file work) that fails with a clear message when `ai_opencode_metrics_version ==
  "local"` and `ai_opencode_metrics_local_path` is empty; verify the task is skipped
  in npm mode and triggers the expected failure message in local mode without a path.

- [ ] 3.2 Add a debug task to `tasks/configure_opencode.yml` (after validation,
  before loader file actions) that reports the resolved plugin state: mode (`npm` or
  `local`), raw version value, resolved source (npm specifier or expanded absolute
  path to `dist/index.js`), and config deployment status
  (`ai_opencode_metrics_config | length > 0`); verify the message renders correctly
  for both npm and local modes by inspecting playbook output.

- [ ] 3.3 Add a task to `tasks/configure_opencode.yml` that removes
  `~/.config/opencode/plugins/opencode-metrics.ts` when `ai_opencode_metrics_version
  != "local"`; verify via `ansible-lint` and by confirming idempotency (task reports
  `ok` when file is already absent, `changed` when it removes an existing file).

- [ ] 3.4 Add a task to `tasks/configure_opencode.yml` that writes
  `~/.config/opencode/plugins/opencode-metrics.ts` from the template when
  `ai_opencode_metrics_version == "local"`; verify the deployed file contains the
  correct absolute path to `dist/index.js` and the managed-by comment.

## 4. Documentation

- [ ] 4.1 Add a "Local development of opencode-metrics" section to `README.md`
  describing the maintainer workflow: (1) make code changes in the local repo,
  (2) run `make build`, (3) set `ai_opencode_metrics_version: "local"` and
  `ai_opencode_metrics_local_path` in the playbook, (4) run the playbook, (5) restart
  OpenCode; verify the section is present and accurately describes the steps.

- [ ] 4.2 Add a "Switching back to npm mode" note in the same README section
  describing the reverse steps: set version back to a semver string, remove or ignore
  `ai_opencode_metrics_local_path`, run the playbook (loader file is removed
  automatically); verify the note is present.

## 5. Validation

- [ ] 5.1 Run `ansible-lint` against the role and confirm zero new lint issues
  introduced by this change.

- [ ] 5.2 Run `openspec validate --change metrics-local-install-mode` and confirm the
  change passes validation.
