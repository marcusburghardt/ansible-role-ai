## Context

The `ansible-role-ai` repository contains a freshly scaffolded, empty Ansible role. The organization maintains three mature sibling roles (`ansible-role-devsecops`, `ansible-role-git`, `ansible-role-vim`) that all follow an identical 3-phase dispatcher architecture with data-driven task selection. A monolithic playbook (`ai_opencode.yml`) currently handles AI tool installation and configuration inline, without role encapsulation. This role needs to absorb that playbook's functionality while conforming to the established role patterns and being extensible for future AI tools beyond OpenCode.

Target platforms are RHEL-family distributions (Fedora, EL), matching sibling roles. The role will be consumed by playbooks that currently use `ai_opencode.yml` directly.

## Goals / Non-Goals

**Goals:**
- Implement a fully functional Ansible role that installs and configures AI developer tools, starting with OpenCode, OpenSPEC, and SpecKit.
- Follow the exact same 3-phase dispatcher pattern used by sibling roles for consistency and maintainability.
- Allow consumers to selectively enable/disable individual tool installations and configurations via the `ai_tasks` variable.
- Support both `latest` (auto-update) and pinned version semantics for all tools.
- Deploy OpenCode user-level configuration, including the config file, wrapper script, commands, and skills.
- Structure the role so adding new AI agents in the future requires only adding new task/var files and a new entry in the `ai_tasks` list.

**Non-Goals:**
- Supporting non-RHEL platforms (Debian, macOS) in this initial implementation. OS-specific variable files can be added later.
- Managing per-project OpenCode configurations (`.opencode/` directories inside repositories). This role manages only user-level (`~/.config/opencode/`) configuration.
- Implementing Molecule tests or CI/CD pipelines -- those are a separate concern.
- Managing GCP authentication or credential setup -- only environment variable exports via the wrapper script.

## Decisions

### 1. Follow the 3-phase dispatcher pattern exactly

**Decision**: Use `include_vars` for OS vars, then loop-based `include_vars` and `include_tasks` over the `ai_tasks` list with `when: task.enabled` guards.

**Rationale**: All three sibling roles use this identical pattern. Deviating would create cognitive overhead for contributors who work across these roles. The pattern is proven and well-understood within the organization.

**Alternatives considered**: Using Ansible tags for task selection. Rejected because no sibling role uses tags -- the variable-driven approach is the established convention.

### 2. Separate sub-tasks per tool rather than a single install-all task

**Decision**: Create individual sub-tasks: `install_opencode`, `install_openspec`, `install_speckit`, `configure_opencode`. Each has its own task file and variable file.

**Rationale**: Granularity is a stated requirement. Users may want to install only OpenCode without SpecKit, or skip configuration to manage it themselves. This also makes the role trivially extensible -- adding a new tool is adding two files and one list entry.

**Alternatives considered**: A single `install_tools` task that installs everything. Rejected because it violates the granularity requirement and the patterns seen in sibling roles (e.g., `ansible-role-git` separates `configure_git`, `configure_ps`, `add_supporting_scripts`, `synchronize_repos`).

### 3. Use Jinja2 templates for configuration files instead of static copies

**Decision**: Use `templates/opencode.json.j2` and `templates/ai_agent_script.sh.j2` instead of `files/` with `ansible.builtin.copy`.

**Rationale**: The reference playbook hardcodes GCP project, model names, and paths into the config file and script. Templates allow these values to be driven by variables, making the role reusable across teams with different GCP projects or model preferences.

**Alternatives considered**: Using `ansible.builtin.copy` with `content:` inline (as the reference playbook does). Rejected because the config file is complex JSON and inline content in YAML is fragile and hard to maintain.

### 4. Deploy Ansible-managed commands and skills as static files to user config

**Decision**: Ship specific OpenCode commands as static files under `files/commands/` in the role, deployed to `~/.config/opencode/command/`. Initial commands: `checkout_pr.md` (personal workflow) and `review_pr.md` (fallback for repos not yet synced by org-infra). Skills directory is created but ships empty initially. The role manages **specific named files only** -- it does not scan, delete, or modify any other files in the target directories. Ansible-managed files are overwritten on every run (standard desired-state enforcement). Users who want to customize managed commands update the role's source, not the deployed files. Users are free to create their own commands and skills alongside managed ones without conflict.

