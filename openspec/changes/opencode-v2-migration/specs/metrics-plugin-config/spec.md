# Spec Delta

## MODIFIED Requirements

### Requirement: Metrics plugin version variable
The role SHALL provide an `ai_opencode_metrics_version` variable (default: `"0.3.0"`)
that controls how the opencode-metrics plugin is installed. Accepted values are:
- A semver version string (e.g., `"0.3.0"`) -- installs the pinned version from npm.
- `"latest"` -- always installs the newest npm release.
- `"local"` -- loads the plugin from a local repository path specified by
  `ai_opencode_metrics_local_path` instead of npm.

While the opencode-metrics plugin is pending V2 migration, the default
`ai_opencode_plugins` list SHALL be empty `[]` regardless of the
`ai_opencode_metrics_version` value. The metrics plugin SHALL NOT be included in
the `plugins` array until it has been ported to the OpenCode V2 plugin API. The
local loader mechanism and config deployment SHALL continue to function for
development and testing purposes.

#### Scenario: Default version is pinned
- **WHEN** the consumer does not override `ai_opencode_metrics_version`
- **THEN** `ai_opencode_metrics_version` SHALL be `"0.3.0"` but the default `ai_opencode_plugins` list SHALL be `[]` (metrics plugin excluded pending V2 migration)

#### Scenario: User overrides version
- **WHEN** the consumer sets `ai_opencode_metrics_version` to `"1.0.0"`
- **THEN** the version variable SHALL be stored for use by the local loader mechanism but the default `ai_opencode_plugins` list SHALL remain `[]`

#### Scenario: Local mode excludes npm entry from plugins list
- **WHEN** the consumer sets `ai_opencode_metrics_version` to `"local"`
- **THEN** the `ai_opencode_plugins` default list SHALL be `[]` and the local loader file SHALL still be deployed for development testing
