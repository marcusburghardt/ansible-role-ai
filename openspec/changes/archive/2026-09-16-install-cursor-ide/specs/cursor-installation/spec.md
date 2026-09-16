## ADDED Requirements

### Requirement: Install Cursor IDE task is disabled by default
The `defaults/main.yml` file SHALL include an `install_cursor` entry in the `ai_tasks` list as the last entry with `enabled: false`. This ensures existing role consumers are unaffected and Cursor installation is fully opt-in.

#### Scenario: Default ai_tasks does not enable Cursor installation
- **WHEN** the role is used without overriding `ai_tasks`
- **THEN** the `install_cursor` entry SHALL have `enabled: false` and SHALL be the last entry in the list

#### Scenario: Consumer enables Cursor installation
- **WHEN** the consumer sets the `install_cursor` entry to `enabled: true` in `ai_tasks`
- **THEN** the Cursor installation task SHALL execute

### Requirement: Support configurable installation method with auto-detection
The role SHALL provide an `ai_cursor_install_method` variable defaulting to `auto`. When set to `auto`, the resolved installation method SHALL be determined by the target host's OS family: `rpm` for RedHat, `deb` for Debian, and `appimage` for any other OS family. Users SHALL be able to override auto-detection by setting the variable to `rpm`, `deb`, or `appimage` explicitly.

#### Scenario: Auto-detect RPM on RedHat family
- **WHEN** `ai_cursor_install_method` is `auto` and the target host OS family is RedHat
- **THEN** the resolved installation method SHALL be `rpm`

#### Scenario: Auto-detect DEB on Debian family
- **WHEN** `ai_cursor_install_method` is `auto` and the target host OS family is Debian
- **THEN** the resolved installation method SHALL be `deb`

#### Scenario: Auto-detect AppImage on unsupported OS family
- **WHEN** `ai_cursor_install_method` is `auto` and the target host OS family is neither RedHat nor Debian
- **THEN** the resolved installation method SHALL be `appimage`

#### Scenario: User overrides install method
- **WHEN** `ai_cursor_install_method` is set to `appimage` and the target host OS family is RedHat
- **THEN** the resolved installation method SHALL be `appimage`, ignoring the OS family

### Requirement: Support version pinning and latest tracking
The role SHALL provide an `ai_cursor_version` variable defaulting to `latest`. When set to `latest`, the task SHALL resolve the current latest version from the Cursor download API. When set to a specific major.minor version (e.g., `3.0`), the task SHALL resolve the full version for that release. The resolved full version (e.g., `3.0.16`) SHALL be used for idempotency comparison.

#### Scenario: Resolve latest version from API
- **WHEN** `ai_cursor_version` is `latest`
- **THEN** the task SHALL issue a HEAD request to `https://api2.cursor.sh/updates/download/golden/{platform_slug}/cursor/latest` and extract the full version from the redirect URL filename

#### Scenario: Resolve pinned version from API
- **WHEN** `ai_cursor_version` is set to `3.0`
- **THEN** the task SHALL issue a HEAD request to `https://api2.cursor.sh/updates/download/golden/{platform_slug}/cursor/3.0` and extract the full version from the redirect URL filename

#### Scenario: Version extraction fails gracefully
- **WHEN** the redirect URL filename does not match the expected pattern
- **THEN** the task SHALL fail with a clear error message indicating the version could not be extracted

### Requirement: Idempotent installation with version comparison
The task SHALL compare the resolved target version against the currently installed version before downloading. If the versions match, the task SHALL skip download and installation. If they differ or no version is installed, the task SHALL proceed with download and installation.

#### Scenario: Skip installation when versions match (RPM)
- **WHEN** the resolved method is `rpm` and `rpm -q --queryformat '%{VERSION}' cursor` returns a version matching the resolved target version
- **THEN** the task SHALL skip download and installation and report no changes

#### Scenario: Skip installation when versions match (DEB)
- **WHEN** the resolved method is `deb` and `dpkg-query -W -f='${Version}' cursor` returns a version matching the resolved target version
- **THEN** the task SHALL skip download and installation and report no changes

