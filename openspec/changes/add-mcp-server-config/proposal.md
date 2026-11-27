# Proposal

## Why

The role owns the whole OpenCode configuration file, so a server added with
`opencode mcp add` disappears on the next playbook run. Consumers that need MCP
servers, such as a local Playwright server attached to an existing browser,
currently have no role-managed way to declare them. Adding first-class MCP
server configuration keeps that setting reviewable, versioned, and idempotent.

## What Changes

- Add an `ai_opencode_mcp_servers` dict variable, defaulting to `{}`, that is
  rendered as the OpenCode V2 `mcp.servers` block.
- Render the `mcp` block unconditionally so the empty default is explicit and
  consumers cannot inherit a stale server from a previous hand edit.
- Document the variable with a local-command example, and note that server
  installation and permission rules remain consumer responsibilities.
- Extend the Ansible smoke test to cover the empty default and a consumer
  override.

Out of scope: installing a specific MCP server package, granting or denying MCP
tool permissions, and remote-server OAuth settings. Consumers express all three
through existing variables or their own playbook tasks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `opencode-configuration`: the template variable contract gains
  `ai_opencode_mcp_servers`, and the deployed configuration gains an `mcp`
  block.

## Impact

- **Files modified**: `defaults/main.yml`, `templates/opencode.json.j2`,
  `tests/test.yml`, `README.md`.
- **Defaults**: one new role variable, empty by default.
- **Compatibility**: additive. An empty default renders `"mcp": {"servers": {}}`,
  which changes no existing behavior. No new dependencies, tasks, or handlers.
- **Specs**: one modified capability, `opencode-configuration`.
