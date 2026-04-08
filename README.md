ansible-role-ai
===============

This Ansible Role will ensure AI developer tools are installed, updated, and configured
according to user preferences. Settings can be customized through variables. Take a look
in the existing defaults defined in `defaults/main.yml` and override them in a Playbook.

This role will:
- Ensure OpenCode (opencode-ai) is installed and updated via npm;
- Ensure OpenSPEC (@fission-ai/openspec) is installed and updated via npm;
- Ensure SpecKit (specify-cli) is installed and updated via uv;
- Deploy the OpenCode configuration file (`opencode.json`) with customizable model, provider, and permission settings;
- Deploy an AI agent wrapper script for launching OpenCode with proper environment variables;
- Deploy managed OpenCode commands (`checkout_pr`, `review_pr`, `refresh`) to the user config directory;
- Ensure the user's OpenCode skills directory exists for custom skills;
- Optionally install system-level dependencies (nodejs, npm, uv) when enabled;

Requirements
------------

- `community.general` Ansible collection (for `community.general.npm` module)
- `npm` / `nodejs` on the target host (or enable `install_dependencies` task)
- `uv` on the target host (or enable `install_dependencies` task)

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
| `ai_opencode_version` | `latest` | OpenCode version (`latest` or pinned, e.g., `1.2.3`) |
| `ai_openspec_version` | `latest` | OpenSPEC version (`latest` or pinned) |
| `ai_speckit_version` | `latest` | SpecKit version (`latest` or pinned tag, e.g., `v0.4.4`) |
| `ai_model` | `google-vertex-anthropic/claude-opus-4-6@default` | Primary AI model |
| `ai_small_model` | `anthropic/claude-sonnet-4-5` | Small/fast AI model |
| `ai_gcp_project` | `your-gcp-project` | GCP project for Vertex AI (see note below) |
| `ai_vertex_location` | `us-central1` | GCP Vertex AI region (see note below) |
| `ai_agent_script_name` | `mybuddy` | Name of the wrapper script in `~/bin/` |
| `ai_opencode_instructions` | `[".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]` | Instruction files for OpenCode |
| `ai_trusted_github_orgs` | `[]` | Trusted GitHub organizations for command security |

### Google Vertex AI Configuration

If you are using Google Vertex AI as the model provider, you **must** set the following
variables to your real values in your playbook:

```yaml
ai_gcp_project: "my-actual-gcp-project"
ai_vertex_location: "us-east5"
```

If you are **not** using Vertex AI (e.g., using a direct Anthropic API key), these variables
are harmlessly ignored -- the wrapper script exports them as environment variables, but
OpenCode only reads them when the provider is `google-vertex-anthropic`.

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

### Custom Commands and Skills

The role deploys managed commands to `~/.config/opencode/command/`. This path is
OpenCode-specific -- no agent-neutral command directory exists. You can add your own
command `.md` files alongside the managed ones; the role will not touch files it does
not manage.

For custom **skills**, prefer the agent-neutral directory `~/.agents/skills/` over
`~/.config/opencode/skills/`. OpenCode natively discovers skills from `~/.agents/skills/`
(via its cross-agent discovery mechanism), and this path is also compatible with Claude Code
and other agents that follow the `.agents/` convention. This means your custom skills
will continue to work if you switch AI agents.

Both directories are created by the role automatically.

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
      - { enabled: true, name: 'install_dependencies' }
      - { enabled: true, name: 'install_opencode' }
      - { enabled: true, name: 'configure_opencode' }
      - { enabled: true, name: 'install_openspec' }
      - { enabled: true, name: 'install_speckit' }
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

**With selective tasks (OpenCode only, no SpecKit):**

```yaml
---
- hosts: my_linux
  vars:
    ai_tasks:
      - { enabled: false, name: 'install_dependencies' }
      - { enabled: true,  name: 'install_opencode' }
      - { enabled: true,  name: 'configure_opencode' }
      - { enabled: true,  name: 'install_openspec' }
      - { enabled: false, name: 'install_speckit' }
  roles:
    - ansible-role-ai
```

License
-------

Apache-2.0

Author Information
------------------

Marcus Burghardt
- [https://github.com/marcusburghardt](https://github.com/marcusburghardt)
- [https://www.linkedin.com/in/marcusburghardt](https://www.linkedin.com/in/marcusburghardt)
