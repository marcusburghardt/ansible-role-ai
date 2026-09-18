ansible-role-ai
===============

This Ansible Role will ensure AI developer tools are installed, updated, and configured
according to user preferences. Settings can be customized through variables. Take a look
in the existing defaults defined in `defaults/main.yml` and override them in a Playbook.

This role will:
- Install and manage Ollama for running open models locally (enabled by default);
- Pull a curated selection of open models via Ollama (default: `qwen3:8b`);
- Ensure OpenCode (opencode-ai) is installed and updated via npm;
- Ensure OpenSPEC (@fission-ai/openspec) is installed and updated via npm;
- Ensure SpecKit (specify-cli) is installed and updated via uv;
- Deploy the OpenCode configuration file (`opencode.json`) with customizable model, provider, and permission settings;
- Deploy an AI agent wrapper script for launching OpenCode with proper environment variables;
- Auto-discover and deploy built-in OpenCode commands, with support for disabling specific commands and adding custom ones from external paths;
- Auto-discover and deploy built-in OpenCode skills, with support for disabling specific skills and adding custom ones from external paths;
- Optionally clean up specific commands and skills from the target host;
- Optionally install system-level dependencies (nodejs, npm, uv) when enabled;
- Optionally install and update Cursor IDE via RPM, DEB, or AppImage with automatic format detection;
- Optionally deploy a Grafana metrics dashboard with a helper script for visualizing opencode-metrics data via an ephemeral podman container;

Requirements
------------

- `community.general` Ansible collection (for `community.general.npm` module)
- `npm` / `nodejs` on the target host (or enable `install_dependencies` task)
- `uv` on the target host (or enable `install_dependencies` task)
- `curl` on the target host (for Ollama install script, when `install_ollama` is enabled)

Role Variables
--------------

You can customize your environment in a very simple and centralized way editing some variables in:
- `defaults/main.yml`

In some rare cases, you may change some configuration to reflect your local environment in:
- `vars/*.yml`

Observe that the above variables could be set in your Playbook too, which is much more elegant.
Take a look in the Example Playbook section.

