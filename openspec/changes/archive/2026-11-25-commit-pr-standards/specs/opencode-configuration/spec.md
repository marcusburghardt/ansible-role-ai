# Spec Delta

## ADDED Requirements

### Requirement: Deploy commit standards as a global baseline instruction file
The role SHALL deploy `commit.md` to `~/.config/opencode/` with the Conventional
Commits format, the standard type set, subject and body length limits,
`Signed-off-by`, and `Assisted-by` requirements. The file SHALL state that
repository rules may add stricter requirements or explicitly waive a specific
rule, but that repository silence does not opt out of the baseline. The file
SHALL be listed first in `ai_opencode_instructions`.

#### Scenario: Baseline cannot be weakened by silence
- **WHEN** a repository has an instruction file that defines Conventional
  Commit types but says nothing about line length or trailers
- **THEN** an agent SHALL still apply the baseline line-length and trailer rules

#### Scenario: Repository adds a stricter rule
- **WHEN** a repository requires a shorter subject limit or an additional trailer
- **THEN** the agent SHALL satisfy both the repository rule and the baseline

#### Scenario: Repository explicitly waives a rule
- **WHEN** a repository explicitly documents an exception to a specific baseline
  rule
- **THEN** the agent MAY follow the documented exception for that rule only

### Requirement: Deploy PR standards as a global baseline instruction file
The role SHALL deploy `pr.md` to `~/.config/opencode/` with the following
requirements: Conventional Commit PR titles using the types defined in
`commit.md`, a complete title at or below 72 characters, no trailing period,
imperative mood, required PR-template discovery, and a fallback body structure
when no template exists. The file SHALL be included in the default
`ai_opencode_instructions` list.

#### Scenario: PR title uses Conventional Commits
- **WHEN** an agent creates a pull request
- **THEN** the title SHALL match `<type>(<scope>)!: <description>` and use one
  of the documented types

#### Scenario: PR title length is bounded
- **WHEN** a generated PR title exceeds 72 characters
- **THEN** the agent SHALL shorten it before creating the pull request

#### Scenario: Repository template is used
- **WHEN** the repository contains `.github/pull_request_template.md`,
  `.github/PULL_REQUEST_TEMPLATE.md`, or a `PULL_REQUEST_TEMPLATE/` directory
- **THEN** the PR body SHALL follow that template instead of a custom format

### Requirement: Default instructions include commit and PR standards
The default `ai_opencode_instructions` list SHALL include
`~/.config/opencode/commit.md` first, followed immediately by
`~/.config/opencode/pr.md`, before the remaining global and repository-relative
instruction files.

#### Scenario: PR standards load by default
- **WHEN** the role deploys with default instructions
- **THEN** `~/.config/opencode/pr.md` SHALL appear immediately after
  `~/.config/opencode/commit.md`
