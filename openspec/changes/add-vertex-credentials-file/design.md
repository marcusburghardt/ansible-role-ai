# Design

## Context

See proposal.md - Why. The role already renders the launcher script and the
service-restart handler from the single `ai_opencode_server_env` dict so both launch
paths share one environment. The `google-vertex` provider is configured through
`ai_opencode_providers` with `settings.project` and `settings.location`; authentication
currently relies on ambient Application Default Credentials. Two constraints shape this
change: the service-account key lives in a protected directory the playbook must never
read (only its path may be rendered), and the restart handler can fire when
`configure_opencode` is disabled (an installation change also notifies it), so any
variable the handler references must be defined regardless of which tasks are enabled.

## Goals / Non-Goals

**Goals:**
- Make key-based Vertex credentials flow to both launch paths through the existing
  shared-environment mechanism
- Preserve the `ai_enmaas_key_file` contract: path-only rendering, tilde expansion,
  empty preserves the environment

**Non-Goals:**
- Reading, validating, or deploying the key file itself (the Google auth library
  consumes it at runtime)
- Changing `ai_opencode_server_env` semantics for consumers
- Model catalog changes under `google-vertex`; consumers pin models through
  `ai_opencode_providers`

## Decisions

### Merge in `vars/main.yml`, not `vars/configure_opencode.yml`
`_ai_vertex_credentials_expanded` and `_ai_opencode_server_env_merged` live in
`vars/main.yml`, which Ansible loads for every role run. The restart handler
references the merged dict and can be notified by `install_opencode` alone, when
`vars/configure_opencode.yml` is never included. Placing the computation in the
task-specific vars file would leave the handler with an undefined variable in that
scenario. Alternative considered: a `| default(...)` fallback in the handler — rejected
because it hides the dependency instead of guaranteeing it.

### Injection by `combine` instead of a playbook dict override
The merged dict is `ai_opencode_server_env | combine({'GOOGLE_APPLICATION_CREDENTIALS': ...})`
when the credentials file is set, otherwise `ai_opencode_server_env` unchanged. This
follows the `_ai_opencode_permissions_merged` precedent (computed internal var,
consumer overrides preserved) and avoids asking consumers to re-declare
`TRUSTED_GITHUB_ORGS` just to add one variable. Alternative considered: documenting a
playbook-level override of `ai_opencode_server_env` — rejected because it duplicates
role defaults in every consumer and diverges when the role evolves.

### Export a path, not the key
`GOOGLE_APPLICATION_CREDENTIALS` takes a file path that the Google auth library reads
itself, unlike the EnMaaS key which the launcher must read into an environment value.
The launcher therefore only shell-quotes and exports the expanded path; no runtime read
or existence check is added to the wrapper, keeping it thin. Alternative considered:
an EnMaaS-style runtime read — rejected because it would embed key material in the
environment.

## Risks / Trade-offs

- [Merged var shadowing if a consumer defines `_ai_opencode_server_env_merged`]
  → Internal names are underscore-prefixed and undocumented for override; the same
  convention already protects `_ai_opencode_permissions_merged`.
- [A service started outside the launcher and the role misses the credentials]
  → Inherent to the existing shared-service design (same exposure as
  `TRUSTED_GITHUB_ORGS`); documented in the README as "start via the launcher or let
  the role restart the service".
- [Handler runs when the key file is missing on the target host]
  → The role never reads the file, so deployment succeeds; Vertex requests fail at
  authentication time with the library's own error, which names the path.

## Migration Plan

Deploy by setting `ai_vertex_credentials_file` in a consumer playbook and placing the
key file on the target host. Roll back by clearing the variable: the merged dict
degrades to `ai_opencode_server_env` and no `GOOGLE_APPLICATION_CREDENTIALS` export is
rendered.
