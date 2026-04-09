### Requirement: Auto-discover built-in skills from role files directory
The role SHALL auto-discover all subdirectories in the role's `files/skills/` directory using `ansible.builtin.find` (with `file_type: directory`) and register the results for deployment. Each discovered directory SHALL be copied recursively to the resolved skills deploy directory. If `files/skills/` does not exist or is empty, no built-in skills SHALL be deployed and no error SHALL occur.

#### Scenario: Built-in skills directory is empty
- **WHEN** `files/skills/` exists but contains no subdirectories
- **THEN** no built-in skills SHALL be deployed and the task SHALL not fail

#### Scenario: Built-in skills directory does not exist
- **WHEN** `files/skills/` does not exist in the role
- **THEN** the discovery task SHALL not fail and no built-in skills SHALL be deployed

#### Scenario: Built-in skill is discovered and deployed
- **WHEN** `files/skills/` contains a subdirectory `code-review/` with a `SKILL.md` file
- **THEN** the entire `code-review/` directory SHALL be copied to the skills deploy directory as `code-review/SKILL.md`

### Requirement: Filter built-in skills against a blocklist
The role SHALL provide a variable `ai_opencode_skills_disabled` (default: empty list) that accepts skill directory names. Any discovered built-in skill whose directory name matches an entry in this list SHALL be skipped during deployment.

#### Scenario: No skills disabled (default)
- **WHEN** `ai_opencode_skills_disabled` is empty (default)
- **THEN** all discovered built-in skills SHALL be deployed

#### Scenario: Specific skill disabled
- **WHEN** `ai_opencode_skills_disabled` contains `code-review` and `files/skills/` contains `code-review/` and `deploy-check/`
- **THEN** only `deploy-check/` SHALL be deployed

### Requirement: Deploy custom skills from user-specified local paths
The role SHALL provide a variable `ai_opencode_skills_custom` (default: empty list) that accepts a list of dictionaries. Each dictionary SHALL have a required `src` key (path to the skill directory, relative to the playbook or absolute) and an optional `name` key (override for the deployed directory name). If `name` is omitted, the basename of `src` SHALL be used. Custom skills SHALL be deployed after built-in skills.

#### Scenario: No custom skills (default)
- **WHEN** `ai_opencode_skills_custom` is empty (default)
- **THEN** only built-in skills (if any) are deployed

#### Scenario: Custom skill with default name
- **WHEN** `ai_opencode_skills_custom` contains `{ src: ../shared-skills/deploy-workflow }`
- **THEN** the directory SHALL be recursively copied to `{{ ai_opencode_skills_deploy_dir }}/deploy-workflow/`

#### Scenario: Custom skill with name override
- **WHEN** `ai_opencode_skills_custom` contains `{ src: /opt/team/review-skill, name: team-review }`
- **THEN** the directory SHALL be recursively copied to `{{ ai_opencode_skills_deploy_dir }}/team-review/`

### Requirement: Configurable skills deployment target directory
The role SHALL provide a variable `ai_skills_target` (default: `agent-neutral`) that determines where skills are deployed. When set to `agent-neutral`, skills SHALL be deployed to `{{ ai_user_home_dir }}/.agents/skills/`. When set to `opencode`, skills SHALL be deployed to `{{ ai_opencode_skills_dir }}` (`~/.config/opencode/skills/`). A derived variable `ai_opencode_skills_deploy_dir` SHALL resolve the actual path based on this setting.

#### Scenario: Default target is agent-neutral
- **WHEN** `ai_skills_target` is `agent-neutral` (default)
- **THEN** skills SHALL be deployed to `{{ ai_user_home_dir }}/.agents/skills/`

#### Scenario: Target is OpenCode-specific
- **WHEN** `ai_skills_target` is `opencode`
- **THEN** skills SHALL be deployed to `{{ ai_opencode_skills_dir }}`

#### Scenario: Both skills directories are always created
- **WHEN** `configure_opencode` task runs regardless of `ai_skills_target` value
- **THEN** both `{{ ai_opencode_skills_dir }}` and `{{ ai_user_home_dir }}/.agents/skills/` directories SHALL exist (existing behavior preserved)