**Rationale**: This aligns with the org-infra AI tooling standard (spec 004), which defines three layers: (1) org-synced repo-level files managed by `sync-config.yml`, (2) framework-managed commands installed by tool plugins (gitignored), (3) user-level config in `~/.config/opencode/`. The Ansible role operates exclusively on layer 3. The `review_pr` command is also synced to repos by org-infra (layer 1), but deploying it at user-level provides coverage for repositories that haven't adopted the org standard yet -- repo-level takes precedence when both exist. Commands and skills have no variables requiring substitution, so static files (not templates) are the appropriate mechanism.

**Alternatives considered**: (a) Using templates for commands/skills. Rejected because these files have no variables that need substitution. (b) Deploying all commands from the org-infra repo. Rejected because org-infra sync handles repo-level distribution -- the role should not duplicate that mechanism. (c) Using `force: no` to avoid overwriting user edits. Rejected because managed files should always reflect the role's source of truth -- users who want changes update the role, not the deployed file.

### 5. Version handling pattern: `latest` vs pinned

**Decision**: For npm packages (OpenCode, OpenSPEC), use `state: latest` when version is `latest`, otherwise `state: present` with explicit version. For SpecKit (GitHub release + uv), resolve `latest` via GitHub API, then install via `uv tool install` with `--force`.

**Rationale**: This exactly mirrors the proven pattern from the reference playbook. The npm module natively supports `state: latest`, while SpecKit requires manual resolution because it's installed from a Git URL.

**Alternatives considered**: Always installing latest regardless of configuration. Rejected because pinned versions are essential for reproducible environments.

### 6. Opt-in system dependency installation via `install_dependencies`

**Decision**: Add an `install_dependencies` sub-task that installs system-level prerequisites (nodejs, npm, uv) using `ansible.builtin.package`. This task is disabled by default (`enabled: false`) in the `ai_tasks` list and placed first in the task order.

**Rationale**: The sibling roles establish a clear precedent -- `ansible-role-devsecops` installs `python3-pip`, `golang`, etc. as system packages in its `install_tools` task, and downstream tasks depend on them. The AI role has the same dependency chain: npm is required for OpenCode/OpenSPEC, uv is required for SpecKit. However, unlike devsecops where every user needs the tools installed, AI tool users are more likely to already have npm/uv present. Defaulting to disabled avoids surprising users with system package changes they didn't request, while giving fresh-machine users a single flag to opt in.

**Alternatives considered**: (a) Always install prerequisites (as devsecops does). Rejected because the primary audience already has these tools. (b) Keep prerequisites as a pure external concern (the original non-goal). Rejected because it creates a poor experience for new users on fresh machines -- the role would simply fail with an unhelpful npm-not-found error. (c) Use pip or curl for uv installation. Rejected in favor of system packages for consistency with the `ansible.builtin.package` pattern used across all sibling roles.

### 7. Variable naming convention: `ai_` prefix

**Decision**: All role variables use the `ai_` prefix (e.g., `ai_tasks`, `ai_opencode_version`, `ai_model`).

**Rationale**: Follows the established convention where each role's variables are prefixed with the role's short name (e.g., `devsecops_`, `git_`, `vim_`).

### 8. Variable-driven instructions file list in opencode.json

**Decision**: Make the OpenCode `instructions` array in `opencode.json.j2` driven by a variable `ai_opencode_instructions` (a list), defaulting to `[".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]`. The template renders this list into the JSON array.

**Rationale**: SpecKit hardcodes `.specify/memory/constitution.md` as the canonical location for the project constitution across all its commands (`speckit.constitution`, `speckit.analyze`, `speckit.plan`) and its init function. OpenSpec has no built-in constitution concept -- it uses a freeform `context` string in `openspec/config.yaml`. Rather than inventing a parallel convention (e.g., `constitution.md` at repo root), the role aligns to the SpecKit standard so all three tools converge on the same file. OpenCode resolves relative paths from the repo root, so `.specify/memory/constitution.md` works directly. OpenCode gracefully ignores instruction files that don't exist, so repos without SpecKit initialized simply skip it. `AGENTS.md` and `CLAUDE.md` are auto-loaded by OpenCode from the repo root without needing to be in `instructions`, but listing them explicitly is self-documenting. Ordering matters: last file wins for conflicting instructions, so `CLAUDE.md` (local overrides) is last. Making the list a variable allows consumers to customize.

**Alternatives considered**: (a) Using `constitution.md` at repo root as proposed by org-infra spec 004. Rejected because SpecKit ignores the root file entirely -- it only reads `.specify/memory/constitution.md`, and maintaining two copies that drift is worse than standardizing on one. (b) Hardcoding the list in the template. Rejected because different teams may have different instruction file conventions.

