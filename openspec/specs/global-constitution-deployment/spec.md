### Requirement: Deploy global coding standards as a baseline instruction file
The role SHALL deploy a `coding-standards.md` file to `~/.config/opencode/` containing organization-agnostic coding principles. The file SHALL be deployed using `ansible.builtin.copy` from `files/coding-standards.md` with mode `0640`. The file SHALL be overwritten on every role execution when the `configure_opencode` task is enabled.

#### Scenario: Coding standards file is deployed
- **WHEN** the `configure_opencode` task is enabled and runs
- **THEN** `coding-standards.md` SHALL be deployed to `~/.config/opencode/coding-standards.md` with mode `0640`

#### Scenario: Coding standards file is updated on subsequent runs
- **WHEN** the role runs and `files/coding-standards.md` has been updated in the role
- **THEN** the deployed `~/.config/opencode/coding-standards.md` SHALL be overwritten with the updated content

### Requirement: Coding standards file contains precedence deferral header
The deployed `coding-standards.md` SHALL begin with a header block stating that these are baseline coding principles applied globally and that repository-level rules (from `constitution.md`, `AGENTS.md`, `CONTRIBUTING.md`, or similar files) take precedence over these defaults when conflicts exist.

#### Scenario: Project-level rules override coding standards defaults
- **WHEN** a repository provides its own `constitution.md` or `AGENTS.md` with coding principles that conflict with the global coding standards
- **THEN** the precedence header SHALL instruct the AI agent to follow the repository-level rules instead

#### Scenario: Coding standards apply in repos without governance files
- **WHEN** the user works in a repository that has no `constitution.md`, `AGENTS.md`, or other coding governance files
- **THEN** the AI agent SHALL follow the coding principles from `~/.config/opencode/coding-standards.md`

### Requirement: Coding standards file contains organization-agnostic core principles
The coding standards file SHALL contain the following core principles, each with a rationale: Single Source of Truth (centralized constants), Simplicity and Isolation, Incremental Improvement, Readability First, Do Not Reinvent the Wheel, Composability (Unix Philosophy), and Convention Over Configuration. The principles SHALL use RFC 2119 language (MUST, SHOULD, MAY) for normative requirements.

#### Scenario: Core principles are present and normative
- **WHEN** examining the deployed `coding-standards.md`
- **THEN** all seven core principles SHALL be present with RFC 2119 normative language and rationale sections

### Requirement: Coding standards file contains all-language coding standards
The coding standards file SHALL include general coding standards applicable to all programming languages, covering: empty line at end of file, pre-commit hooks, Makefile usage, testing requirements, line length limits, and lint configuration awareness.

#### Scenario: All-language standards are present
- **WHEN** examining the deployed `coding-standards.md`
- **THEN** the all-language coding standards section SHALL be present with normative requirements

### Requirement: Coding standards file contains language-specific guidelines
The coding standards file SHALL include coding guidelines for Go, Python, YAML/GitHub Actions, and Containers. Each section SHALL cover language-appropriate conventions for file naming, formatting, licensing headers, and tooling.

#### Scenario: Language-specific sections are present
- **WHEN** examining the deployed `coding-standards.md`
- **THEN** guidelines for Go, Python, YAML/GitHub Actions, and Containers SHALL each be present as distinct sections

### Requirement: Coding standards file contains contribution workflow standards
The coding standards file SHALL include contribution workflow standards covering branching strategy (main branch, feature branches) and pull request requirements (atomic changes, review requirements, CI/CD gates, PR title format).

#### Scenario: Contribution workflow section is present
- **WHEN** examining the deployed `coding-standards.md`
- **THEN** branching strategy and pull request standards SHALL be present

### Requirement: Coding standards file excludes commit standards
The coding standards file SHALL NOT include commit message format or commit trailer requirements. These standards are covered by the separately deployed `commit.md` file to maintain single responsibility and avoid duplication.

#### Scenario: No commit standards duplication
- **WHEN** examining the deployed `coding-standards.md`
- **THEN** there SHALL be no Conventional Commits format specification, no Signed-off-by trailer requirement, and no Assisted-by trailer requirement

### Requirement: Coding standards file excludes organization-specific content
The coding standards file SHALL NOT contain organization-specific branding, repository structure mandates (specific required files or licenses), infrastructure centralization references, governance sections (amendment procedures, compliance review), or references to specific organization repositories.

#### Scenario: No organization-specific content
- **WHEN** examining the deployed `coding-standards.md`
- **THEN** there SHALL be no references to "ComplyTime", "org-infra", Apache License mandates, or organization-specific governance procedures

### Requirement: Coding standards deployment is skipped when task is disabled
The role SHALL skip coding standards deployment when the `configure_opencode` task entry has `enabled: false`.

#### Scenario: Deployment is skipped
- **WHEN** the `configure_opencode` task entry has `enabled: false` in `ai_tasks`
- **THEN** the role SHALL NOT deploy the coding standards file
