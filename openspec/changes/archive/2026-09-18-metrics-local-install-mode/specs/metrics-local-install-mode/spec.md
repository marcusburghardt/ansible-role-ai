# Spec Delta

## Purpose

Controls whether the opencode-metrics plugin is loaded from the npm registry (pinned
version or latest) or from a local repository on the target host, enforcing mutual
exclusivity between the two installation mechanisms and providing a documented
maintainer workflow for switching between them.

## ADDED Requirements

### Requirement: Local install mode variable
The role SHALL provide an `ai_opencode_metrics_local_path` variable (default: `""`)
that specifies the path to a local `opencode-metrics` repository on the target host.
This variable SHALL only be consulted when `ai_opencode_metrics_version` is set to
`"local"`. The path MAY use a leading tilde (`~`) which the role SHALL expand to the
target user's home directory before use.

#### Scenario: Default local path is empty
- **WHEN** the consumer does not override `ai_opencode_metrics_local_path`
- **THEN** the variable SHALL resolve to an empty string `""`

#### Scenario: Tilde is expanded to user home directory
- **WHEN** the consumer sets `ai_opencode_metrics_local_path` to `"~/GIT/me/opencode-metrics"`
- **THEN** the role SHALL expand the path to an absolute path rooted at the target user's home directory (e.g., `/home/user/GIT/me/opencode-metrics`) before writing any file

### Requirement: Local mode activation
When `ai_opencode_metrics_version` is set to `"local"` and
`ai_opencode_metrics_local_path` is non-empty, the role SHALL write a TypeScript
loader file at `~/.config/opencode/plugins/opencode-metrics.ts` that imports the
plugin directly from `<expanded_local_path>/dist/index.js`. The loader file SHALL
contain a header comment indicating it is managed by the role and MUST NOT be edited
manually.

#### Scenario: Loader file is written in local mode
- **WHEN** `ai_opencode_metrics_version` is `"local"` and `ai_opencode_metrics_local_path` is `"~/GIT/me/opencode-metrics"`
- **THEN** the role SHALL create or overwrite `~/.config/opencode/plugins/opencode-metrics.ts` with an import from the expanded absolute path to `dist/index.js`

#### Scenario: Loader file header identifies role as owner
- **WHEN** the loader file is written by the role
- **THEN** the file SHALL contain a comment stating it is managed by `ansible-role-ai` and should not be edited manually

### Requirement: Validation of local path when in local mode
The role SHALL fail with a clear, human-readable error message when
`ai_opencode_metrics_version` is `"local"` but `ai_opencode_metrics_local_path` is
empty or unset.

#### Scenario: Missing local path causes failure
- **WHEN** `ai_opencode_metrics_version` is `"local"` and `ai_opencode_metrics_local_path` is `""`
- **THEN** the role SHALL halt execution and emit an error message indicating that `ai_opencode_metrics_local_path` must be set when using local mode

### Requirement: NPM mode removes loader file
When `ai_opencode_metrics_version` is a version string or `"latest"` (npm mode), the
role SHALL ensure the loader file `~/.config/opencode/plugins/opencode-metrics.ts`
is absent. This guarantees mutual exclusivity between npm and local installation
mechanisms on each playbook run.

#### Scenario: Loader file is removed when switching to npm mode
- **WHEN** `ai_opencode_metrics_version` is a semver string (e.g., `"0.2.0"`) and the loader file exists from a previous local mode run
- **THEN** the role SHALL remove `~/.config/opencode/plugins/opencode-metrics.ts`

#### Scenario: NPM mode is idempotent when no loader file exists
- **WHEN** `ai_opencode_metrics_version` is a semver string and the loader file does not exist
- **THEN** the role SHALL complete without error and without creating any loader file

### Requirement: Report resolved plugin source during playbook run
The role SHALL emit a debug message during the `configure_opencode` task that
reports the resolved plugin installation state: the active mode (`npm` or `local`),
the raw `ai_opencode_metrics_version` value, the resolved source (npm package
specifier or expanded absolute path to `dist/index.js`), and whether a custom
`config.yaml` is being deployed. This message SHALL appear before the role takes
any action on the loader file or `opencode.json`, following the same pattern used
by `install_ollama` and `install_cursor`.

#### Scenario: NPM mode is reported
- **WHEN** `ai_opencode_metrics_version` is `"0.2.0"` and the playbook runs
- **THEN** the role SHALL emit a debug message showing `mode=npm`, `version=0.2.0`, `source=@mburghardt/opencode-metrics@0.2.0`, and the config deployment status

#### Scenario: Local mode is reported
- **WHEN** `ai_opencode_metrics_version` is `"local"` and `ai_opencode_metrics_local_path` is `"~/GIT/me/opencode-metrics"` and the playbook runs
- **THEN** the role SHALL emit a debug message showing `mode=local`, `version=local`, `source=<expanded_path>/dist/index.js`, and the config deployment status

### Requirement: Maintainer local development workflow
The role documentation SHALL describe the expected steps a maintainer must perform
when using `"local"` mode, so that the workflow can be consulted without reading role
source code. This documentation SHALL live in the role's `README.md` under a
dedicated section.

#### Scenario: Workflow documentation is present
- **WHEN** a maintainer reads the role README
- **THEN** they SHALL find a section describing the local mode workflow: editing the local repo, building `dist/`, setting the role variables, running the playbook, and restarting OpenCode
