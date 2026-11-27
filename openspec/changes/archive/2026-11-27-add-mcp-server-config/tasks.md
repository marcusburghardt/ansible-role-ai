# Tasks

## 1. Configuration plumbing

- [x] 1.1 Add `ai_opencode_mcp_servers: {}` to `defaults/main.yml` with a comment
  that entries are complete OpenCode V2 server objects; verify with
  `ansible-doc -t role ansible-role-ai` or by reading the rendered defaults.
- [x] 1.2 Render `"mcp": { "servers": {{ ai_opencode_mcp_servers | to_json }} }`
  in `templates/opencode.json.j2`; verify the empty default produces valid JSON
  containing `mcp.servers` as an empty object.
- [x] 1.3 Extend `tests/test.yml` so the defaults assertion covers
  `_ai_config.mcp.servers == {}` and the override case renders a sample local
  server with its `type` and `command` unchanged; verify with `make test`.
- [x] 1.4 Assert in `tests/test.yml` that the sample server name appears only
  under `mcp.servers` and that a `disabled: true` entry is preserved; verify the
  same `make test` run fails when either assertion is removed.

## 2. Documentation

- [x] 2.1 Add an `ai_opencode_mcp_servers` row to the README variable table and
  a short section with a local `command` example, the V2 `mcp.servers` location,
  and the note that installation and permissions are consumer responsibilities.
- [x] 2.2 State the secrets guidance (prefer `{env:...}` or a protected file
  reference over inline values) and verify the example renders as documented by
  running the playbook syntax check with the sample value.
- [x] 2.3 Confirm the README does not reproduce the V1 `mcp.<name>` or `enabled`
  shape; verify by searching the README for those patterns.

## 3. Integration checks

- [x] 3.1 Run `make test` and confirm every test target passes.
- [x] 3.2 Run `make lint` and confirm yamllint, ruff, and the Ansible syntax
  check pass.
- [x] 3.3 Run `openspec validate add-mcp-server-config --strict` and confirm no
  warnings or errors.

## Workflow follow-up

- Archive the change after review.
- In the consuming playbook (`~/GIT/mbtech/Ansible/dev_ai.yml`), set
  `ai_opencode_mcp_servers` and re-run the playbook against a symlinked role
  checkout; then replace the symlink with a normal role install after release.
