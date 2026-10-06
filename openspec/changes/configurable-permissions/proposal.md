# Proposal

## Why

The permission block in `opencode.json.j2` is the only hardcoded section in an otherwise fully variable-driven template. This prevents users from customizing which bash commands, file reads, edits, and external directory accesses are allowed, asked, or denied. Analysis of 14,617 bash commands across 795 sessions shows that 57% triggered unnecessary confirmation prompts (~10.5 per session), causing significant workflow friction without security benefit. At the same time, truly dangerous commands (sudo, systemctl, kill) are only gated with "ask" rather than hard-denied, and GitHub CLI write operations (pr create, issue comment, etc.) have no explicit rules.

## What Changes

- Introduce `ai_opencode_permissions` variable (default: `{}`) in `defaults/main.yml` for user overrides
- Introduce `_ai_opencode_permissions_default` internal variable in `vars/configure_opencode.yml` containing a comprehensive three-tier permission set:
  - **DENY tier**: System administration commands (sudo, systemctl, kill, dnf, etc.) that no AI agent should run
  - **ASK tier**: Repository write operations (git push/commit, gh pr create/comment/review, gh api mutations, rm) that require human approval
  - **ALLOW tier**: Read-only inspection commands (cat, grep, ls, git log/status/diff, gh view/list) and universal dev tools (openspec, yamllint)
  - **Read permissions**: Deny patterns for secrets (*.env, *.key, *.pem, credentials, SSH keys)
  - **External directory**: Deny system paths (/etc, /usr, /var, /boot, /sys, /proc), allow /tmp
- Template the permission block in `opencode.json.j2` using `_ai_opencode_permissions_default | combine(ai_opencode_permissions, recursive=True)` so user rules overlay on top of defaults
- Remove the previously hardcoded permission block from the template

## Capabilities

### New Capabilities

### Modified Capabilities
- `opencode-configuration`: Adding the permission block as a variable-driven, user-customizable section of the deployed opencode.json, following the same pattern used by providers, agents, plugins, and compaction settings

## Impact

- **Templates**: `templates/opencode.json.j2` -- permission block replaced with variable-driven rendering
- **Variables**: `defaults/main.yml` -- new `ai_opencode_permissions` variable; `vars/configure_opencode.yml` -- new `_ai_opencode_permissions_default` internal variable
- **Existing users**: No breaking change. The default permission set is a superset of the current hardcoded rules (same rules plus additional deny/ask/allow entries), so behavior improves without requiring any playbook changes
- **Tests**: Existing tests for `configure_opencode` task need updating to validate the new variable-driven permission rendering
