# Proposal

## Why

The role is intended to manage AI developer tooling that is agent-neutral and
harness-oriented: spec-driven frameworks, OpenCode configuration, commands,
skills, and a local model runtime. The `install_cursor` task is the only
IDE-specific capability in the role, and it carries its own lifecycle risks
(undocumented download API, unsigned package install with
`disable_gpg_check: true`, root privileges for RPM/DEB). Cursor is better owned
by a dedicated `ansible-role-cursor`, consistent with the existing
VSCode-specific role, so each IDE can evolve and release independently.

## What Changes

- **BREAKING** Remove the `install_cursor` entry from the default `ai_tasks`
  list. Consumers that override `ai_tasks` with an entry named `install_cursor`
  will fail because the task file no longer exists.
- Delete `tasks/install_cursor.yml`, `vars/install_cursor.yml`, and
  `templates/cursor.desktop.j2`.
- Remove the Cursor variables from `defaults/main.yml`: `ai_cursor_version`,
  `ai_cursor_install_method`, `ai_cursor_appimage_dir`.
- Remove Cursor documentation from `README.md`: the "will do" bullet, the three
  key-variable rows, the "Cursor IDE" section, both Cursor example playbooks,
  and `install_cursor` entries in the remaining example `ai_tasks` lists.
- Delete the `cursor-installation` capability spec.
- Reword the `tool-installation` requirement that cites `vars/install_cursor.yml`
  as the pattern exemplar, and add an explicit scope boundary that the role does
  not install IDEs.
- Preserve the Cursor implementation as the starting point for the new
  `ansible-role-cursor` repository, including the behavioral spec scenarios and
  the archived design rationale.

## Capabilities

### New Capabilities

_None. IDE installation moves to a separate role in a separate repository, so it
leaves this role's spec inventory rather than becoming a new capability here._

### Modified Capabilities

- `cursor-installation`: all requirements are removed. The capability is deleted
  from `openspec/specs/` and re-established as the baseline spec of
  `ansible-role-cursor`.
- `tool-installation`: remove the `vars/install_cursor.yml` pattern reference and
  add a requirement that this role does not install IDE-specific tooling.

## Impact

- **Deleted files**: `tasks/install_cursor.yml` (168 lines),
  `vars/install_cursor.yml` (17 lines), `templates/cursor.desktop.j2`
  (17 lines), `openspec/specs/cursor-installation/spec.md` (191 lines).
- **Modified files**: `defaults/main.yml` (task entry and three variables),
  `README.md` (bullet list, key variables table, Cursor section, example
  playbooks), `openspec/specs/tool-installation/spec.md`.
- **Tests**: no change. `tests/` never referenced `install_cursor`; the smoke
  test task lists simply omit it.
- **Untouched historical artifacts**: `CHANGELOG.md`, the archived
  `2026-09-16-install-cursor-ide` change, and the Grafana dashboard description
  that mentions Cursor as an example agent name.
- **Consumer impact**: limited to hosts that explicitly enabled the task. The
  default ships it disabled, so a normal role upgrade is unaffected.
- **Migration**: consumers install `ansible-role-cursor` and add its
  `install_cursor` entry to their playbook or compose both roles in an umbrella
  play.
- **Dependencies**: none added or removed. `community.general` remains required
  for other tasks.
- **Release**: `BREAKING CHANGE` footer on the removal commit; release-please
  bumps the minor version (`0.5.x` → `0.6.0`) while the role is below `1.0.0`.