### Key Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ai_tasks` | See defaults | List of sub-tasks with `enabled` flags |
| `ai_ollama_install_method` | `auto` | Install method: `auto`, `package`, or `script` |
| `ai_ollama_selinux_policy` | `false` | Deploy confined SELinux policy for Ollama (see below) |
| `ai_ollama_service_enabled` | `false` | Enable Ollama service to persist across reboots |
| `ai_ollama_service_state` | `started` | Ollama service runtime state (`started` or `stopped`) |
| `ai_ollama_models` | See defaults | Curated list of models to pull (with `enabled` flags) |
| `ai_opencode_version` | `latest` | OpenCode version (`latest` or pinned, e.g., `1.2.3`) |
| `ai_openspec_version` | `latest` | OpenSPEC version (`latest` or pinned) |
| `ai_speckit_version` | `latest` | SpecKit version (`latest` or pinned tag, e.g., `v0.4.4`) |
| `ai_model` | `ollama/qwen3:8b` | Primary AI model |
| `ai_small_model` | `ollama/qwen3:8b` | Small/fast AI model (background tasks) |
| `ai_opencode_agent_build_model` | `{{ ai_model }}` | Model for build agent |
| `ai_opencode_agent_plan_model` | `{{ ai_small_model }}` | Model for plan agent |
| `ai_opencode_agent_explore_model` | `{{ ai_small_model }}` | Model for explore agent |
| `ai_opencode_agent_general_model` | `{{ ai_small_model }}` | Model for general agent |
| `ai_opencode_agents` | See defaults | Full agent routing dict (rendered into `opencode.json`) |
| `ai_opencode_metrics_version` | `0.2.0` | Pinned version of the `@mburghardt/opencode-metrics` plugin (set to `"local"` for local dev) |
| `ai_opencode_metrics_local_path` | `""` | Path to local opencode-metrics repo (only used when version is `"local"`) |
| `ai_opencode_metrics_config` | `{}` | Optional metrics plugin config dict (deployed as `config.yaml` when non-empty) |
| `ai_opencode_metrics_data_dir` | `~/.local/share/opencode-metrics` | Metrics plugin data directory (bind-mounted into Grafana container) |
| `ai_opencode_plugins` | `["@mburghardt/opencode-metrics@..."]` | List of npm plugin packages for OpenCode (metrics plugin included by default) |
| `ai_opencode_compaction` | See defaults | Compaction settings dict (`auto`, `prune`, `reserved`) |
| `ai_opencode_providers` | See defaults | Provider catalog for OpenCode (rendered into `opencode.json`) |
| `ai_opencode_ollama_models` | See defaults | Ollama models visible in OpenCode (subset of pulled models) |
| `ai_opencode_disabled_providers` | `[]` | Providers that OpenCode should not auto-detect |
| `ai_gcp_project` | `your-gcp-project` | GCP project for Vertex AI (see note below) |
| `ai_vertex_location` | `us-central1` | GCP Vertex AI region (see note below) |
| `ai_agent_script_name` | `skynet` | Name of the wrapper script in `~/bin/` |
| `ai_opencode_instructions` | `[".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]` | Instruction files for OpenCode |
| `ai_trusted_github_orgs` | `[]` | Trusted GitHub organizations for command security |
| `ai_opencode_commands_disabled` | `[]` | Built-in command names to skip (without `.md`) |
| `ai_opencode_commands_custom` | `[]` | Custom commands to deploy (list of `src`/`name` dicts) |
| `ai_opencode_skills_disabled` | `[]` | Built-in skill names to skip (directory name) |
| `ai_opencode_skills_custom` | `[]` | Custom skills to deploy (list of `src`/`name` dicts) |
| `ai_skills_target` | `agent-neutral` | Skills deploy target: `agent-neutral` or `opencode` |
| `ai_opencode_commands_cleanup` | `[]` | Command filenames to remove (used by `cleanup_opencode`) |
| `ai_opencode_skills_cleanup` | `[]` | Skill directory names to remove (used by `cleanup_opencode`) |
| `ai_cursor_version` | `latest` | Cursor version (`latest` or pinned major.minor, e.g., `3.0`) |
| `ai_cursor_install_method` | `auto` | Install format: `auto`, `rpm`, `deb`, or `appimage` |
| `ai_cursor_appimage_dir` | `~/.local/bin` | Directory for AppImage binary (AppImage method only) |
| `ai_grafana_metrics_port` | `3033` | Host port for the Grafana container |
| `ai_grafana_metrics_container_name` | `opencode-grafana` | Podman container name |
| `ai_grafana_metrics_script_name` | `opencode-grafana` | Helper script name in `~/bin/` |
| `ai_grafana_metrics_provisioning_dir` | `~/.config/opencode/grafana` | Grafana provisioning and dashboard files directory |
| `ai_grafana_metrics_monthly_budget` | `300` | Monthly cost budget (USD). Drives color thresholds on all cost KPI panels |

### Ollama (Local Models)

Ollama is **enabled by default**, giving every user a working OpenCode setup at zero cost.
The role installs Ollama, manages the systemd service, and pulls models from a curated list.

**Install method:**

By default (`ai_ollama_install_method: auto`), the role detects the OS family and uses the
native package manager when available:

| Method | When used | How it installs |
|--------|-----------|-----------------|
| `package` | RedHat/Fedora, Debian/Ubuntu (auto-detected) | `dnf install ollama` / `apt install ollama` |
| `script` | Other distros (fallback) | Official install script from `ollama.com` |

You can force a specific method by overriding the variable:

```yaml
ai_ollama_install_method: script    # force install script on any distro
```

**SELinux policy (disabled by default):**

On SELinux-enforcing systems (e.g., Fedora), the Ollama package does not ship its own
SELinux policy. Without one, Ollama runs as `init_t` (the generic systemd service context)
and is denied network access -- it cannot bind to port 11434 or pull models from the
registry.

Setting `ai_ollama_selinux_policy: true` deploys a confined policy that creates a dedicated
`ollama_t` domain with only the permissions Ollama needs:

| Permission | Purpose |
|------------|---------|
| Bind to port 11434 | Serve the local API |
| Listen/accept TCP connections | Handle API requests |
| Connect to HTTPS ports | Pull models from `registry.ollama.ai` |
| Read `/proc/sys/net`, `/proc/meminfo` | Network config and memory detection |
| Read/write `/usr/share/ollama` | Model storage |
| DNS resolution | Resolve registry hostname |
| Read `/etc/*`, NSS, locale | Standard daemon operation |

