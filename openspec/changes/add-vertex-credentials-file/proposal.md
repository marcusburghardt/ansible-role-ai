# Proposal

## Why

The `google-vertex` provider activates only when the OpenCode shared service can
authenticate through Application Default Credentials. Today the role assumes those
credentials come from an interactive `gcloud auth application-default login`, so
consumers provisioning Vertex through an organization-issued service-account JSON key
have no role-supported way to pass it to the launcher or the shared service.

## What Changes

- New `ai_vertex_credentials_file` role variable (default: `""`) holding the path to a
  protected GCP service-account JSON key on the target host. Only the path is rendered;
  the file contents are never read by Ansible or embedded in deployed files.
- When set, the role injects `GOOGLE_APPLICATION_CREDENTIALS` (with a leading `~`
  expanded to `ai_user_home_dir`) into the OpenCode server environment by merging it
  with `ai_opencode_server_env`, so both launch paths — the launcher script and the
  role-driven service restart — receive it. Consumer entries in
  `ai_opencode_server_env` are preserved by the merge.
- When empty, the environment is unchanged, preserving the existing gcloud ADC flow.
- Launcher tests gain credentials-path coverage (exported when configured, absent when
  empty, path expanded and shell-quoted), and the service-restart test gains a play
  that verifies the handler passes the credentials path.

## Capabilities

### New Capabilities

### Modified Capabilities
- `opencode-configuration`: Adding a service-account credentials file option for the
  `google-vertex` provider that flows through the shared server environment used by
  both the launcher script and the role-driven service restart

## Impact

- **Variables**: `defaults/main.yml` — new `ai_vertex_credentials_file`;
  `vars/main.yml` — new internal `_ai_vertex_credentials_expanded` and
  `_ai_opencode_server_env_merged`
- **Templates**: `templates/ai_agent_script.sh.j2` — environment exports render from
  the merged server environment
- **Handlers**: `handlers/main.yml` — the service restart passes the merged server
  environment
- **Tests**: `tests/check_wrapper.py`, `tests/test_wrapper.yml`, `tests/test.yml` —
  launcher credentials-path coverage and a restart-with-credentials play
- **Docs**: `README.md` — variable table and the Google Vertex AI Configuration section
- **Existing users**: No breaking change; the default empty value preserves today's
  behavior, and every `ai_opencode_server_env` entry is still exported on both launch
  paths
