# Design

## Context

See proposal.md for motivation. The permission block in `templates/opencode.json.j2` (lines 12-63) is the only section not driven by Ansible variables. Every other configurable block (providers, agents, plugins, compaction, instructions) follows the same pattern: a variable in `defaults/main.yml` rendered via `to_json` in the template. Permissions need a merge strategy because there are security-critical defaults the role should enforce, unlike providers or plugins where empty defaults are acceptable.

## Goals / Non-Goals

**Goals:**
- Make the permission block variable-driven, following established role patterns
- Ship a comprehensive three-tier default (deny/ask/allow) based on analysis of real usage data
- Allow users to add, override, or escalate individual permission rules from their playbooks without replacing the entire default set
- Maintain backward compatibility: default behavior is a superset of the current hardcoded rules

**Non-Goals:**
- Per-agent permissions (OpenCode supports this, but it is out of scope for this change)
- Adding permissions for non-bash tools beyond what already exists (glob, grep, task, webfetch, etc.)
- Terminal multiplexer installation or configuration (separate concern, separate role)

## Decisions

### Decision 1: Merge strategy using `combine(recursive=True)`

**Chosen**: Two-variable approach with Ansible's `combine` filter.
- `_ai_opencode_permissions_default` (internal, in `vars/configure_opencode.yml`) -- comprehensive defaults
- `ai_opencode_permissions` (user-facing, in `defaults/main.yml`, default: `{}`) -- user overrides

Template renders: `_ai_opencode_permissions_default | combine(ai_opencode_permissions, recursive=True) | to_nice_json`

**Why**: This mirrors how other Ansible roles handle defaults-with-overrides. The `combine(recursive=True)` merges nested dicts (bash, read, external_directory sub-sections) so users can add keys to any sub-section without losing the rest. The `_` prefix on the internal variable follows Ansible convention for private/internal variables.

**Alternative considered**: Single `ai_opencode_permissions` variable with all defaults in `defaults/main.yml`. Rejected because users who override this variable would lose all defaults unless they manually included them. The merge approach lets users specify only their deltas.

**Alternative considered**: Separate variables per sub-section (`ai_opencode_permissions_bash`, `ai_opencode_permissions_read`, etc.). Rejected because it fragments the configuration and doesn't match the JSON structure. A single dict matching the OpenCode schema is more intuitive.

### Decision 2: Permission content organized by intent, not alphabetically

**Chosen**: Within each sub-section (bash, read, external_directory), rules are grouped by security tier: allow first, then ask, then deny. Within each tier, rules are alphabetically sorted.

**Why**: This makes the YAML readable when reviewing defaults. A maintainer scanning the file can quickly see the intent of each tier. OpenCode evaluates rules by "last matching rule wins" ordering, so the deny rules being last means they override any allow/ask for the same pattern.

**Risk**: If a user adds an "allow" rule for a pattern that the defaults "deny" via the merge, the user's rule appears alongside the default deny. Since `combine` merges at the key level, the user's key either adds a new pattern or replaces the default's value for that exact key. A user cannot accidentally override `"sudo *": "deny"` unless they explicitly write `"sudo *": "allow"` in their override dict -- which is an intentional action.

### Decision 3: Template renders the entire merged permission block as JSON

**Chosen**: Replace the hardcoded permission JSON in `opencode.json.j2` with `{{ _ai_opencode_permissions_merged | to_nice_json(indent=6) }}` where `_ai_opencode_permissions_merged` is computed in the template using a `set` statement or in vars.

**Implementation detail**: Since Jinja2 in Ansible templates supports `{% set %}`, the merge can be done inline in the template:
```jinja2
{% set _perms = _ai_opencode_permissions_default | combine(ai_opencode_permissions, recursive=True) %}
    "permission": {{ _perms | to_nice_json(indent=6) }},
```

Alternatively, compute the merged variable in `vars/configure_opencode.yml`:
```yaml
_ai_opencode_permissions_merged: >-
  {{ _ai_opencode_permissions_default
     | combine(ai_opencode_permissions, recursive=True) }}
```

**Preferred**: Compute in vars file. This keeps the template simple and makes the merged value available for potential use in other tasks (e.g., validation).

### Decision 4: Default deny list scope

**Chosen**: Deny system administration commands that no AI coding agent should run (sudo, systemctl, kill, dnf, etc.). The deny list is intentionally broad for system commands.

**Why**: These commands modify system state, can cause data loss, or escalate privileges. Even in `--auto` mode (where "ask" rules are auto-approved), "deny" rules remain enforced. The deny tier is the hard safety floor.

**Trade-off**: Some users might want `dnf list` or `dnf info` (read-only package queries). They can override specific patterns in their playbook: `{bash: {"dnf list *": "allow", "dnf info *": "allow"}}`. The default errs on the side of safety.

## Risks / Trade-offs

- **[JSON key ordering]** OpenCode uses "last matching rule wins." Python 3.7+ dicts preserve insertion order, and Ansible's `to_nice_json` respects this. However, `combine(recursive=True)` places merged keys after existing keys, which is the correct behavior (user overrides win). Verified with Ansible 2.14+. **Mitigation**: Document in the variable comment that user rules overlay on defaults.

- **[Breaking change risk]** Minimal. The default permission set is a superset of the current hardcoded rules (same rules plus additional deny/ask/allow entries). Users who had the old hardcoded config get strictly more rules, not fewer. The only difference is that commands previously falling through to `"*": "ask"` are now explicitly classified as allow, ask, or deny.

- **[Large internal variable]** `_ai_opencode_permissions_default` will be a substantial YAML block (~90 keys across 4 sub-sections). **Mitigation**: Well-commented with tier headers, alphabetically sorted within tiers.
