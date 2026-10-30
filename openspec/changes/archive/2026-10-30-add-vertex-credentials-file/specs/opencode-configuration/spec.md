# Spec Delta

## ADDED Requirements

### Requirement: Vertex service-account credentials file
The role SHALL provide an `ai_vertex_credentials_file` variable (default: `""`) with the path to a protected GCP service-account JSON key. When set, the role SHALL inject `GOOGLE_APPLICATION_CREDENTIALS` with the tilde-expanded path into the server environment used by both the launcher and the role-driven service restart, merged with `ai_opencode_server_env` so consumer entries are preserved. When empty, the environment SHALL be unchanged; the key file is never read by the role.

#### Scenario: Launcher exports the credentials path when configured
- **WHEN** the consumer sets `ai_vertex_credentials_file` to `~/.config/vertex/service-account.json`
- **THEN** the deployed launcher script SHALL export `GOOGLE_APPLICATION_CREDENTIALS` with the path expanded to `ai_user_home_dir`, and every entry of `ai_opencode_server_env` SHALL still be exported

#### Scenario: Launcher omits the variable when not configured
- **WHEN** `ai_vertex_credentials_file` is empty
- **THEN** the launcher script SHALL NOT export `GOOGLE_APPLICATION_CREDENTIALS`

#### Scenario: Service restart receives the credentials path
- **WHEN** `ai_vertex_credentials_file` is set and the role restarts a running shared service
- **THEN** the restarted service SHALL receive `GOOGLE_APPLICATION_CREDENTIALS` alongside every `ai_opencode_server_env` entry

#### Scenario: Consumer server environment entries are preserved
- **WHEN** the consumer overrides `ai_opencode_server_env` and sets `ai_vertex_credentials_file`
- **THEN** both the consumer entries and `GOOGLE_APPLICATION_CREDENTIALS` SHALL reach the launcher and the restarted service

#### Scenario: Credentials path is quoted and only the path is rendered
- **WHEN** the credentials path contains spaces or shell metacharacters
- **THEN** the launcher export SHALL be safely quoted, and the key file contents SHALL NOT appear in any deployed file
