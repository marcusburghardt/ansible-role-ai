# Tasks

## 1. Add permission default variables

- [x] 1.1 Add `_ai_opencode_permissions_default` to `vars/configure_opencode.yml` with the full three-tier permission rule set (bash allow/ask/deny, read deny patterns, edit allow, external_directory deny/allow). Organize by tier with comments. Verify by running `ansible -m debug -a "var=_ai_opencode_permissions_default" localhost` with the role loaded and confirming all expected keys are present.
- [x] 1.2 Add `ai_opencode_permissions` variable to `defaults/main.yml` with default value `{}` and a descriptive comment explaining the merge behavior. Verify the variable appears in `ansible -m debug -a "var=ai_opencode_permissions"` output as an empty dict.
- [x] 1.3 Add `_ai_opencode_permissions_merged` computed variable to `vars/configure_opencode.yml` that combines `_ai_opencode_permissions_default` with `ai_opencode_permissions` using `combine(recursive=True)`. Verify by temporarily overriding `ai_opencode_permissions` with `{bash: {"test_cmd *": "allow"}}` and confirming the merged output contains both default rules and the test override.

## 2. Update the template

- [x] 2.1 Replace the hardcoded `"permission": { ... }` block in `templates/opencode.json.j2` (lines 12-63) with `"permission": {{ _ai_opencode_permissions_merged | to_nice_json(indent=6) }}`. Verify by running the role and checking the deployed `opencode.json` contains all default permission rules from the new variable.
- [x] 2.2 Verify the deployed `opencode.json` is valid JSON and that OpenCode starts without errors by running `opencode --version` or loading the config. Confirm the permission block matches the expected merged output.

## 3. Verify merge behavior

- [x] 3.1 Test that an empty `ai_opencode_permissions` override produces a permission block identical to `_ai_opencode_permissions_default` by running the role with no overrides and comparing the deployed JSON permission block against the default variable content.
- [x] 3.2 Test user override adds new rules by setting `ai_opencode_permissions: {bash: {"poetry *": "allow"}, external_directory: {"~/GIT/**": "allow"}}` in the playbook, running the role, and confirming the deployed JSON contains both default rules and the new entries.
- [x] 3.3 Test user override replaces a default rule by setting `ai_opencode_permissions: {bash: {"rm *": "deny"}}` in the playbook, running the role, and confirming `rm *` is `deny` in the deployed JSON while all other defaults remain unchanged.
- [x] 3.4 Run `ansible-lint` on the role and verify zero lint issues related to the changed files.
