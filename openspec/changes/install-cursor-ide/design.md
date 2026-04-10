## Context

The role currently installs CLI tools (OpenCode, OpenSPEC, SpecKit) via npm and uv. It has never managed a GUI application. Cursor IDE is distributed as RPM, DEB, and AppImage through a download API at `api2.cursor.sh`, with no official package repository. The API supports a `latest` version slug and returns 302 redirects to versioned download URLs on `downloads.cursor.com`.

The role supports RedHat-family distributions only (EL, Fedora). Adding Cursor with DEB support would be the first task requiring Debian awareness. The existing task dispatcher (`ai_tasks` in `defaults/main.yml`) and per-task variable files (`vars/<task_name>.yml`) provide a clean extension point.

Users report that Cursor's internal auto-updater conflicts with system-managed installations: it detects new versions but cannot overwrite system-managed paths, causing a persistent update nag on every restart.

## Goals / Non-Goals

**Goals:**
- Provide idempotent Cursor IDE installation that skips download when the installed version matches the target.
- Support RPM, DEB, and AppImage formats with automatic detection based on OS family.
- Allow users to pin a specific version or track `latest`.
- Generate a `.desktop` file for AppImage installations to provide proper desktop integration.
- Follow all existing role patterns (task dispatcher, variable naming, privilege model).

**Non-Goals:**
- Disabling Cursor's internal auto-updater programmatically (no reliable mechanism exists; documented only).
- Managing Cursor configuration or settings (extensions, themes, keybindings).
- Adding a yum/apt repository for Cursor (none exists upstream).
- Supporting macOS or Windows (the role targets Linux only).
- Managing Cursor user-level configuration files.

## Decisions

### Decision 1: Format-flexible installation with auto-detection

The task will support three installation methods (`rpm`, `deb`, `appimage`) controlled by `ai_cursor_install_method`, defaulting to `auto`. Auto-detection resolves as:

| OS Family | Resolved Method |
|-----------|-----------------|
| RedHat    | rpm             |
| Debian    | deb             |
| Other     | appimage        |

**Alternatives considered:**
- *RPM-only*: Simpler but would exclude Debian/Ubuntu users entirely. Since the download API already provides all formats with the same URL pattern, supporting all three requires only conditional logic, not fundamentally different code paths.
- *AppImage-only*: Universal but loses system package manager integration, which is the whole point of solving the update-nag problem.

**Rationale:** Auto-detection follows the role's convention-over-configuration principle. RPM/DEB paths let the system package manager be the single source of truth (solving the update-nag). AppImage provides a graceful fallback for unsupported OS families without requiring `become`.

### Decision 2: Version resolution via redirect inspection

To determine the latest available version, the task will issue a HEAD request to the Cursor download API and extract the full version from the redirect URL's filename. The filename follows predictable patterns:
- RPM: `cursor-<version>.el8.<arch>.rpm`
- DEB: `cursor-<version>_<arch>.deb` (expected pattern)
- AppImage: `Cursor-<version>-<arch>.AppImage`

The version (e.g., `3.0.16`) will be extracted via regex from the `location` header.

