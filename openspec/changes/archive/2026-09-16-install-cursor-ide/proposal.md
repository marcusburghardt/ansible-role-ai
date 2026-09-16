## Why

Cursor IDE users on Linux face a persistent update-nag problem: the IDE's built-in updater detects new versions and prompts to update, but when Cursor was installed via RPM (or DEB), the internal updater cannot write to system-managed paths. The update fails silently, and the nag returns on every restart. Managing Cursor installation and updates through Ansible resolves this by making the system package manager the single source of truth for the installed version. Since IDE choice is personal, this task must be optional and disabled by default.

## What Changes

- Add a new `install_cursor` sub-task that downloads and installs Cursor IDE on Linux systems.
- Support three installation formats: RPM, DEB, and AppImage, with automatic detection based on OS family and user override capability.
- Implement version-aware idempotency: query the installed version before downloading, skip installation when versions match.
- Generate a `.desktop` file for the AppImage installation path so Cursor integrates properly with desktop environments (RPM/DEB packages already include their own).
- Add new variables (`ai_cursor_version`, `ai_cursor_install_method`) following existing `ai_` prefix conventions.
- Append `install_cursor` to the `ai_tasks` list as the last entry with `enabled: false`.
- Add a corresponding `vars/install_cursor.yml` for task-scoped internal variables (platform slug mapping, download URL construction).
- Update `README.md` to document the new task, its variables, and a note about Cursor's internal updater behavior.

## Capabilities

### New Capabilities
- `cursor-installation`: Covers the download, version resolution, idempotent installation, and desktop integration of Cursor IDE across RPM, DEB, and AppImage formats.

### Modified Capabilities
_(none -- this is a new, self-contained task that follows existing patterns without changing requirements for other capabilities)_

## Impact

- **New files**: `tasks/install_cursor.yml`, `vars/install_cursor.yml`, a Jinja2 template for the `.desktop` file (AppImage case).
- **Modified files**: `defaults/main.yml` (new variables and `ai_tasks` entry), `README.md` (documentation), `meta/main.yml` (add Debian/Ubuntu platforms if DEB support is included).
- **Dependencies**: No new Ansible collections required. Uses `ansible.builtin.uri` (for API queries), `ansible.builtin.get_url` (for download), `ansible.builtin.package`/`ansible.builtin.apt`/`ansible.builtin.dnf` (for RPM/DEB install), and `ansible.builtin.copy`/`ansible.builtin.template` (for AppImage and desktop entry).
- **Privilege escalation**: RPM and DEB paths require `become: true`; AppImage path operates in user space without escalation.
- **Network**: Requires HTTPS access to `api2.cursor.sh` and `downloads.cursor.com` during execution.
