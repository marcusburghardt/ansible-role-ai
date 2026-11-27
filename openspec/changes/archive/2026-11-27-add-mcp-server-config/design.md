# Design

## Context

See `proposal.md` for motivation. The role deploys `opencode.json` from a single
Jinja2 template, and `configure_opencode` rewrites the file on every run.
Existing blocks (`agents`, `providers`, `permissions`, `compaction`) are each
fed by one variable whose value is rendered mostly verbatim. OpenCode V2 keeps
servers under `mcp.servers`, a shape the current template does not emit.

## Goals / Non-Goals

**Goals:**

- Give consumers an idempotent, role-managed place to declare MCP servers.
- Preserve the existing variable-per-block convention and file mode `0600`.
- Keep the default behavior unchanged and testable.

**Non-Goals:**

- Installing any MCP server package or browser extension.
- Validating individual server objects beyond JSON rendering.
- Managing MCP tool permissions, OAuth credentials, or secrets.
- Changing the service-restart handler.

## Decisions

**One dict variable rendered verbatim.**
`ai_opencode_mcp_servers` mirrors `ai_opencode_providers`: the consumer supplies
complete V2 server objects, and the role does not model `type`, `command`,
`url`, `environment`, `timeout`, `disabled`, `codemode`, or future fields
individually. This avoids duplicating a schema the role does not own and lets
new OpenCode fields pass through without a role release.

Alternative considered: typed per-server variables. Rejected because it grows
the role surface for every OpenCode feature and makes heterogeneous servers
(local, remote, OAuth) hard to express.

**Always render the `mcp` block, even when empty.**
An empty `ai_opencode_mcp_servers` renders `"mcp": {"servers": {}}`. A
conditional block would leave a server added by `opencode mcp add` in place
after the role runs, which is the problem this change solves.

Alternative considered: render only when non-empty. Rejected because it makes
removal ambiguous and breaks the role's "template is the source of truth"
contract.

**Keep server installation and permissions out of the role.**
The role owns the mechanism (render configuration); the consumer owns policy
(which server, which permissions, which secrets). Installation stays available
through existing npm tasks in a playbook, and tool permissions stay in
`ai_opencode_permissions`. This keeps the change small and avoids coupling the
role to one vendor.

**Test at both ends.**
The smoke test parses the deployed JSON and asserts the empty default, and
renders the template with a sample override to assert passthrough. This matches
how other template variables are covered.

## Risks / Trade-offs

- **Invalid server objects reach OpenCode unfiltered** → Intentional; OpenCode
  validates its own config and reports the error. The README points at the
  schema, and the role does not pretend to be a validator.
- **OpenCode changes the `mcp` schema** → Consumers update their dict; the role
  needs no change unless the top-level key moves. The smoke test asserts only
  the V2 location documented at the time of the change.
- **Secrets can be placed in the dict** → The config file is mode `0600`, but
  values are still stored in plaintext. The README recommends environment
  substitution (`{env:...}`) or a protected file reference over inline secrets.

## Migration Plan

Additive: an empty default renders an empty block and changes no behavior.
Consumers opt in by setting the variable and re-running the playbook; the
existing template-change handler restarts a running service. Rollback is
removing the variable value and re-running, or reverting the commit.
