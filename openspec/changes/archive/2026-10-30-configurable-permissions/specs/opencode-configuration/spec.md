# Spec Delta

## MODIFIED Requirements

### Requirement: Deploy OpenCode configuration file from template
The role SHALL deploy the OpenCode configuration file to `ai_opencode_config_file` (default: `~/.config/opencode/opencode.json`) using a Jinja2 template. The template SHALL incorporate variables for model, small_model, agent routing (`ai_opencode_agents`), plugin list (`ai_opencode_plugins`), provider settings, disabled providers, permissions (`_ai_opencode_permissions_default` merged with `ai_opencode_permissions`), compaction settings (`ai_opencode_compaction`), and a variable-driven instructions file list (`ai_opencode_instructions`).

#### Scenario: Configuration file is deployed with default settings
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** the role creates or overwrites `~/.config/opencode/opencode.json` from the `opencode.json.j2` template with the values from role variables, with file mode `0600`

#### Scenario: Configuration file reflects variable overrides
- **WHEN** the consumer overrides `ai_model` to `anthropic/claude-sonnet-4-5` and `ai_gcp_project` to `my-project`
- **THEN** the deployed `opencode.json` SHALL contain the overridden model and GCP project values

#### Scenario: Instructions list includes org governance files by default
- **WHEN** the role deploys with default `ai_opencode_instructions` value
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["~/.config/opencode/commit.md", "~/.config/opencode/coding-standards.md", ".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]`, with global baseline files preceding repository-relative paths

#### Scenario: Instructions list is customizable
- **WHEN** the consumer overrides `ai_opencode_instructions` to `["CUSTOM.md"]`
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["CUSTOM.md"]`

#### Scenario: Configuration directory is created if missing
- **WHEN** the parent directory of `ai_opencode_config_file` does not exist
- **THEN** the role SHALL create the directory structure before deploying the config file

#### Scenario: Agent routing block is rendered from variable
- **WHEN** the role deploys with default `ai_opencode_agents` value and default `ai_model` / `ai_small_model` (both `ollama/qwen3:8b`)
- **THEN** the deployed `opencode.json` SHALL contain an `"agent"` block with `build`, `plan`, `explore`, and `general` keys, all with `model` set to `ollama/qwen3:8b`

#### Scenario: Agent routing reflects per-agent model overrides
- **WHEN** the consumer sets `ai_opencode_agent_plan_model` to `google-vertex-anthropic/claude-sonnet-4-6@default` and `ai_opencode_agent_explore_model` to `google-vertex-anthropic/claude-haiku-4-5@20251001`
- **THEN** the deployed `opencode.json` SHALL contain an `"agent"` block where `plan.model` is `google-vertex-anthropic/claude-sonnet-4-6@default` and `explore.model` is `google-vertex-anthropic/claude-haiku-4-5@20251001`, while `build` and `general` retain their defaults

#### Scenario: Plugin list renders metrics plugin by default
- **WHEN** the role deploys with default `ai_opencode_plugins` value
- **THEN** the deployed `opencode.json` SHALL contain `"plugin": ["@mburghardt/opencode-metrics@0.3.0"]`

#### Scenario: Compaction settings are rendered from variable
- **WHEN** the role deploys with default `ai_opencode_compaction` value
- **THEN** the deployed `opencode.json` SHALL contain `"compaction": {"auto": true, "prune": true, "reserved": 10000}`

#### Scenario: Compaction settings reflect user overrides
- **WHEN** the consumer overrides `ai_opencode_compaction` to `{"auto": true, "prune": false, "reserved": 5000}`
- **THEN** the deployed `opencode.json` SHALL contain the overridden compaction values

#### Scenario: Permission block is rendered from merged variables
- **WHEN** the role deploys with default settings and the consumer does not override `ai_opencode_permissions`
- **THEN** the deployed `opencode.json` SHALL contain a `"permission"` block rendered from `_ai_opencode_permissions_default` alone

#### Scenario: Permission block merges user overrides on top of defaults
- **WHEN** the consumer overrides `ai_opencode_permissions` with `{bash: {"poetry *": "allow"}, read: {"*credentials*": "deny"}}`
- **THEN** the deployed `opencode.json` SHALL contain a `"permission"` block where the default rules are present AND the user's additional rules are also present, with user rules taking precedence for any key that appears in both

## ADDED Requirements

### Requirement: Data-driven permission defaults
The role SHALL provide an internal variable `_ai_opencode_permissions_default` in `vars/configure_opencode.yml` containing a three-tier permission rule set for OpenCode. The defaults SHALL include bash, read, edit, and external_directory sub-sections.

#### Scenario: Default bash permissions include catch-all ask
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"*": "ask"` as the default for unrecognized commands

#### Scenario: Default bash permissions allow read-only commands
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"allow"` entries for read-only commands including `cat *`, `cd *`, `diff *`, `echo *`, `file *`, `find *`, `grep *`, `head *`, `jq *`, `less *`, `ls *`, `rg *`, `sort *`, `tail *`, `test *`, `tree *`, `wc *`, and `which *`

#### Scenario: Default bash permissions allow git read-only and staging commands
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"allow"` entries for git read and staging commands including `git add *`, `git -C *`, `git blame *`, `git branch*`, `git checkout*`, `git config *`, `git diff *`, `git fetch *`, `git log *`, `git ls-files *`, `git ls-remote *`, `git ls-tree *`, `git merge-base *`, `git mv *`, `git pull *`, `git remote *`, `git rev-parse *`, `git show *`, `git show-ref *`, `git stash *`, `git status *`, and `git symbolic-ref *`

#### Scenario: Default bash permissions allow GitHub CLI with base allow rule
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"gh *": "allow"` as a base rule for GitHub CLI commands

#### Scenario: Default bash permissions ask for git write operations
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"ask"` entries for `git commit *`, `git merge *`, `git push *`, `git rebase *`, `git reset *`, and `git tag *`

#### Scenario: Default bash permissions ask for GitHub write operations
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"ask"` entries for `gh issue close *`, `gh issue comment *`, `gh issue create *`, `gh issue edit *`, `gh pr close *`, `gh pr comment *`, `gh pr create *`, `gh pr edit *`, `gh pr merge *`, `gh pr review *`, and `gh release create *`

#### Scenario: Default bash permissions ask for GitHub API write methods
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"ask"` entries for `gh api --method POST *`, `gh api --method PUT *`, `gh api --method DELETE *`, `gh api --method PATCH *`, `gh api -X POST *`, `gh api -X PUT *`, `gh api -X DELETE *`, `gh api -X PATCH *`, and `gh api graphql *`

#### Scenario: Default bash permissions ask for file deletion
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"rm *": "ask"`

#### Scenario: Default bash permissions deny system administration commands
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"deny"` entries for `at *`, `chown *`, `crontab *`, `dd *`, `dnf *`, `fdisk *`, `firewall-cmd *`, `iptables *`, `kill *`, `killall *`, `mkfs *`, `mount *`, `nft *`, `pkill *`, `reboot`, `shutdown *`, `su *`, `sudo *`, `systemctl *`, and `umount *`

#### Scenario: Default bash permissions allow dev tools
- **WHEN** the role deploys with default settings
- **THEN** the `permission.bash` block SHALL contain `"allow"` entries for `openspec *`, `yamllint *`, and `.specify/scripts/bash/*`

#### Scenario: Default read permissions deny secrets and credentials
- **WHEN** the role deploys with default settings
- **THEN** the `permission.read` block SHALL contain `"*": "allow"` as the default and `"deny"` entries for `*.cer`, `*.crt`, `*.env`, `*.env.*`, `*.jks`, `*.kdbx`, `*.key`, `*.keystore`, `*.p12`, `*.p8`, `*.pem`, `*.pfx`, `*.priv*`, `*.secret*`, `*id_ecdsa*`, `*id_ed25519*`, and `*id_rsa*`

#### Scenario: Default edit permission is allow
- **WHEN** the role deploys with default settings
- **THEN** the `permission.edit` value SHALL be `"allow"`

#### Scenario: Default external_directory permissions deny system paths and allow tmp
- **WHEN** the role deploys with default settings
- **THEN** the `permission.external_directory` block SHALL contain `"deny"` entries for `/boot/**`, `/etc/**`, `/proc/**`, `/sys/**`, `/usr/**`, and `/var/**`, and an `"allow"` entry for `/tmp/**`

### Requirement: User-customizable permission overrides
The role SHALL provide an `ai_opencode_permissions` dict variable (default: `{}`) in `defaults/main.yml`. The template SHALL merge this variable on top of `_ai_opencode_permissions_default` using Ansible's `combine` filter with `recursive=True`, so that user-provided rules overlay on top of role defaults without replacing them entirely.

#### Scenario: Empty user override preserves all defaults
- **WHEN** the consumer does not set `ai_opencode_permissions` (or sets it to `{}`)
- **THEN** the deployed permission block SHALL be identical to `_ai_opencode_permissions_default`

#### Scenario: User adds new bash allow rules
- **WHEN** the consumer sets `ai_opencode_permissions` to `{bash: {"poetry *": "allow", "cargo *": "allow"}}`
- **THEN** the deployed `permission.bash` block SHALL contain all default rules plus `"poetry *": "allow"` and `"cargo *": "allow"`

#### Scenario: User overrides a default rule
- **WHEN** the consumer sets `ai_opencode_permissions` to `{bash: {"rm *": "deny"}}`
- **THEN** the deployed `permission.bash` block SHALL contain `"rm *": "deny"` instead of the default `"rm *": "ask"`, with all other default rules unchanged

#### Scenario: User adds external_directory rules
- **WHEN** the consumer sets `ai_opencode_permissions` to `{external_directory: {"~/GIT/**": "allow", "~/.config/opencode/**": "allow"}}`
- **THEN** the deployed `permission.external_directory` block SHALL contain the default deny rules plus `"~/GIT/**": "allow"` and `"~/.config/opencode/**": "allow"`

#### Scenario: User adds read deny patterns
- **WHEN** the consumer sets `ai_opencode_permissions` to `{read: {"*credentials*": "deny", "*vault*pass*": "deny"}}`
- **THEN** the deployed `permission.read` block SHALL contain all default deny patterns plus `"*credentials*": "deny"` and `"*vault*pass*": "deny"`