The full policy with detailed rationale for each rule is in `files/selinux/ollama.te`.

```yaml
ai_ollama_selinux_policy: true    # enable on SELinux-enforcing hosts
```

> **Note:** This installs `selinux-policy-devel` and `policycoreutils-python-utils` as
> build dependencies on the target host.

**Service lifecycle:**

| `ai_ollama_service_enabled` | `ai_ollama_service_state` | Behavior |
|-----------------------------|---------------------------|----------|
| `false` (default) | `started` (default) | Runs now, gone after reboot |
| `true` | `started` | Runs now, auto-starts on boot |
| `false` | `stopped` | Installed but not running |
| `true` | `stopped` | Will start on next boot, not now |

**Model selection:**

The default curated list enables only `qwen3:8b` (~5 GB, runs on virtually any modern
hardware). Enable additional models in your playbook:

```yaml
ai_ollama_models:
  - { enabled: true, name: 'qwen3:8b' }
  - { enabled: true, name: 'qwen3:32b' }      # strong all-round (~20 GB VRAM)
  - { enabled: false, name: 'devstral' }        # Mistral code model (~15 GB VRAM)
  - { enabled: false, name: 'qwen3-coder:a3b' } # MoE code specialist (~20 GB VRAM)
  - { enabled: false, name: 'llama3.1:8b' }     # Meta general model (~5 GB VRAM)
```

Models are only pulled when the Ollama service is running. If you set
`ai_ollama_service_state: stopped`, model pulls are gracefully skipped.

**OpenCode-visible models:**

By default, all enabled models appear in OpenCode. To control which pulled models are
visible in the OpenCode `/models` picker, override `ai_opencode_ollama_models`:

```yaml
ai_opencode_ollama_models:
  qwen3:8b:
    name: "Qwen 3 8B (local)"
  qwen3:32b:
    name: "Qwen 3 32B (local)"
```

### Provider Configuration

The OpenCode provider catalog is fully data-driven via the `ai_opencode_providers`
variable. By default, both Ollama and Google Vertex Anthropic are configured. Override
this variable to add, remove, or customize providers:

```yaml
# Ollama-only setup (remove Vertex entirely)
ai_opencode_providers:
  ollama:
    npm: "@ai-sdk/openai-compatible"
    name: "Ollama (local)"
    options:
      baseURL: "http://localhost:11434/v1"
    models: "{{ ai_opencode_ollama_models }}"
```

To prevent OpenCode from auto-detecting unconfigured providers:

```yaml
ai_opencode_disabled_providers:
  - openai
  - gemini
```

### Google Vertex AI Configuration

If you are using Google Vertex AI as the model provider, you **must** set the following
variables to your real values in your playbook:

```yaml
ai_gcp_project: "my-actual-gcp-project"
ai_vertex_location: "us-east5"
ai_model: "google-vertex-anthropic/claude-opus-4-6@default"
ai_small_model: "anthropic/claude-sonnet-4-5"
```

If you are **not** using Vertex AI, these variables are harmlessly ignored. The wrapper
script only exports GCP environment variables when `google-vertex-anthropic` is present
in `ai_opencode_providers`.

### Cost Optimization (Paid Providers)

