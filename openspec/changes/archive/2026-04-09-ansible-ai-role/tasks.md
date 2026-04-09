## 1. Role Foundation and Dispatcher

- [x] 1.1 Update `meta/main.yml` with proper Galaxy metadata (author: Marcus Burghardt, license: Apache-2.0, min_ansible_version: 2.16, platforms: EL and Fedora, galaxy_tags: ai, opencode, developer-tools)
- [x] 1.2 Populate `defaults/main.yml` with the `ai_tasks` list (install_dependencies disabled by default, then install_opencode, configure_opencode, install_openspec, install_speckit all enabled by default) and all user-overridable variables (versions, models, GCP settings, paths, script name)
- [x] 1.3 Implement `tasks/main.yml` with the 3-phase dispatcher pattern: load OS vars, loop-include task vars for enabled tasks, loop-include task files for enabled tasks
- [x] 1.4 Create `vars/redhat.yml` with OS-family-specific package list (nodejs, npm, uv)

## 2. System Dependencies

- [x] 2.1 Create `vars/install_dependencies.yml` (task-scoped variables placeholder)
- [x] 2.2 Create `tasks/install_dependencies.yml` with task to install system packages from `{{ packages }}` using ansible.builtin.package with become: true and state: present

## 3. OpenCode Installation

- [x] 2.1 Create `vars/install_opencode.yml` (task-scoped variables placeholder)
- [x] 2.2 Create `tasks/install_opencode.yml` with tasks to ensure ~/.npm directory exists and install opencode-ai via npm globally with latest/pinned version support and become: true

## 4. OpenSPEC Installation

- [x] 4.1 Create `vars/install_openspec.yml` (task-scoped variables placeholder)
- [x] 4.2 Create `tasks/install_openspec.yml` with task to install @fission-ai/openspec via npm globally with latest/pinned version support and become: true

## 5. SpecKit Installation

- [x] 5.1 Create `vars/install_speckit.yml` (task-scoped variables placeholder)
- [x] 5.2 Create `tasks/install_speckit.yml` with tasks to resolve latest version from GitHub API (when ai_speckit_version is latest), set resolved version fact, and install via uv tool install --force without become

## 6. OpenCode Configuration

- [x] 6.1 Create `vars/configure_opencode.yml` (task-scoped variables for config paths)
- [x] 6.2 Create `templates/opencode.json.j2` with Jinja2 template for OpenCode config file using role variables for model, provider, permissions, compaction settings
- [x] 6.3 Create `templates/ai_agent_script.sh.j2` with Jinja2 template for the wrapper script that exports GCP env vars and launches opencode
- [x] 6.4 Create `files/commands/checkout_pr.md` command definition file (PR checkout workflow)
- [x] 6.5 Create `files/commands/review_pr.md` command definition file (PR review fallback for non-synced repos, sourced from org-infra)
- [x] 6.6 Create `files/commands/refresh.md` command definition file (detect OpenSpec/SpecKit in current repo and run the appropriate update command to refresh per-repo framework artifacts)
- [x] 6.7 Create `tasks/configure_opencode.yml` with tasks to: ensure scripts dir exists, ensure config dir and subdirs (command/, skills/) exist, deploy opencode.json from template, deploy wrapper script from template, copy managed command files (checkout_pr.md, review_pr.md, refresh.md)

## 8. README and Documentation

- [x] 8.1 Replace `README.md` boilerplate with proper documentation following sibling role pattern: role description, requirements (npm, uv, community.general collection), role variables reference, example playbooks (minimal, with install_dependencies, with pinned versions, with selective tasks), license (Apache-2.0), and author info

## 9. OpenCode Instructions and Security Improvements

- [x] 9.1 Add `ai_opencode_instructions` variable to `defaults/main.yml` defaulting to `[".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]` (SpecKit-standard constitution path)
- [x] 9.2 Update `templates/opencode.json.j2` to use `ai_opencode_instructions` variable for the instructions array instead of hardcoded `["CLAUDE.md"]`
- [x] 9.3 Add `ai_trusted_github_orgs` list variable to `defaults/main.yml` defaulting to empty list `[]`
- [x] 9.4 Update `templates/ai_agent_script.sh.j2` to export `TRUSTED_GITHUB_ORGS` env var from `ai_trusted_github_orgs` (comma-separated)
- [x] 9.5 Update `files/commands/checkout_pr.md` to include pre-flight org verification step checking `TRUSTED_GITHUB_ORGS` env var
- [x] 9.6 Update `files/commands/review_pr.md` to include pre-flight org verification step checking `TRUSTED_GITHUB_ORGS` env var, and update constitution reference from root `constitution.md` to `.specify/memory/constitution.md`

## 11. Sensitive Defaults and Galaxy Readiness

- [x] 11.1 Replace `ai_gcp_project` default in `defaults/main.yml` with safe placeholder `your-gcp-project`
- [x] 11.2 Replace `ai_vertex_location` default in `defaults/main.yml` from `us-east5` to `us-central1`
- [x] 11.3 Update `README.md` to add a Vertex AI configuration note explaining that `ai_gcp_project` and `ai_vertex_location` must be set when using Vertex, and that they are ignored otherwise. Also document `ai_trusted_github_orgs` usage.
- [x] 11.4 Update `tests/test.yml` to disable install tasks (install_dependencies, install_opencode, install_openspec, install_speckit) and only enable configure_opencode for a runnable smoke test
- [x] 11.5 Create `.yamllint` configuration file with rules appropriate for Ansible roles

## 13. License Headers and Agent-Neutral Skills

- [x] 13.1 Fix SPDX license headers in `vars/main.yml`, `handlers/main.yml`, and `tests/inventory` from `MIT-0` to `Apache-2.0`
- [x] 13.2 Add task to `tasks/configure_opencode.yml` to ensure `~/.agents/skills/` directory exists (agent-neutral skills path)
- [x] 13.3 Update `README.md` to guide users toward `~/.agents/skills/` for cross-agent-portable custom skills, and note that `~/.config/opencode/command/` is OpenCode-specific (no agent-neutral command path exists)

## 15. Commit Standards Instruction File

- [x] 15.1 Create `files/commit.md` with universal commit standards (Conventional Commits, Signed-off-by, Assisted-by) and explicit deference to repository-level guidelines
- [x] 15.2 Update `ai_opencode_instructions` default in `defaults/main.yml` to prepend `~/.config/opencode/commit.md` as the first entry (lowest precedence baseline)
- [x] 15.3 Add task to `tasks/configure_opencode.yml` to deploy `commit.md` to `~/.config/opencode/commit.md` using `ansible.builtin.copy`
- [x] 15.4 Update `README.md` to document the commit standards baseline and repo-level override behavior

## 16. Validation

- [x] 16.1 Verify `commit.md` is first in the `ai_opencode_instructions` default list
- [x] 16.2 Verify `commit.md` deployment task exists in `configure_opencode.yml`
- [x] 16.3 Run yamllint against all YAML files and verify they pass
