# Tasks

## 1. Server environment merge

- [x] 1.1 Add `ai_vertex_credentials_file` (default: `""`) with a comment matching the
  `ai_enmaas_key_file` contract to `defaults/main.yml` next to `ai_gcp_project` /
  `ai_vertex_location`. Verify with `yamllint defaults/main.yml`.
- [x] 1.2 Add `_ai_vertex_credentials_expanded` (tilde expansion, trailing-slash strip,
  empty passthrough) and `_ai_opencode_server_env_merged` (`combine` injection when the
  path is set, otherwise `ai_opencode_server_env` unchanged) to `vars/main.yml` so the
  restart handler can reference them even when `configure_opencode` is disabled. Verify
  with `yamllint vars/main.yml`.
- [x] 1.3 Switch `templates/ai_agent_script.sh.j2` and the service-restart handler in
  `handlers/main.yml` from `ai_opencode_server_env` to `_ai_opencode_server_env_merged`.
  Verify with `ansible-playbook tests/test.yml` — existing wrapper and restart-marker
  assertions must still pass.

## 2. Tests

- [x] 2.1 Extend `tests/test_wrapper.yml` with a third launcher render that sets
  `ai_vertex_credentials_file` to a path containing `~`, a space, and an apostrophe, and
  passes it plus the expanded path to `check_wrapper.py`. Verify the rendered script
  contains the expanded, quoted `GOOGLE_APPLICATION_CREDENTIALS` export.
- [x] 2.2 Extend `tests/check_wrapper.py` so the mock `opencode` asserts the launched
  environment: `GOOGLE_APPLICATION_CREDENTIALS` equals the expected expanded path for the
  vertex launcher and is unset for the other launchers (positive and negative cases).
  Verify with the wrapper test run inside `tests/test.yml`.
- [x] 2.3 Extend `tests/test.yml`: assert the default launcher does not export
  `GOOGLE_APPLICATION_CREDENTIALS`, and add a play with `ai_vertex_credentials_file` set
  whose fake binary records the handler-passed environment. Verify the restart marker
  contains the expanded credentials path.

## 3. Documentation

- [x] 3.1 Document `ai_vertex_credentials_file` in the `README.md` variable table and
  extend the Google Vertex AI Configuration section with the service-account key flow
  (path-only rendering, both launch paths, empty preserves gcloud ADC). Verify by
  reading the rendered section against the implemented behavior.

## 4. Validation

- [x] 4.1 Run `ansible-playbook tests/test.yml` end to end and confirm all assertions
  pass, including the new vertex scenarios.
- [x] 4.2 Run `yamllint .` and `ansible-lint` on the role and fix any findings introduced
  by this change.