When using paid API providers, OpenCode sessions can burn tokens on tasks that don't
require the most capable model. The role supports three complementary strategies to
reduce cost, informed by the
[OpenCode Token Efficiency Configuration Guide](https://gist.github.com/jflowers/c54514358abf892df84d5e6b8e7d7772)
by [jflowers](https://github.com/jflowers).

**Agent model routing:**

The role assigns each OpenCode agent its own model variable. By default, `build` uses
`ai_model` and all other agents (`plan`, `explore`, `general`) use `ai_small_model`.
For Ollama users this is a no-op (same model everywhere). For paid providers, setting
different primary and small models activates routing automatically:

```yaml
ai_model: "google-vertex-anthropic/claude-opus-4-6@default"
ai_small_model: "google-vertex-anthropic/claude-haiku-4-5@20251001"
```

For three-tier routing (Opus / Sonnet / Haiku), override individual agent variables:

```yaml
ai_model: "google-vertex-anthropic/claude-opus-4-6@default"
ai_small_model: "google-vertex-anthropic/claude-haiku-4-5@20251001"
ai_opencode_agent_plan_model: "google-vertex-anthropic/claude-sonnet-4-6@default"
ai_opencode_agent_general_model: "google-vertex-anthropic/claude-sonnet-4-6@default"
```

This routes build to Opus, plan/general to Sonnet, and explore to Haiku.

**Plugins (metrics included by default):**

The [`@mburghardt/opencode-metrics`](https://github.com/marcusburghardt/opencode-metrics)
plugin is included by default, giving every user automatic metrics collection out of the
box. The version is pinned via `ai_opencode_metrics_version` (default: `0.2.0`).

To add more plugins alongside the default:

```yaml
ai_opencode_plugins:
  - "@mburghardt/opencode-metrics@{{ ai_opencode_metrics_version }}"
  - "@angdrew/opencode-hashline-plugin"   # content-addressable edits
  - "@tarquinen/opencode-dcp"             # dynamic context pruning
```

To remove the metrics plugin and start with an empty list:

```yaml
ai_opencode_plugins: []
```

OpenCode installs npm plugins automatically at startup. Plugin-specific configuration
files (e.g., `dcp.jsonc`) are managed by the user outside this role.

**Local development of opencode-metrics:**

When developing the `opencode-metrics` plugin locally, you can bypass npm and load the
plugin directly from a local repository checkout. This avoids publishing a new release
for every change during development.

Workflow:

1. Make code changes in your local `opencode-metrics` repository
2. Build the plugin: `make build` (produces `dist/index.js`)
3. Set the role variables in your playbook:
   ```yaml
   ai_opencode_metrics_version: "local"
   ai_opencode_metrics_local_path: "~/GIT/me/opencode-metrics"
   ```
4. Run the playbook to deploy the loader file
5. Restart OpenCode to pick up the changes

The role writes a TypeScript loader file at `~/.config/opencode/plugins/opencode-metrics.ts`
that imports the plugin from the local path, and removes the npm entry from `opencode.json`.
A leading `~` in the path is expanded to the target user's home directory.

**Switching back to npm mode:**

To switch back from local to npm-managed installation:

1. Set `ai_opencode_metrics_version` back to a semver string (e.g., `"0.2.0"`) or `"latest"`
2. Remove or leave `ai_opencode_metrics_local_path` as-is (it is ignored in npm mode)
3. Run the playbook -- the loader file is removed automatically and the npm entry is
   restored in `opencode.json`

**Metrics plugin configuration (optional):**

By default, the metrics plugin creates its own `config.yaml` with sensible defaults at
first run. To customize classification or budget rules, set `ai_opencode_metrics_config`
in your playbook:

```yaml
ai_opencode_metrics_config:
  version: 1
  classification_rules:
    - name: debugging
      conditions:
        - field: session_title
          operator: contains
          value: debug
  budget_rules:
    - period: monthly
      limit_usd: 300
```

When non-empty, the role deploys the config to `{{ ai_opencode_metrics_data_dir }}/config.yaml`.

**Compaction tuning:**

The role deploys compaction settings via the `ai_opencode_compaction` variable. The
defaults enable automatic compaction with output pruning:

```yaml
ai_opencode_compaction:
  auto: true
  prune: true
  reserved: 10000    # tokens reserved for the model's response
```

Override to tune for your context window size or disable compaction entirely.

### Migration from Previous Versions

Previous versions of this role defaulted to `google-vertex-anthropic` as the primary
provider with hardcoded provider configuration. If you are upgrading, note:

- **`ai_model`** now defaults to `ollama/qwen3:8b` instead of
  `google-vertex-anthropic/claude-opus-4-6@default`
- **`ai_small_model`** now defaults to `ollama/qwen3:8b` instead of
  `anthropic/claude-sonnet-4-5`
- **Provider block** in `opencode.json` is now driven by `ai_opencode_providers`
  instead of being hardcoded
- **`disabled_providers`** is now driven by `ai_opencode_disabled_providers` (defaults
  to empty instead of `["openai", "gemini"]`)

To restore the previous Vertex-only behavior:

```yaml
ai_model: "google-vertex-anthropic/claude-opus-4-6@default"
ai_small_model: "anthropic/claude-sonnet-4-5"
ai_opencode_disabled_providers: ["openai", "gemini"]
ai_tasks:
  - { enabled: false, name: 'install_dependencies' }
  - { enabled: false, name: 'install_ollama' }
  - { enabled: false, name: 'configure_ollama' }
  - { enabled: true,  name: 'install_opencode' }
  - { enabled: true,  name: 'configure_opencode' }
  - { enabled: false, name: 'cleanup_opencode' }
  - { enabled: true,  name: 'install_openspec' }
  - { enabled: true,  name: 'install_speckit' }
  - { enabled: false, name: 'install_cursor' }
```

### Trusted GitHub Organizations

The `checkout_pr` and `review_pr` commands include a security guard that verifies the current
repository belongs to a trusted GitHub organization before interacting with remote PRs. Set
`ai_trusted_github_orgs` to your organization's GitHub login(s):

```yaml
ai_trusted_github_orgs:
  - "my-org"
  - "partner-org"
```

When the list is empty (default), the commands will always prompt for confirmation before
proceeding.

### Commands

Built-in commands (`.md` files in `files/commands/`) are **auto-discovered** and deployed
to `~/.config/opencode/command/`. Adding or removing a command file from the role
requires no changes to task YAML -- it is picked up automatically.

**Disable specific built-in commands** by adding their name (without `.md`) to the blocklist:

```yaml
ai_opencode_commands_disabled:
  - checkout_pr       # skip deploying checkout_pr.md
```

**Deploy custom commands** from local paths (relative to the playbook or absolute):

```yaml
ai_opencode_commands_custom:
  - src: ../shared-commands/deploy_staging.md
  - src: /opt/team/audit.md
    name: security_audit.md    # optional: override deployed filename
```

The role will not touch command files it does not manage. If a custom command has the
same filename as a built-in, the custom version wins (custom deployment runs after
built-in deployment).

### Skills

Built-in skills (subdirectories in `files/skills/`) are auto-discovered and deployed
in the same way as commands. The role ships with no built-in skills initially, but the
infrastructure is ready.

By default, skills are deployed to the **agent-neutral** directory `~/.agents/skills/`.
OpenCode natively discovers skills from this path, and it is also compatible with
Claude Code and other agents that follow the `.agents/` convention. To deploy to
the OpenCode-specific directory instead, set:

```yaml
ai_skills_target: opencode    # deploys to ~/.config/opencode/skills/
```

Both directories are always created by the role regardless of the `ai_skills_target` setting.

**Disable specific built-in skills** or **deploy custom skills** the same way as commands:

```yaml
ai_opencode_skills_disabled:
  - some-built-in-skill

ai_opencode_skills_custom:
  - src: ../shared-skills/deploy-workflow
  - src: /opt/team/review-skill
    name: team-review          # optional: override deployed directory name
```

### Cursor IDE

The `install_cursor` task installs and updates Cursor IDE. It is **disabled by default**
and must be explicitly enabled in `ai_tasks`. The task supports three installation formats:

| Method | When used | Requires root? |
|--------|-----------|----------------|
| `rpm` | RedHat/Fedora (auto-detected) | Yes |
| `deb` | Debian/Ubuntu (auto-detected) | Yes |
| `appimage` | Any Linux distro / fallback | No |

By default, `ai_cursor_install_method` is `auto`, which selects the format based on the
target host's OS family. You can override this to force a specific format.

The task is **idempotent**: it queries the Cursor download API to resolve the target version,
compares it against the currently installed version, and skips download/installation when
versions match. This avoids downloading ~150MB on every run.

For AppImage installations, the task also deploys a `.desktop` file to
`~/.local/share/applications/` so Cursor appears in desktop application launchers.

> **Note on Cursor's built-in updater:** Cursor includes an internal auto-updater that may
> still display update prompts even when the version is managed by Ansible. This is expected
> behavior -- the system-installed version is the authoritative one, and the internal updater
> cannot override it for RPM/DEB installations. You can safely dismiss these prompts.

### Metrics Visualization

The `configure_grafana_metrics` task deploys a helper script and Grafana provisioning files
for visualizing data from the [opencode-metrics](https://github.com/marcusburghardt/opencode-metrics)
plugin. It is **disabled by default** and must be explicitly enabled in `ai_tasks`.

**Prerequisites:**

- `podman` installed on the target host (the task does not install podman)
- The opencode-metrics plugin collecting data to `~/.local/share/opencode-metrics/metrics.db`

**Enable the task:**

```yaml
ai_tasks:
  # ... other tasks ...
  - { enabled: true, name: 'configure_grafana_metrics' }
```

After running the playbook, use the helper script to manage the Grafana container:

```bash
opencode-grafana start    # Start Grafana at http://localhost:3033
opencode-grafana stop     # Stop and remove the container (data preserved)
opencode-grafana status   # Check if the container is running
opencode-grafana logs     # Follow container logs
```

The container runs an ephemeral Grafana instance pre-configured with:

- The [frser-sqlite-datasource](https://github.com/fr-ser/grafana-sqlite-datasource) plugin
- A pre-built dashboard with 9 panels (cost, tokens, cache, classification, duration, projects)
- Anonymous admin access (no login required -- local-only, single-user tool)
- A named podman volume for persisting preferences and dashboard modifications across restarts

Port 3033 is used by default to avoid conflicts with other services on port 3000. Override
with `ai_grafana_metrics_port`.

### Cleanup

To remove specific commands or skills from the target host, enable the `cleanup_opencode`
task and provide names to remove:

```yaml
ai_tasks:
  # ... other tasks ...
  - { enabled: true, name: 'cleanup_opencode' }

ai_opencode_commands_cleanup:
  - old_command.md

ai_opencode_skills_cleanup:
  - deprecated-skill
```

The cleanup task is disabled by default and runs after `configure_opencode` in the
task order. It uses `state: absent`, so missing files are silently skipped.

### Commit Standards

The role deploys a `commit.md` instruction file to `~/.config/opencode/` that establishes
baseline commit standards for all repositories:

- **Conventional Commits** message format
- **Signed-off-by** trailer on all commits (via `git commit -s`)
- **Assisted-by** trailer on AI-assisted commits (identifying tool and model)

This file is loaded first in the OpenCode instructions chain, making it the lowest-precedence
baseline. If a repository provides its own commit rules (via `constitution.md`, `AGENTS.md`,
`CONTRIBUTING.md`, or similar), those repository-level rules automatically take precedence.

Dependencies
------------

None.

Example Playbook
----------------

**Minimal (all defaults):**

```yaml
---
- hosts: my_linux
  roles:
    - ansible-role-ai
```

**With system dependencies enabled (fresh machine):**

```yaml
---
- hosts: my_linux
  vars:
    ai_tasks:
      - { enabled: true,  name: 'install_dependencies' }
      - { enabled: true,  name: 'install_ollama' }
      - { enabled: true,  name: 'configure_ollama' }
      - { enabled: true,  name: 'install_opencode' }
      - { enabled: true,  name: 'configure_opencode' }
      - { enabled: false, name: 'cleanup_opencode' }
      - { enabled: true,  name: 'install_openspec' }
      - { enabled: true,  name: 'install_speckit' }
      - { enabled: false, name: 'install_cursor' }
  roles:
    - ansible-role-ai
```

**With Vertex AI as primary provider (paid setup):**

```yaml
---
- hosts: my_linux
  vars:
    ai_model: "google-vertex-anthropic/claude-opus-4-6@default"
    ai_small_model: "anthropic/claude-sonnet-4-5"
    ai_gcp_project: "my-gcp-project"
    ai_vertex_location: "us-east5"
  roles:
    - ansible-role-ai
```

**With larger Ollama models for beefy GPU:**

```yaml
---
- hosts: my_linux
  vars:
    ai_ollama_models:
      - { enabled: true, name: 'qwen3:8b' }
      - { enabled: true, name: 'qwen3:32b' }
    ai_opencode_ollama_models:
      qwen3:8b:
        name: "Qwen 3 8B (local)"
      qwen3:32b:
        name: "Qwen 3 32B (local)"
    ai_model: "ollama/qwen3:32b"
    ai_small_model: "ollama/qwen3:8b"
    ai_ollama_service_enabled: true
  roles:
    - ansible-role-ai
```

**With pinned versions:**

```yaml
---
- hosts: my_linux
  vars:
    ai_opencode_version: "1.2.3"
    ai_openspec_version: "1.0.0"
    ai_speckit_version: "v0.4.4"
  roles:
    - ansible-role-ai
```

**With selective tasks (OpenCode only, no SpecKit, no Ollama):**

```yaml
---
- hosts: my_linux
  vars:
    ai_tasks:
      - { enabled: false, name: 'install_dependencies' }
      - { enabled: false, name: 'install_ollama' }
      - { enabled: false, name: 'configure_ollama' }
      - { enabled: true,  name: 'install_opencode' }
      - { enabled: true,  name: 'configure_opencode' }
      - { enabled: false, name: 'cleanup_opencode' }
      - { enabled: true,  name: 'install_openspec' }
      - { enabled: false, name: 'install_speckit' }
      - { enabled: false, name: 'install_cursor' }
  roles:
    - ansible-role-ai
```

**With Cursor IDE enabled (auto-detects RPM/DEB/AppImage):**

```yaml
---
- hosts: my_linux
  vars:
    ai_tasks:
      - { enabled: false, name: 'install_dependencies' }
      - { enabled: true,  name: 'install_ollama' }
      - { enabled: true,  name: 'configure_ollama' }
      - { enabled: true,  name: 'install_opencode' }
      - { enabled: true,  name: 'configure_opencode' }
      - { enabled: false, name: 'cleanup_opencode' }
      - { enabled: true,  name: 'install_openspec' }
      - { enabled: true,  name: 'install_speckit' }
      - { enabled: true,  name: 'install_cursor' }
  roles:
    - ansible-role-ai
```

**With Cursor IDE pinned to a specific version:**

```yaml
---
- hosts: my_linux
  vars:
    ai_cursor_version: "3.0"
    ai_cursor_install_method: appimage    # force AppImage regardless of OS
    ai_tasks:
      - { enabled: false, name: 'install_dependencies' }
      - { enabled: true,  name: 'install_ollama' }
      - { enabled: true,  name: 'configure_ollama' }
      - { enabled: true,  name: 'install_opencode' }
      - { enabled: true,  name: 'configure_opencode' }
      - { enabled: false, name: 'cleanup_opencode' }
      - { enabled: true,  name: 'install_openspec' }
      - { enabled: true,  name: 'install_speckit' }
      - { enabled: true,  name: 'install_cursor' }
  roles:
    - ansible-role-ai
```

**With custom commands and disabled built-ins:**

```yaml
---
- hosts: my_linux
  vars:
    ai_opencode_commands_disabled:
      - checkout_pr
    ai_opencode_commands_custom:
      - src: shared-commands/deploy_staging.md
      - src: shared-commands/run_migrations.md
        name: migrate.md
    ai_opencode_skills_custom:
      - src: shared-skills/deploy-workflow
  roles:
    - ansible-role-ai
```

Release Process
---------------

This role uses [release-please](https://github.com/googleapis/release-please) for
automated versioning based on
[Conventional Commits](https://www.conventionalcommits.org/).

**How it works:**

1. Push commits to `main` using conventional prefixes (`feat:`, `fix:`, `chore:`, etc.)
2. Release-please opens a PR with a version bump and changelog update
3. Review and merge the PR to create a git tag and GitHub Release
4. Ansible Galaxy imports the role automatically on each release

**Version bumps:**

| Commit prefix | Example | Version bump |
|---------------|---------|--------------|
| `fix:` | `fix: correct model pull check` | Patch (`0.1.0` → `0.1.1`) |
| `feat:` | `feat: add new provider` | Patch (`0.1.x` → `0.1.x+1`) |
| `BREAKING CHANGE` | footer in commit body | Minor (`0.1.x` → `0.2.0`) |

> **Note:** While the version is below `1.0.0`, breaking changes bump minor and features
> bump patch. After `1.0.0`, standard semver applies (breaking = major, feat = minor,
> fix = patch).

**Installing a specific version:**

```bash
ansible-galaxy role install marcusburghardt.ai,v0.1.0
```

License
-------

Apache-2.0

Author Information
------------------

Marcus Burghardt
- [https://github.com/marcusburghardt](https://github.com/marcusburghardt)
- [https://www.linkedin.com/in/marcusburghardt](https://www.linkedin.com/in/marcusburghardt)
