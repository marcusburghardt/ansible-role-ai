# Tasks

## 1. Installation

- [x] 1.1 Remove the globally installed V1 `opencode-ai` npm package before installing `@opencode/cli` in `tasks/install_opencode.yml`, preserving latest/pinned version behavior

## 2. Remove V1-Only Variables

- [x] 2.1 Remove `ai_small_model` from `defaults/main.yml`
- [x] 2.2 Remove `ai_opencode_options` from `defaults/main.yml`
- [x] 2.3 Remove `ai_opencode_disabled_providers` from `defaults/main.yml`
- [x] 2.4 Update all `ai_opencode_agent_*_model` defaults from `{{ ai_small_model }}` to `{{ ai_model }}` in `defaults/main.yml`

## 3. Provider Migration

- [x] 3.1 Update `ai_opencode_providers` default: rename `npm` to `package`, `options` to `settings`, replace `google-vertex-anthropic` with `google-vertex` including `settings.project` and `settings.location` in `defaults/main.yml`
- [x] 3.2 Simplify `templates/ai_agent_script.sh.j2`: remove conditional GCP env var exports, update provider key check from `google-vertex-anthropic` to `google-vertex` if any conditional logic remains

## 4. Permission System Overhaul

- [x] 4.1 Convert `_ai_opencode_permissions_default` from nested dict to ordered list of `{action, resource, effect}` objects in `vars/configure_opencode.yml`, renaming `bash` to `shell` and adding an `external_directory` catch-all `ask` rule before path exceptions to preserve V1 behavior
- [x] 4.2 Change `ai_opencode_permissions` default from `{}` to `[]` in `defaults/main.yml`, update variable description
- [x] 4.3 Change `_ai_opencode_permissions_merged` from `combine(recursive=True)` to list concatenation (`_ai_opencode_permissions_default + ai_opencode_permissions`) in `vars/configure_opencode.yml`

## 5. Compaction Schema Update

- [x] 5.1 Update `ai_opencode_compaction` default from `{auto: true, prune: true, reserved: 10000}` to `{auto: true, keep: {tokens: 15000}, buffer: 10000}` in `defaults/main.yml`

## 6. Instructions Update

- [x] 6.1 Remove `CLAUDE.md` from `ai_opencode_instructions` default list in `defaults/main.yml`

## 7. Commands Directory Rename

- [x] 7.1 Change `ai_opencode_command_dir` from `command` to `commands` in `vars/configure_opencode.yml`

## 8. Metrics Plugin Disable

- [x] 8.1 Change `ai_opencode_plugins` default to `[]` (empty list) in `defaults/main.yml`, update comments to note V2 migration pending

## 9. Config Template Rewrite

- [x] 9.1 Rewrite `templates/opencode.json.j2` with V2 key names: `plugins`, `agents`, `providers`, `permissions`, `update`; remove `small_model`, `share`, `options`, `disabled_providers`, `autoupdate`

## 10. Test Updates

- [x] 10.1 Update `tests/test.yml` to reflect new directory name (`commands/` not `command/`) and any changed variable names
- [x] 10.2 Run `tests/test.yml` and verify it passes

## 11. Shared Service Lifecycle

- [x] 11.1 Add `ai_opencode_restart_service` (default `true`) and `ai_opencode_server_env` (`TRUSTED_GITHUB_ORGS`) defaults in `defaults/main.yml`
- [x] 11.2 Add a restart handler in `handlers/main.yml` that checks `opencode service status` and restarts only a running service, passing `ai_opencode_server_env`
- [x] 11.3 Notify the restart handler from the OpenCode install and configuration tasks
- [x] 11.4 Render the launcher environment from `ai_opencode_server_env` and remove the re-added GCP exports

## 12. Launcher Verification

- [x] 12.1 Report `opencode` and `opencode2` launchers found on `PATH` after installation
- [x] 12.2 Remove dangling `opencode` symlinks, recreate `opencode` from the `opencode2` alias, re-check resolution, and fail with an actionable report if it still does not resolve
- [x] 12.3 Restore `exec opencode "$@"` in the launcher template

## 13. Verification

- [x] 13.1 Extend the smoke test with a fake `opencode` binary covering restart-on-change and restart-disabled
- [x] 13.2 Update `README.md` and `CHANGELOG.md` for the restart behavior, `{file:}` provider key, and launcher verification
- [x] 13.3 Run tests, lint, `git diff --check`, and `openspec validate --strict`
