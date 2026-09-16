## 1. Task-scoped Variables and Platform Mapping

- [x] 1.1 Create `vars/install_cursor.yml` with `_cursor_platform_map` dictionary mapping `(method, architecture)` to API platform slugs, and `_cursor_download_base_url` pointing to `https://api2.cursor.sh/updates/download/golden`

## 2. Default Variables

- [x] 2.1 Add Cursor variables to `defaults/main.yml`: `ai_cursor_version` (default `latest`), `ai_cursor_install_method` (default `auto`), `ai_cursor_appimage_dir` (default `{{ ai_user_home_dir }}/.local/bin`)
- [x] 2.2 Append `{ enabled: false, name: 'install_cursor' }` as the last entry in `ai_tasks`

## 3. Core Task File

- [x] 3.1 Create `tasks/install_cursor.yml` with install method resolution logic: resolve `auto` to `rpm`/`deb`/`appimage` based on `ansible_facts['os_family']`, or use the explicit value when not `auto`
- [x] 3.2 Add platform slug resolution using `_cursor_platform_map[resolved_method][ansible_facts['architecture']]`
- [x] 3.3 Add version resolution via HEAD request to the Cursor download API, extracting the full version and download URL from the redirect `location` header using a regex
- [x] 3.4 Add assertion task that fails with a clear message if the version regex extraction does not match
- [x] 3.5 Add installed version detection: `rpm -q` for RPM, `dpkg-query` for DEB, read `.cursor-version` file for AppImage (register results, ignore errors for not-installed case)
- [x] 3.6 Add version comparison logic that sets a `_cursor_install_needed` fact based on whether installed version matches target version
- [x] 3.7 Add download task using `ansible.builtin.get_url` to fetch the package to a temporary directory, conditioned on `_cursor_install_needed`
- [x] 3.8 Add RPM installation task using `ansible.builtin.dnf` with `become: true`, conditioned on `_cursor_install_needed` and resolved method being `rpm`
- [x] 3.9 Add DEB installation task using `ansible.builtin.apt` with `deb` parameter and `become: true`, conditioned on `_cursor_install_needed` and resolved method being `deb`
- [x] 3.10 Add AppImage installation task: copy to `ai_cursor_appimage_dir` with mode `0750`, write `.cursor-version` marker file, conditioned on `_cursor_install_needed` and resolved method being `appimage`
- [x] 3.11 Add temporary file cleanup task to remove the downloaded package after RPM/DEB installation

## 4. Desktop Entry Template

- [x] 4.1 Create `templates/cursor.desktop.j2` with standard `.desktop` file structure referencing the AppImage binary path and a generic icon fallback
- [x] 4.2 Add task in `install_cursor.yml` to deploy the desktop entry to `~/.local/share/applications/cursor.desktop`, conditioned on resolved method being `appimage`

## 5. Documentation

- [x] 5.1 Update `README.md` to document the `install_cursor` task: available variables, how to enable it, usage examples for RPM/DEB/AppImage, and a note about Cursor's built-in updater nag behavior

## 6. Galaxy Metadata

- [x] 6.1 Add Debian and Ubuntu platform entries to `meta/main.yml` to reflect DEB support
