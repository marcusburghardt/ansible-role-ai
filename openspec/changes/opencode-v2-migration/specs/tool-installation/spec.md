# Spec Delta

## ADDED Requirements

### Requirement: Install OpenCode V2 CLI via npm
The role SHALL remove the global V1 `opencode-ai` npm package using `state: absent` before installing the `@opencode/cli` npm package globally using `community.general.npm`. Both packages own the `opencode` executable. Removal SHALL be idempotent when V1 is absent. The version behavior SHALL remain: when `ai_opencode_version` is `"latest"`, use `state: latest`; when pinned, use the specified version with `state: present`.

#### Scenario: V2 package is installed
- **WHEN** the `install_opencode` task runs
- **THEN** the npm module SHALL install `@opencode/cli` globally

#### Scenario: V1 package is removed before V2 installation
- **WHEN** the `install_opencode` task runs
- **THEN** the npm module SHALL remove `opencode-ai` before installing `@opencode/cli`, and SHALL NOT install `opencode-ai`

#### Scenario: Version pinning works with V2 package
- **WHEN** `ai_opencode_version` is set to `"2.0.0"`
- **THEN** the npm module SHALL install `@opencode/cli` at version `2.0.0` with `state: present`

#### Scenario: Latest version tracking works with V2 package
- **WHEN** `ai_opencode_version` is `"latest"`
- **THEN** the npm module SHALL install `@opencode/cli` with `state: latest`