### 9. Trusted GitHub organizations for command security guards

**Decision**: Add an `ai_trusted_github_orgs` list variable (defaulting to an empty list) that is exported via the wrapper script as `TRUSTED_GITHUB_ORGS` (comma-separated). The `checkout_pr` and `review_pr` command files include a pre-flight verification step: before performing any operations, check the current repository's owner against the trusted orgs list. If the repo belongs to a trusted org, proceed silently. If not, warn the user and ask for explicit confirmation before continuing.

**Rationale**: The `checkout_pr` and `review_pr` commands use `gh` CLI to interact with remote repositories. Without verification, a user could unknowingly fetch and checkout code from an untrusted organization. The wrapper script approach (env var) keeps commands as static files while making the org list configurable via Ansible variables. The guard is advisory (AI-interpreted instruction, not a programmatic gate), which is appropriate for a command executed within an AI agent context.

**Alternatives considered**: (a) Converting commands to Jinja2 templates. Rejected because it would break the "static files" deployment model and add template complexity for a single variable reference. (b) Restricting git permissions in opencode.json (e.g., `"git fetch*": "ask"`). Rejected because it would prompt on every fetch regardless of context, degrading the experience for trusted repos. (c) Hardcoding the org name in command files. Rejected because it makes the role unusable by other organizations.

### 10. Proper README documentation following sibling role pattern

**Decision**: Replace the boilerplate `README.md` with proper documentation following the pattern established by `ansible-role-git`: role description with bullet list of capabilities, requirements section listing prerequisites, role variables section referencing `defaults/main.yml`, example playbooks showing common usage patterns (minimal, with dependencies enabled, with pinned versions, with selective tasks), license, and author information.

**Rationale**: The default `ansible-galaxy init` README provides no useful information about the role. Users consuming the role need to understand what it does, what variables they can override, and how to use it in a playbook. The git role README provides a proven template that is concise yet informative.

**Alternatives considered**: None -- proper documentation is a baseline requirement.

### 11. Use safe placeholder defaults for GCP variables

**Decision**: Replace `ai_gcp_project` and `ai_vertex_location` defaults with safe placeholder values (`your-gcp-project` and `us-central1` respectively). These are clearly placeholder values. The README documents that these must be set when using Google Vertex AI as the provider. When not using Vertex, the values are exported as env vars by the wrapper script but harmlessly ignored by OpenCode.

**Rationale**: The role will be published on Ansible Galaxy. Real GCP project names and internal region choices expose organizational infrastructure details to the public. Placeholder values make it obvious the role needs configuration while being safe to commit.

**Alternatives considered**: Leaving defaults empty or undefined. Rejected because the wrapper script template would export empty strings, and the opencode.json template would fail to render cleanly. Placeholder strings are semantically clear and syntactically valid.

### 12. Runnable smoke test with install tasks disabled

**Decision**: Update `tests/test.yml` to disable all install tasks (`install_dependencies`, `install_opencode`, `install_openspec`, `install_speckit`) and only enable `configure_opencode`. This exercises the dispatcher pattern and configuration deployment without requiring npm, uv, or GitHub API access.

**Rationale**: The default `tests/test.yml` from `ansible-galaxy init` runs the entire role, which would fail without npm/uv installed. Disabling install tasks makes the smoke test actually runnable in a minimal environment while still verifying the core role structure. This matches the sibling role pattern (minimal `tests/test.yml`) while being more practically useful.

**Alternatives considered**: (a) Adding Molecule with container-based testing. Rejected for this change because no sibling role uses Molecule -- it would be a pattern divergence best addressed as a separate effort. (b) Keeping the default test.yml as-is. Rejected because it would fail on any machine without npm/uv, making it useless as a smoke test.

### 13. Add yamllint configuration

**Decision**: Add a `.yamllint` configuration file for YAML linting consistency. No sibling role currently has this, but it is a lightweight quality gate that catches common YAML issues before runtime.

**Rationale**: YAML syntax errors in Ansible roles are a frequent source of runtime failures. A `.yamllint` config is zero-cost to maintain and can be run locally or in CI. It sets a quality baseline for the role without requiring heavy infrastructure.

**Alternatives considered**: Adding both `.yamllint` and `.ansible-lint`. Decided to include only yamllint for now as it's the lighter-weight option. Ansible-lint can be added later as a follow-up.

### 14. Fix SPDX license headers to Apache-2.0

**Decision**: Replace `MIT-0` SPDX headers in scaffolded files (`vars/main.yml`, `handlers/main.yml`, `tests/inventory`) with `Apache-2.0` to match the role's actual license declared in `meta/main.yml` and `README.md`.

