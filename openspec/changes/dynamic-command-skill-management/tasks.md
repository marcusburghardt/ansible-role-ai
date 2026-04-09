## 1. Default Variables

- [x] 1.1 Add `ai_opencode_commands_disabled` (default: `[]`) to `defaults/main.yml`
- [x] 1.2 Add `ai_opencode_commands_custom` (default: `[]`) to `defaults/main.yml` with commented examples showing `src` and `name` usage
- [x] 1.3 Add `ai_opencode_skills_disabled` (default: `[]`) to `defaults/main.yml`
- [x] 1.4 Add `ai_opencode_skills_custom` (default: `[]`) to `defaults/main.yml` with commented examples showing `src` and `name` usage
- [x] 1.5 Add `ai_skills_target` (default: `agent-neutral`) to `defaults/main.yml` with a comment explaining the two options
- [x] 1.6 Add `ai_opencode_commands_cleanup` (default: `[]`) and `ai_opencode_skills_cleanup` (default: `[]`) to `defaults/main.yml`
- [x] 1.7 Add `cleanup_opencode` entry to `ai_tasks` list (disabled by default), positioned after `configure_opencode`

## 2. Task-specific Variables

- [x] 2.1 Add `ai_opencode_skills_deploy_dir` derived variable to `vars/configure_opencode.yml` that resolves based on `ai_skills_target` (`~/.agents/skills/` for `agent-neutral`, `{{ ai_opencode_skills_dir }}` for `opencode`)
- [x] 2.2 Create `vars/cleanup_opencode.yml` placeholder file following the existing pattern

## 3. Rewrite Command Deployment in configure_opencode.yml

- [x] 3.1 Replace the hard-coded command loop with an `ansible.builtin.find` task that discovers all `.md` files in `{{ role_path }}/files/commands/` and registers the result
- [x] 3.2 Add a built-in command deployment task that loops over the find results, filtering out entries where `item.path | basename | regex_replace('\.md$','')` is in `ai_opencode_commands_disabled`
- [x] 3.3 Add a custom command deployment task that loops over `ai_opencode_commands_custom` (when non-empty), using `item.src` as the source and `item.name | default(item.src | basename)` as the destination filename

## 4. Add Skill Deployment to configure_opencode.yml

- [x] 4.1 Add an `ansible.builtin.find` task that discovers subdirectories in `{{ role_path }}/files/skills/` (with `file_type: directory`) and registers the result; use `failed_when: false` to handle the case where `files/skills/` does not exist
- [x] 4.2 Add a built-in skill deployment task that loops over the find results, filtering out entries where `item.path | basename` is in `ai_opencode_skills_disabled`, copying each directory to `{{ ai_opencode_skills_deploy_dir }}`
- [x] 4.3 Add a custom skill deployment task that loops over `ai_opencode_skills_custom` (when non-empty), using `item.src` as the source and `item.name | default(item.src | basename)` as the destination directory name in `{{ ai_opencode_skills_deploy_dir }}`

## 5. Create Cleanup Task

- [x] 5.1 Create `tasks/cleanup_opencode.yml` with a command cleanup task that loops over `ai_opencode_commands_cleanup` and removes each named file from `{{ ai_opencode_command_dir }}` using `ansible.builtin.file` with `state: absent`
- [x] 5.2 Add a skill cleanup task to `tasks/cleanup_opencode.yml` that loops over `ai_opencode_skills_cleanup` and removes each named directory from `{{ ai_opencode_skills_deploy_dir }}` using `ansible.builtin.file` with `state: absent`

## 6. Create Built-in Skills Directory

- [x] 6.1 Create the `files/skills/` directory in the role (empty, with a `.gitkeep` to ensure it is tracked) so that the `ansible.builtin.find` task has a valid path to scan

## 7. Validation

- [x] 7.1 Run the role with default variables and verify all three built-in commands (`checkout_pr.md`, `review_pr.md`, `refresh_spec_frameworks.md`) are deployed -- confirming auto-discovery works and the `refresh.md` bug is resolved
- [x] 7.2 Test disabling a built-in command via `ai_opencode_commands_disabled` and verify it is not deployed
- [x] 7.3 Test adding a custom command via `ai_opencode_commands_custom` and verify it is deployed with the correct name
- [x] 7.4 Test the cleanup task by enabling it and providing a command name in `ai_opencode_commands_cleanup`