#### Scenario: Skip installation when versions match (AppImage)
- **WHEN** the resolved method is `appimage` and the version marker file contains a version matching the resolved target version
- **THEN** the task SHALL skip download and installation and report no changes

#### Scenario: Proceed with installation when versions differ
- **WHEN** the installed version does not match the resolved target version
- **THEN** the task SHALL download the Cursor package from the resolved download URL and install it

#### Scenario: Proceed with installation when not installed
- **WHEN** Cursor is not currently installed (query returns no result or marker file does not exist)
- **THEN** the task SHALL download the Cursor package from the resolved download URL and install it

### Requirement: Platform slug resolution from method and architecture
The task SHALL resolve the Cursor download API platform slug from the combination of the resolved installation method and the target host's CPU architecture (`ansible_facts['architecture']`). The mapping SHALL be defined in `vars/install_cursor.yml` and SHALL support both `x86_64` and `aarch64` architectures for all three installation methods.

#### Scenario: Resolve RPM x64 platform slug
- **WHEN** the resolved method is `rpm` and the architecture is `x86_64`
- **THEN** the platform slug SHALL be `linux-x64-rpm`

#### Scenario: Resolve RPM ARM64 platform slug
- **WHEN** the resolved method is `rpm` and the architecture is `aarch64`
- **THEN** the platform slug SHALL be `linux-arm64-rpm`

#### Scenario: Resolve DEB x64 platform slug
- **WHEN** the resolved method is `deb` and the architecture is `x86_64`
- **THEN** the platform slug SHALL be `linux-x64-deb`

#### Scenario: Resolve DEB ARM64 platform slug
- **WHEN** the resolved method is `deb` and the architecture is `aarch64`
- **THEN** the platform slug SHALL be `linux-arm64-deb`

#### Scenario: Resolve AppImage x64 platform slug
- **WHEN** the resolved method is `appimage` and the architecture is `x86_64`
- **THEN** the platform slug SHALL be `linux-x64`

#### Scenario: Resolve AppImage ARM64 platform slug
- **WHEN** the resolved method is `appimage` and the architecture is `aarch64`
- **THEN** the platform slug SHALL be `linux-arm64`

### Requirement: Download Cursor package to temporary location
When installation is needed, the task SHALL download the Cursor package from the resolved redirect URL to a temporary directory. The download SHALL use `ansible.builtin.get_url` with HTTPS. The temporary file SHALL be cleaned up after installation.

#### Scenario: Download RPM package
- **WHEN** the resolved method is `rpm` and installation is needed
- **THEN** the task SHALL download the RPM file to a temporary path and install it using the system package manager with `become: true`

#### Scenario: Download DEB package
- **WHEN** the resolved method is `deb` and installation is needed
- **THEN** the task SHALL download the DEB file to a temporary path and install it using `ansible.builtin.apt` with `become: true`

#### Scenario: Download AppImage
- **WHEN** the resolved method is `appimage` and installation is needed
- **THEN** the task SHALL download the AppImage file to `ai_cursor_appimage_dir` (defaulting to `{{ ai_user_home_dir }}/.local/bin`), set it as executable (mode `0750`), and update the version marker file

### Requirement: Install RPM and DEB packages via system package manager
RPM packages SHALL be installed using `ansible.builtin.dnf` (or `ansible.builtin.package`) with `become: true`. DEB packages SHALL be installed using `ansible.builtin.apt` with `become: true` and `deb` parameter pointing to the downloaded file. Both methods SHALL use the system package manager as the authoritative source for the installed version.

#### Scenario: RPM installation with privilege escalation
- **WHEN** the resolved method is `rpm`
- **THEN** the installation task SHALL use `become: true` and install via the system package manager

#### Scenario: DEB installation with privilege escalation
- **WHEN** the resolved method is `deb`
- **THEN** the installation task SHALL use `become: true` and install via `ansible.builtin.apt` with the `deb` parameter

#### Scenario: AppImage installation without privilege escalation
- **WHEN** the resolved method is `appimage`
- **THEN** the installation task SHALL NOT use `become: true`