**Rationale**: The `ansible-galaxy init` scaffolding generated these files with `MIT-0` headers. The role uses Apache-2.0. Inconsistent license identifiers create legal ambiguity and would be flagged during Galaxy publishing or compliance audits.

### 15. Ensure agent-neutral skills directory alongside OpenCode-specific one

**Decision**: In addition to ensuring `~/.config/opencode/skills/` exists, also ensure `~/.agents/skills/` exists. The README should guide users to create custom skills in `~/.agents/skills/` for cross-agent portability. The `~/.config/opencode/skills/` directory remains for OpenCode-specific skills. Commands stay in `~/.config/opencode/command/` as there is no agent-neutral command discovery mechanism.

**Rationale**: OpenCode natively discovers skills from `.agents/skills/` and `.claude/skills/` (via its `EXTERNAL_DIRS` constant), in addition to its own `.opencode/skills/`. The org-infra spec 004 recommends `.agents/skills/` as the agent-neutral location. By ensuring this directory exists and guiding users toward it, the role supports cross-agent portability for user-created skills. If a user later switches from OpenCode to Claude Code or another agent, their skills in `~/.agents/skills/` continue to work. Commands have no equivalent agent-neutral path -- OpenCode only scans `.opencode/command/` -- so they remain OpenCode-specific.

**Alternatives considered**: (a) Only ensuring `~/.config/opencode/skills/`. Rejected because it misses the cross-agent opportunity at zero cost. (b) Deploying managed skills to `~/.agents/skills/` instead of `~/.config/opencode/skills/`. Rejected because no managed skills are shipped yet -- when they are, the placement decision can be revisited per-skill.

### 16. Deploy commit.md as a global baseline with repo-level override semantics

**Decision**: Deploy a `commit.md` file to `~/.config/opencode/` containing universal commit standards (Conventional Commits format, Signed-off-by trailer, Assisted-by trailer for AI-assisted commits). Reference it in `ai_opencode_instructions` via `~/.config/opencode/commit.md` so OpenCode always loads it regardless of which repository the user is in. The file explicitly states that it provides baseline defaults, and that any conflicting rules found in repository-level files (constitution.md, AGENTS.md, CONTRIBUTING.md, or any other file used by AI tools in the repository) take precedence.

**Rationale**: The commit trailer standards (from the org constitution) must apply universally -- including in repos that haven't been synced with org-infra or that lack a constitution.md. The `~/` path prefix in OpenCode's `instructions` array resolves from the home directory, making it load regardless of the working repo. Placing the file first in the instructions list establishes it as the lowest-precedence baseline: OpenCode processes instructions in order with last-wins semantics, so repo-level files loaded afterward naturally override conflicting rules. The explicit "defer to repo" language in the file adds a belt-and-suspenders safeguard for cases where ordering alone might be ambiguous.

**Alternatives considered**: (a) Embedding commit rules in a global AGENTS.md at `~/.config/opencode/AGENTS.md`. Rejected because AGENTS.md would become a mixed-purpose file and could grow into a maintenance burden. (b) Using a skill for commit guidance. Rejected because skills are on-demand (user must invoke them), not always-on. (c) Relying solely on the constitution.md in each repo. Rejected because the requirement is to enforce these rules even when no constitution exists.

## Risks / Trade-offs

- **[npm/uv availability]** The role assumes `npm` and `uv` are installed on the target by default. If they are missing, installation tasks will fail. → Mitigation: Users can enable the `install_dependencies` sub-task to have the role install system packages (nodejs, npm, uv) automatically. Document this in the role README.

- **[GitHub API rate limiting]** The SpecKit `latest` resolution queries the GitHub API without authentication, which has a 60 requests/hour limit per IP. → Mitigation: Users can pin a specific version to avoid API calls. The rate limit is unlikely to be hit in normal usage (one call per role run).

- **[Config file drift]** If a user manually edits `~/.config/opencode/opencode.json` after the role runs, the next role run will overwrite their changes. → Mitigation: This is standard Ansible behavior (desired state enforcement). Users who want manual control can disable `configure_opencode` in `ai_tasks`.

- **[Single OS family support]** Only `redhat.yml` variables are provided. Running on Debian/Ubuntu will fail at the OS vars inclusion step. → Mitigation: The dispatcher pattern includes `ansible_facts['os_family']|lower` dynamically, so adding `debian.yml` later is straightforward. Document the supported platforms in meta.yml and README.
