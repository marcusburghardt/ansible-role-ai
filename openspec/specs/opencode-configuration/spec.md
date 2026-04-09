### Requirement: Deploy OpenCode configuration file from template
The role SHALL deploy the OpenCode configuration file to `ai_opencode_config_file` (default: `~/.config/opencode/opencode.json`) using a Jinja2 template. The template SHALL incorporate variables for model, small_model, provider settings, disabled providers, permissions, compaction settings, and a variable-driven instructions file list (`ai_opencode_instructions`).

#### Scenario: Configuration file is deployed with default settings
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** the role creates or overwrites `~/.config/opencode/opencode.json` from the `opencode.json.j2` template with the values from role variables, with file mode `0600`

#### Scenario: Configuration file reflects variable overrides
- **WHEN** the consumer overrides `ai_model` to `anthropic/claude-sonnet-4-5` and `ai_gcp_project` to `my-project`
- **THEN** the deployed `opencode.json` SHALL contain the overridden model and GCP project values

#### Scenario: Instructions list includes org governance files by default
- **WHEN** the role deploys with default `ai_opencode_instructions` value
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `[".specify/memory/constitution.md", "AGENTS.md", "CLAUDE.md"]`, aligning with the SpecKit-standard constitution path

#### Scenario: Instructions list is customizable
- **WHEN** the consumer overrides `ai_opencode_instructions` to `["CUSTOM.md"]`
- **THEN** the `instructions` array in the deployed `opencode.json` SHALL contain `["CUSTOM.md"]`

#### Scenario: Configuration directory is created if missing
- **WHEN** the parent directory of `ai_opencode_config_file` does not exist
- **THEN** the role SHALL create the directory structure before deploying the config file

### Requirement: Deploy AI agent wrapper script from template
The role SHALL deploy a wrapper script to `ai_user_scripts_dir/ai_agent_script_name` (default: `~/bin/mybuddy`) using a Jinja2 template. The script SHALL export GCP environment variables (`GCP_PROJECT`, `VERTEX_LOCATION`), a `TRUSTED_GITHUB_ORGS` variable (comma-separated list from `ai_trusted_github_orgs`), and launch `opencode`.

#### Scenario: Wrapper script is deployed
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** the role creates or overwrites the wrapper script at `{{ ai_user_scripts_dir }}/{{ ai_agent_script_name }}` with mode `0750`

#### Scenario: Wrapper script contains correct environment variables
- **WHEN** the script is deployed with `ai_gcp_project` set to `my-gcp-project` and `ai_vertex_location` set to `us-central1`
- **THEN** the script SHALL contain `export GCP_PROJECT="my-gcp-project"` and `export VERTEX_LOCATION="us-central1"`

#### Scenario: Wrapper script exports trusted GitHub organizations
- **WHEN** `ai_trusted_github_orgs` is set to `["myorg", "partnerorg"]`
- **THEN** the wrapper script SHALL contain `export TRUSTED_GITHUB_ORGS="myorg,partnerorg"`

### Requirement: Commands include trusted organization verification
The `checkout_pr.md` and `review_pr.md` commands SHALL include a pre-flight verification step before performing any operations. The command SHALL instruct the AI agent to check the current repository's owner (via `gh repo view --json owner --jq '.owner.login'`) against the `TRUSTED_GITHUB_ORGS` environment variable. If the owner matches a trusted org, the command proceeds silently. If the owner does not match (or `TRUSTED_GITHUB_ORGS` is empty), the command SHALL warn the user and ask for explicit confirmation before continuing.

#### Scenario: Command proceeds on trusted org repo
- **WHEN** the user runs `/checkout_pr 42` in a repo owned by an org listed in `TRUSTED_GITHUB_ORGS`
- **THEN** the command proceeds without prompting

#### Scenario: Command warns on untrusted org repo
- **WHEN** the user runs `/checkout_pr 42` in a repo owned by an org NOT listed in `TRUSTED_GITHUB_ORGS`
- **THEN** the command warns the user and asks for confirmation before proceeding

#### Scenario: Command warns when no trusted orgs configured
- **WHEN** `TRUSTED_GITHUB_ORGS` is empty or unset
- **THEN** the command warns the user and asks for confirmation before proceeding

### Requirement: Deploy Ansible-managed commands to user config directory
The role SHALL auto-discover all `.md` files in the role's `files/commands/` directory at runtime and deploy them to `{{ ai_opencode_command_dir }}`. Commands whose basename (minus `.md`) appears in `ai_opencode_commands_disabled` SHALL be skipped. After built-in deployment, custom commands from `ai_opencode_commands_custom` SHALL be deployed, each using its `src` path as the source and `name` (or basename of `src`) as the destination filename. All command files SHALL be copied as-is without template processing using `ansible.builtin.copy` with mode `0640`. Managed files SHALL be overwritten on every role execution. The role SHALL NOT delete, modify, or interfere with any other files in the command directory that are not part of the current deployment run.

#### Scenario: Default behavior deploys all built-in commands
- **WHEN** `ai_opencode_commands_disabled` is empty and `ai_opencode_commands_custom` is empty
- **THEN** all `.md` files in `files/commands/` SHALL be deployed to `{{ ai_opencode_command_dir }}`

#### Scenario: Built-in command is disabled
- **WHEN** `ai_opencode_commands_disabled` contains `checkout_pr`
- **THEN** `checkout_pr.md` SHALL NOT be deployed, but all other built-in commands SHALL be

#### Scenario: Custom command is deployed alongside built-ins
- **WHEN** `ai_opencode_commands_custom` contains `{ src: ../my-commands/deploy.md }`
- **THEN** `deploy.md` SHALL be deployed to `{{ ai_opencode_command_dir }}` alongside the built-in commands