**Alternatives considered:**
- *Always download and install*: Simpler (like SpecKit's `--force` pattern) but wastes ~150MB of bandwidth per run and causes unnecessary `changed` status. The user explicitly requested resource-efficient idempotency.
- *Query a version API*: Cursor has no dedicated version-query endpoint. The redirect-inspection approach reuses the download URL we already need.

**Rationale:** A HEAD request is lightweight (~0 bytes transferred) and gives us the exact download URL and version in one step. Comparing this against the installed version enables true idempotency.

### Decision 3: Installed version detection per format

Each installation format has a different method for querying the currently installed version:

| Format   | Detection method                                               |
|----------|----------------------------------------------------------------|
| RPM      | `rpm -q --queryformat '%{VERSION}' cursor`                     |
| DEB      | `dpkg-query -W -f='${Version}' cursor`                        |
| AppImage | Check a version marker file maintained by the task             |

For AppImage, since there is no system package database, the task will write a `.cursor-version` file alongside the AppImage binary containing the installed version string. This is checked on subsequent runs.

**Alternatives considered:**
- *Run `cursor --version`*: Requires the binary to be in PATH and to execute correctly (may launch GUI or require display). Fragile and slow.
- *Parse the AppImage filename*: Requires a naming convention that the task must maintain. Less reliable than an explicit version file.

**Rationale:** RPM/DEB queries are the canonical, zero-cost way to check package versions. The version marker file for AppImage is a lightweight, reliable complement that the task fully controls.

### Decision 4: Platform slug construction in task-scoped variables

The mapping from `(install_method, architecture)` to Cursor API platform slug will be defined in `vars/install_cursor.yml` as a dictionary:

```yaml
_cursor_platform_map:
  rpm:
    x86_64: linux-x64-rpm
    aarch64: linux-arm64-rpm
  deb:
    x86_64: linux-x64-deb
    aarch64: linux-arm64-deb
  appimage:
    x86_64: linux-x64
    aarch64: linux-arm64
```

The resolved slug is looked up as `_cursor_platform_map[resolved_method][ansible_facts['architecture']]`.

**Rationale:** Centralizing the mapping in the vars file keeps the task logic clean and makes it trivial to add new architectures or formats in the future. Follows the role's pattern of putting computed/internal variables in `vars/` files.

### Decision 5: Desktop entry template for AppImage

A Jinja2 template (`templates/cursor.desktop.j2`) will generate a `.desktop` file placed in `~/.local/share/applications/` for AppImage installations only. RPM and DEB packages include their own desktop entries.

The template will reference the AppImage binary path and an icon extracted or bundled with the AppImage (or use a generic icon if extraction is impractical).

**Rationale:** Without a desktop entry, AppImage-installed Cursor would only be launchable from the terminal. This closes the desktop integration gap between AppImage and native packages, making the experience better as the user requested.

### Decision 6: Task ordering and default state

`install_cursor` will be appended as the last entry in `ai_tasks` with `enabled: false`. This means:
- It runs after all CLI tool installations and configuration.
- It is fully opt-in; existing users of the role are unaffected.
- Users enable it by overriding `ai_tasks` or setting the entry to `enabled: true`.

**Rationale:** Cursor is an IDE, not a dependency for the other tools. Placing it last avoids any ordering confusion. Disabled by default respects that IDE choice is personal.

## Risks / Trade-offs

- **[Cursor API stability]** The download API URL pattern and redirect behavior are undocumented. If Cursor changes their API, version resolution and downloads will break. **Mitigation:** The API has been stable across multiple major versions (2.3 through 3.0). The task isolates all API interaction in a few tasks, making fixes localized.

- **[Version extraction fragility]** Parsing the version from the redirect URL filename depends on a consistent naming convention. **Mitigation:** Use a regex that captures the version group from known patterns. Include an assertion task that fails clearly if the pattern doesn't match, rather than silently installing the wrong version.

- **[AppImage desktop integration]** The `.desktop` file requires an icon. AppImages may not reliably expose icons for extraction. **Mitigation:** Use a generic application icon as fallback. Document that users can replace the icon path if they extract one manually.

- **[No Debian vars file yet]** The role's Phase 1 dispatcher always loads `vars/{{ os_family|lower }}.yml`. Running on Debian today would fail because `vars/debian.yml` doesn't exist. **Mitigation:** Create `vars/debian.yml` as part of this change with the same structure as `vars/redhat.yml`. This is necessary even if Cursor is the only DEB-capable task, because the dispatcher loads OS vars unconditionally.

- **[Internal updater nag persists]** Even with Ansible managing the version, Cursor may still show update prompts for builds newer than what Ansible has installed. **Mitigation:** Documentation only. Note in README that the internal updater UI may still appear but the system version is managed by Ansible.