### Requirement: Desktop entry for AppImage installations
When the resolved method is `appimage`, the task SHALL generate a `.desktop` file at `~/.local/share/applications/cursor.desktop` using a Jinja2 template (`templates/cursor.desktop.j2`). The desktop entry SHALL reference the AppImage binary path as `Exec` and use a generic icon as fallback. RPM and DEB installations SHALL NOT generate a desktop entry (their packages include one).

#### Scenario: Desktop entry created for AppImage
- **WHEN** the resolved method is `appimage` and Cursor is installed
- **THEN** a `cursor.desktop` file SHALL exist at `~/.local/share/applications/cursor.desktop` with the correct `Exec` path pointing to the AppImage binary

#### Scenario: Desktop entry not created for RPM
- **WHEN** the resolved method is `rpm`
- **THEN** the task SHALL NOT create a `.desktop` file

#### Scenario: Desktop entry not created for DEB
- **WHEN** the resolved method is `deb`
- **THEN** the task SHALL NOT create a `.desktop` file

### Requirement: AppImage version marker file
When the resolved method is `appimage`, the task SHALL maintain a version marker file at `{{ ai_cursor_appimage_dir }}/.cursor-version` containing only the installed version string. This file SHALL be created or updated on every successful AppImage installation and SHALL be read on subsequent runs for version comparison.

#### Scenario: Version marker created on AppImage install
- **WHEN** the resolved method is `appimage` and a new version is installed
- **THEN** a `.cursor-version` file SHALL be written to `ai_cursor_appimage_dir` containing the installed version string

#### Scenario: Version marker read for comparison
- **WHEN** the resolved method is `appimage` and a `.cursor-version` file exists
- **THEN** its contents SHALL be used as the installed version for comparison against the target version

### Requirement: Per-task variable file with platform mapping
A `vars/install_cursor.yml` file SHALL define the `_cursor_platform_map` dictionary that maps `(install_method, architecture)` to Cursor download API platform slugs. It SHALL also define the download base URL and any other internal variables needed by the task. Variable names SHALL be prefixed with `_cursor_` to indicate internal scope.

#### Scenario: Platform map covers all format-architecture combinations
- **WHEN** `vars/install_cursor.yml` is loaded
- **THEN** `_cursor_platform_map` SHALL contain entries for `rpm`, `deb`, and `appimage` methods, each with `x86_64` and `aarch64` sub-keys

### Requirement: Temporary file cleanup after installation
After RPM or DEB installation, the downloaded package file in the temporary directory SHALL be removed. This prevents stale files from accumulating on the target host.

#### Scenario: RPM temp file cleaned up
- **WHEN** an RPM package is downloaded and installed
- **THEN** the temporary RPM file SHALL be removed after installation completes

#### Scenario: DEB temp file cleaned up
- **WHEN** a DEB package is downloaded and installed
- **THEN** the temporary DEB file SHALL be removed after installation completes

### Requirement: Task naming follows role convention
All tasks in `tasks/install_cursor.yml` SHALL follow the naming pattern `"{{ role_name }} | {{ task.name }} | <action description>"` consistent with all other task files in the role.

#### Scenario: Task names are hierarchical
- **WHEN** any task in `install_cursor.yml` executes
- **THEN** its `name` field SHALL follow the `{{ role_name }} | {{ task.name }} | <description>` pattern

### Requirement: User-facing variables use ai_ prefix
All new user-facing variables introduced for Cursor installation SHALL use the `ai_` prefix: `ai_cursor_version`, `ai_cursor_install_method`, `ai_cursor_appimage_dir`. These SHALL be defined with defaults in `defaults/main.yml`.

#### Scenario: Cursor variables have ai_ prefix
- **WHEN** examining `defaults/main.yml`
- **THEN** all Cursor-related variable names SHALL start with `ai_cursor_`

### Requirement: README documents Cursor installation
The `README.md` SHALL be updated to document the `install_cursor` task, its variables, usage examples, and a note explaining that Cursor's built-in updater may still display update prompts even when the version is managed by Ansible.

#### Scenario: README includes Cursor documentation
- **WHEN** a user reads the README
- **THEN** it SHALL contain a section describing the `install_cursor` task, how to enable it, available variables, and the internal updater caveat