#### Scenario: User-created commands are not affected
- **WHEN** the user has created custom command files directly in `{{ ai_opencode_command_dir }}`
- **THEN** those files SHALL remain untouched after the role runs

#### Scenario: Commands directory is created if missing
- **WHEN** the `{{ ai_opencode_command_dir }}` directory does not exist
- **THEN** the role SHALL create it before deploying command files

### Requirement: Deploy refresh command for per-repo framework artifact updates
The role SHALL deploy a `refresh.md` command that instructs OpenCode to detect which spec-driven development framework is initialized in the current repository and run the appropriate update command. For OpenSpec repositories (detected by the presence of an `openspec/` directory), the command SHALL run `openspec update`. For SpecKit repositories (detected by the presence of a `.specify/` directory), the command SHALL run `specify init --here --ai opencode --force`. If both frameworks are present, both update commands SHALL be run. This enables users to refresh per-repo framework artifacts (commands, skills, scripts, templates) after CLI tools have been updated globally.

#### Scenario: Refresh OpenSpec repository
- **WHEN** the user runs `/refresh` in a repository that contains an `openspec/` directory
- **THEN** OpenCode SHALL execute `openspec update` to regenerate per-repo skills and commands to match the current CLI version

#### Scenario: Refresh SpecKit repository
- **WHEN** the user runs `/refresh` in a repository that contains a `.specify/` directory
- **THEN** OpenCode SHALL execute `specify init --here --ai opencode --force` to regenerate per-repo commands, scripts, and templates to match the current CLI version

#### Scenario: Refresh repository with both frameworks
- **WHEN** the user runs `/refresh` in a repository that contains both `openspec/` and `.specify/` directories
- **THEN** OpenCode SHALL execute both update commands

#### Scenario: No framework detected
- **WHEN** the user runs `/refresh` in a repository with neither `openspec/` nor `.specify/` directories
- **THEN** OpenCode SHALL report that no spec-driven development framework is initialized in the current repository

### Requirement: Ensure user skills directories exist (OpenCode-specific and agent-neutral)
The role SHALL ensure both `{{ ai_opencode_skills_dir }}` (OpenCode-specific) and `{{ ai_user_home_dir }}/.agents/skills/` (agent-neutral) directories exist. Built-in skills from `files/skills/` SHALL be auto-discovered and deployed to `{{ ai_opencode_skills_deploy_dir }}` (resolved via `ai_skills_target`), filtered against `ai_opencode_skills_disabled`. Custom skills from `ai_opencode_skills_custom` SHALL be deployed after built-ins. The role SHALL NOT delete, modify, or interfere with any other directories in the skills directory that are not part of the current deployment run.

#### Scenario: OpenCode skills directory is created if missing
- **WHEN** the `{{ ai_opencode_skills_dir }}` directory does not exist
- **THEN** the role SHALL create it

#### Scenario: Agent-neutral skills directory is created if missing
- **WHEN** the `{{ ai_user_home_dir }}/.agents/skills/` directory does not exist
- **THEN** the role SHALL create it

#### Scenario: Built-in skills are deployed to configured target
- **WHEN** `files/skills/` contains skill directories and `ai_skills_target` is `agent-neutral`
- **THEN** the skills SHALL be deployed to `{{ ai_user_home_dir }}/.agents/skills/`

#### Scenario: Custom skills are deployed alongside built-ins
- **WHEN** `ai_opencode_skills_custom` contains `{ src: /opt/team/my-skill }`
- **THEN** the `my-skill/` directory SHALL be deployed to `{{ ai_opencode_skills_deploy_dir }}/my-skill/`

#### Scenario: User-created skills are not affected
- **WHEN** the user has created custom skill directories in the skills deploy directory
- **THEN** those directories and files SHALL remain untouched after the role runs

### Requirement: Deploy commit standards as a global baseline instruction file
The role SHALL deploy a `commit.md` file to `~/.config/opencode/` containing universal commit standards. The file SHALL specify: Conventional Commits message format, mandatory Signed-off-by trailer (via `git commit -s`), and mandatory Assisted-by trailer for AI-assisted commits identifying the tool and model. The file SHALL explicitly state that these are baseline defaults and that any conflicting rules in repository-level files (such as `constitution.md`, `AGENTS.md`, `CONTRIBUTING.md`, or any other file used by AI tools in the repository) take precedence. The file SHALL be referenced in `ai_opencode_instructions` via `~/.config/opencode/commit.md` so it is always loaded.

#### Scenario: Commit rules apply in repos without a constitution
- **WHEN** the user works in a repository that has no `constitution.md`, `AGENTS.md`, or other commit guidance
- **THEN** OpenCode SHALL follow the commit standards from `~/.config/opencode/commit.md`

#### Scenario: Repository-level rules override commit.md
- **WHEN** the user works in a repository that has a `constitution.md` or `AGENTS.md` with commit rules that conflict with `commit.md`
- **THEN** the repository-level rules SHALL take precedence and OpenCode SHALL follow them instead

#### Scenario: Commit.md is deployed and updated by the role
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** `commit.md` SHALL be deployed to `~/.config/opencode/commit.md` and overwritten on every role execution

#### Scenario: Commit.md is loaded first in instructions order
- **WHEN** examining the `ai_opencode_instructions` default
- **THEN** `~/.config/opencode/commit.md` SHALL appear before repository-relative instruction files so that repo-level files can override it via last-wins semantics

### Requirement: Skip configuration when task is disabled
The role SHALL skip all configuration activities when the `configure_opencode` task entry has `enabled: false`.

#### Scenario: Configuration is skipped
- **WHEN** the `configure_opencode` task entry has `enabled: false` in `ai_tasks`
- **THEN** the role SHALL NOT deploy the config file, wrapper script, commands, or skills
