# Tasks

## 1. Normalize the existing Cursor capability spec

- [x] 1.1 Rewrite `openspec/specs/cursor-installation/spec.md` as a main spec with a `## Purpose` section and a `## Requirements` section containing all 14 existing requirements and their scenarios, unchanged in meaning. Verify with `openspec show cursor-installation --type spec --json` reporting 14 requirements.
- [x] 1.2 Run `openspec validate --specs` and confirm `cursor-installation` no longer produces structural-invalid warnings.

## 2. Remove the Cursor implementation

- [x] 2.1 Delete `tasks/install_cursor.yml`, `vars/install_cursor.yml`, and `templates/cursor.desktop.j2`. Verify with `test ! -e tasks/install_cursor.yml && test ! -e vars/install_cursor.yml && test ! -e templates/cursor.desktop.j2`.
- [x] 2.2 Remove the `install_cursor` entry from `ai_tasks` and the `ai_cursor_version`, `ai_cursor_install_method`, and `ai_cursor_appimage_dir` variables from `defaults/main.yml`. Verify with `grep -ri cursor defaults/ tasks/ vars/ templates/` returning no matches.
- [x] 2.3 Run `make lint` and confirm `yamllint` and the Ansible syntax check pass with the reduced task list.
- [x] 2.4 Run `make test` and confirm the smoke test and PR-workflow unit tests pass unchanged.

## 3. Remove Cursor documentation from the README

- [x] 3.1 Remove the Cursor bullet from the role summary, the three `ai_cursor_*` rows from the key variables table, and the `install_cursor` entries from every example `ai_tasks` list. Verify with `grep -n "install_cursor\|ai_cursor_" README.md` returning no matches.
- [x] 3.2 Remove the "Cursor IDE" section and the two Cursor example playbooks, replacing them with a short "Migrating to 0.6.0" note that points to `ansible-role-cursor` and lists the `ai_cursor_*` to `cursor_*` renames. Verify the note appears exactly once and the README heading structure remains intact.

## 4. Remove the Cursor capability from this role's specs

- [x] 4.1 Confirm the `cursor-installation` delta in this change removes all 14 requirements, each with `**Reason**` and `**Migration**`. Verify with `openspec validate remove-cursor-installation` reporting valid.
- [x] 4.2 Confirm the `tool-installation` delta removes the `vars/install_cursor.yml` reference and adds the "Role scope excludes IDE installation" requirement. Verify with `openspec show tool-installation --type spec --json` still reporting 4 requirements before archive.

## 5. Integration verification

- [x] 5.1 Run the full test suite from a clean checkout with `make test` and `make lint`, confirming no target references Cursor.
- [x] 5.2 Confirm the role still deploys the expected configuration by inspecting the smoke-test assertions for `opencode.json`, commands, skills, wrapper, and PR workflow helper; all must pass with no Cursor-related assertion changes.

## Workflow follow-up

- Archive this change after review, then verify `openspec/specs/cursor-installation/` no longer exists and `tool-installation` contains the new scope requirement.
- Commit the removal with a `BREAKING CHANGE` footer so release-please produces `0.6.0`, and confirm the generated changelog entry names the removed task.
- In the new `ansible-role-cursor` repository, port `tasks/install_cursor.yml`, `vars/install_cursor.yml`, `templates/cursor.desktop.j2`, and the 14 requirements as the baseline spec, renaming `ai_cursor_*` to `cursor_*`.
- Add `ansible-role-cursor` scaffolding (meta, README, Makefile, `.yamllint`, release-please, Galaxy publish workflow) and at minimum a syntax check plus an AppImage-path integration test before its first release.
