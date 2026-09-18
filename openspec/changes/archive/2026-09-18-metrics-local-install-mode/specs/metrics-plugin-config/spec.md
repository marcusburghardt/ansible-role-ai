# Spec Delta

## MODIFIED Requirements

### Requirement: Metrics plugin version variable
The role SHALL provide an `ai_opencode_metrics_version` variable (default: `"0.2.0"`)
that controls how the opencode-metrics plugin is installed. Accepted values are:
- A semver version string (e.g., `"0.2.0"`) — installs the pinned version from npm.
- `"latest"` — always installs the newest npm release.
- `"local"` — loads the plugin from a local repository path specified by
  `ai_opencode_metrics_local_path` instead of npm.

When the value is a semver string or `"latest"`, this variable SHALL be referenced by
the default `ai_opencode_plugins` list to construct the versioned npm package
specifier. When the value is `"local"`, the npm specifier SHALL NOT appear in
`ai_opencode_plugins`.

#### Scenario: Default version is pinned
- **WHEN** the consumer does not override `ai_opencode_metrics_version`
- **THEN** the default `ai_opencode_plugins` list SHALL contain `@mburghardt/opencode-metrics@0.2.0`

#### Scenario: User overrides version
- **WHEN** the consumer sets `ai_opencode_metrics_version` to `"1.0.0"`
- **THEN** the default `ai_opencode_plugins` list SHALL contain `@mburghardt/opencode-metrics@1.0.0`

#### Scenario: Local mode excludes npm entry from plugins list
- **WHEN** the consumer sets `ai_opencode_metrics_version` to `"local"`
- **THEN** the `ai_opencode_plugins` default list SHALL NOT contain any `@mburghardt/opencode-metrics` entry
