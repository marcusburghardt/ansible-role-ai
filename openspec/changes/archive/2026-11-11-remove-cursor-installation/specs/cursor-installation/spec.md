# Spec Delta

## REMOVED Requirements

### Requirement: Install Cursor IDE task is disabled by default
**Reason**: The role no longer manages IDE installation. Cursor ownership moves
to the dedicated `ansible-role-cursor` repository.
**Migration**: Enable the `install_cursor` task in `ansible-role-cursor` and add
that role to the playbook. Hosts that never enabled the task require no action.

### Requirement: Support configurable installation method with auto-detection
**Reason**: Installation-format selection is part of the Cursor-specific
capability and moves with it.
**Migration**: Set `cursor_install_method` (`auto`, `rpm`, `deb`, `appimage`) in
`ansible-role-cursor`. The auto-detection rules are unchanged.

### Requirement: Support version pinning and latest tracking
**Reason**: Cursor version resolution belongs to the Cursor role.
**Migration**: Set `cursor_version` in `ansible-role-cursor` (`latest` or a
major.minor pin such as `3.0`). The resolved full version is still used for
idempotency.

### Requirement: Idempotent installation with version comparison
**Reason**: Idempotency is a property of the moved Cursor task.
**Migration**: No consumer action. `ansible-role-cursor` compares installed and
resolved versions before downloading, exactly as before.

### Requirement: Platform slug resolution from method and architecture
**Reason**: The Cursor download API mapping is Cursor-specific.
**Migration**: No consumer action. The platform map moves to
`vars/install_cursor.yml` in `ansible-role-cursor`.

### Requirement: Download Cursor package to temporary location
**Reason**: Package acquisition is part of Cursor installation.
**Migration**: No consumer action.

### Requirement: Install RPM and DEB packages via system package manager
**Reason**: Package installation is part of Cursor installation.
**Migration**: No consumer action. RPM and DEB paths still require privilege
escalation.

### Requirement: Desktop entry for AppImage installations
**Reason**: Desktop integration is Cursor-specific and only applies to AppImage.
**Migration**: No consumer action. `ansible-role-cursor` still deploys
`cursor.desktop` for AppImage installs.

### Requirement: AppImage version marker file
**Reason**: The marker file exists only to support Cursor AppImage idempotency.
**Migration**: No consumer action. A stale `~/.local/bin/.cursor-version` may be
removed manually if Cursor is uninstalled.

### Requirement: Per-task variable file with platform mapping
**Reason**: The `_cursor_*` variables move with the task.
**Migration**: Consumers who referenced `_cursor_*` internals directly should
stop doing so; the variables are internal and now scoped to the new role.

### Requirement: Temporary file cleanup after installation
**Reason**: Cleanup applies only to the moved installation flow.
**Migration**: No consumer action.

### Requirement: Task naming follows role convention
**Reason**: The task is removed from this role's task inventory.
**Migration**: No consumer action. The new role applies its own naming
convention to the moved task.

### Requirement: User-facing variables use ai_ prefix
**Reason**: The role-level `ai_cursor_*` variables are removed. The new role
uses its own prefix to avoid cross-role collisions.
**Migration**: Rename playbook variables: `ai_cursor_version` →
`cursor_version`, `ai_cursor_install_method` → `cursor_install_method`,
`ai_cursor_appimage_dir` → `cursor_appimage_dir`.

### Requirement: README documents Cursor installation
**Reason**: Cursor documentation leaves this role's README.
**Migration**: Refer to the `ansible-role-cursor` README for task documentation,
variables, examples, and the built-in-updater caveat.
