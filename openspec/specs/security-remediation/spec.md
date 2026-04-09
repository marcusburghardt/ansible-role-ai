### Requirement: Command file follows the established command format
The command SHALL be deployed as `files/commands/security_remediation.md` with YAML frontmatter containing a `description` field, an H1 title, an Arguments section documenting required and optional parameters, step-by-step Execution Steps, and a Guardrails section constraining agent behavior.

#### Scenario: Command is auto-discovered and deployed
- **WHEN** the Ansible role runs with `configure_opencode` enabled
- **THEN** `security_remediation.md` SHALL be auto-discovered from `files/commands/` and deployed to `{{ ai_opencode_command_dir }}` without any changes to task YAML

#### Scenario: Command can be disabled
- **WHEN** `ai_opencode_commands_disabled` contains `security_remediation`
- **THEN** `security_remediation.md` SHALL NOT be deployed

### Requirement: Pre-flight organization verification
The command SHALL perform the same organization trust verification used by `review_pr.md` and `checkout_pr.md` before performing any operations. The command SHALL check the current repository's owner against the `TRUSTED_GITHUB_ORGS` environment variable and warn the user if the repository belongs to an untrusted organization.

#### Scenario: Trusted organization proceeds silently
- **WHEN** the user runs `/security_remediation` in a repo owned by an org listed in `TRUSTED_GITHUB_ORGS`
- **THEN** the command SHALL proceed without prompting

#### Scenario: Untrusted organization warns and confirms
- **WHEN** the user runs `/security_remediation` in a repo owned by an org NOT in `TRUSTED_GITHUB_ORGS`
- **THEN** the command SHALL warn the user and wait for explicit confirmation before continuing

### Requirement: Pre-flight token permission verification
The command SHALL verify that the `gh` CLI has sufficient permissions to access the repository's security alert APIs before proceeding. If the API returns a 403 or 404, the command SHALL stop and display the exact permissions needed for both classic tokens (`security_events` scope) and fine-grained tokens (`vulnerability_alerts` and `code_scanning_alerts` read permissions).

#### Scenario: Sufficient permissions
- **WHEN** the `gh` CLI can access both Dependabot and code scanning alert endpoints
- **THEN** the command SHALL proceed to alert collection

#### Scenario: Insufficient permissions
- **WHEN** the `gh` CLI returns 403 or 404 for a security alert endpoint
- **THEN** the command SHALL stop with a clear error message listing the required token permissions and instructions for both classic and fine-grained tokens

### Requirement: Collect open Dependabot vulnerability alerts
The command SHALL collect all open Dependabot vulnerability alerts from the current repository using the GitHub API (`gh api repos/{owner}/{repo}/dependabot/alerts --paginate`). For each alert, the command SHALL extract: alert number, state, CVE ID(s), severity, affected package name and ecosystem, vulnerable version range, and patched version (if available).

#### Scenario: Repository has open Dependabot alerts
- **WHEN** the repository has 5 open Dependabot alerts
- **THEN** the command SHALL collect all 5 alerts with their CVE IDs, severity, affected packages, and patched versions

#### Scenario: Repository has no Dependabot alerts
- **WHEN** the repository has no open Dependabot alerts
- **THEN** the command SHALL report "No open Dependabot alerts" and proceed to code scanning collection

#### Scenario: Dependabot is not enabled
- **WHEN** Dependabot vulnerability alerts are not enabled for the repository
- **THEN** the command SHALL report that Dependabot is not enabled and proceed to code scanning collection

### Requirement: Collect open code scanning alerts
The command SHALL collect all open code scanning alerts from the current repository using the GitHub API (`gh api repos/{owner}/{repo}/code-scanning/alerts --paginate`). For each alert, the command SHALL extract: alert number, rule ID, rule description, severity, affected file path, start line, and state.

#### Scenario: Repository has open code scanning alerts
- **WHEN** the repository has 3 open code scanning alerts
- **THEN** the command SHALL collect all 3 alerts with their rule IDs, severity, affected files, and line numbers

#### Scenario: Repository has no code scanning alerts
- **WHEN** the repository has no open code scanning alerts
- **THEN** the command SHALL report "No open code scanning alerts"

#### Scenario: Code scanning is not enabled
- **WHEN** code scanning is not configured for the repository
- **THEN** the command SHALL report that code scanning is not enabled

### Requirement: Analyze relationships between vulnerability alerts
The command SHALL analyze relationships between collected Dependabot alerts to identify groupings. The analysis SHALL detect: alerts sharing the same direct dependency (one version bump resolves multiple CVEs), alerts in transitive dependencies resolvable by bumping a parent package, and alerts with no relationship to others (independent fixes).

#### Scenario: Multiple CVEs in same direct dependency
- **WHEN** 3 Dependabot alerts affect the same direct dependency `package-x` at different CVE IDs
- **THEN** the command SHALL group all 3 alerts into a single fix group with a single version bump to the minimum patched version that resolves all 3

#### Scenario: Transitive dependency resolvable by parent bump
- **WHEN** a Dependabot alert affects transitive dependency `sub-package` which is pulled in by direct dependency `parent-package`
- **THEN** the command SHALL check if bumping `parent-package` to a version that pulls a fixed `sub-package` resolves the alert, and if so, group them together

#### Scenario: Independent alerts
- **WHEN** alerts affect unrelated dependencies with no shared fix path
- **THEN** the command SHALL treat each as an independent fix group

### Requirement: Analyze relationships between code scanning alerts
The command SHALL group code scanning alerts by file (multiple findings in the same source file) and by rule (multiple instances of the same rule violation across files). Each group SHALL be treated as a candidate fix group.

#### Scenario: Multiple findings in same file
- **WHEN** 3 code scanning alerts are in the same file `src/handler.go`
- **THEN** the command SHALL group them into a single fix group for that file

#### Scenario: Same rule across multiple files
- **WHEN** 4 code scanning alerts share rule ID `go/sql-injection` across different files
- **THEN** the command SHALL group them by rule into a single fix group

### Requirement: Present remediation plan for human review
The command SHALL present a structured remediation plan before taking any action. The plan SHALL list each fix group with: group description, alerts included (by number and CVE/rule), proposed action (version bump target or code change description), estimated risk level (low/medium/high based on change scope), and whether the fix is a dependency update or a code change.

#### Scenario: Plan is presented before any mutation
- **WHEN** the command has completed alert collection and relationship analysis
- **THEN** the command SHALL display the full remediation plan and wait for user approval before proceeding to any branch creation or code changes

#### Scenario: User can select which fix groups to apply
- **WHEN** the remediation plan contains 4 fix groups
- **THEN** the user SHALL be able to approve all, approve specific groups by number, or reject all

### Requirement: Conservative dependency version selection
For dependency updates, the command SHALL prefer the minimum version that resolves the vulnerability. The command SHALL prefer patch-level bumps over minor bumps, and minor bumps over major bumps. For major version bumps, the command SHALL warn the user about potential breaking changes and check the dependency's changelog for breaking change indicators when accessible.

#### Scenario: Patch-level fix available
- **WHEN** package `example` is at version `1.2.3` with a vulnerability and `1.2.4` is the patched version
- **THEN** the command SHALL propose bumping to `1.2.4`

#### Scenario: Only major version fix available
- **WHEN** package `example` is at version `1.2.3` and the only patched version is `2.0.0`
- **THEN** the command SHALL warn the user about potential breaking changes and present the major version bump as a high-risk fix group

#### Scenario: No patched version available
- **WHEN** a Dependabot alert has no patched version available
- **THEN** the command SHALL flag the alert as requiring manual intervention and suggest alternatives (e.g., finding a replacement package or applying a workaround)

### Requirement: Create scoped fix branches per independent fix group
For each approved fix group, the command SHALL create a branch from the repository's default branch with naming convention `fix/security-<short-description>`. Each branch SHALL contain only the changes for its fix group. The command SHALL NOT create branches without explicit user approval.

#### Scenario: Branch created for dependency fix group
- **WHEN** the user approves a fix group that bumps `package-x` from `1.2.3` to `1.2.4`
- **THEN** the command SHALL create branch `fix/security-update-package-x` from the default branch with the version bump changes

#### Scenario: Branch created for code scanning fix group
- **WHEN** the user approves a fix group for SQL injection findings in `handler.go`
- **THEN** the command SHALL create branch `fix/security-sql-injection-handler` from the default branch with the code fixes

#### Scenario: Branch names exclude CVE identifiers
- **WHEN** creating a branch for any fix group
- **THEN** the branch name SHALL NOT contain CVE IDs or specific vulnerability identifiers

### Requirement: Regenerate lock files after dependency version bumps
After modifying dependency version files, the command SHALL detect the project's package manager and regenerate the appropriate lock files. The command SHALL support at minimum: `go mod tidy` for Go, `pip-compile` or `poetry lock` for Python, `npm install` for Node.js, and `bundle install` for Ruby.

#### Scenario: Go module lock file regeneration
- **WHEN** a Go dependency is bumped in `go.mod`
- **THEN** the command SHALL run `go mod tidy` to regenerate `go.sum`

#### Scenario: Python lock file regeneration
- **WHEN** a Python dependency is bumped and `poetry.lock` exists
- **THEN** the command SHALL run `poetry lock` to regenerate the lock file

#### Scenario: Unknown package manager
- **WHEN** the project uses a package manager the command does not recognize
- **THEN** the command SHALL warn the user to manually regenerate lock files

### Requirement: Validate fixes with local deterministic tools
After applying each fix group's changes, the command SHALL run the same local tool detection and execution pattern used by `review_pr.md` (checking for `Makefile`, `.golangci.yml`, `ruff.toml`, `.pre-commit-config.yaml`, etc.) to validate the fix does not introduce regressions. If tests fail, the fix group SHALL be flagged for manual intervention.

#### Scenario: Local tests pass after fix
- **WHEN** a fix group's changes are applied and local tools (lint, test) pass
- **THEN** the command SHALL mark the fix group as validated and proceed to commit

#### Scenario: Local tests fail after fix
- **WHEN** a fix group's changes are applied and local tests fail
- **THEN** the command SHALL report the test failures, flag the fix group for manual intervention, and ask the user whether to skip this group, attempt a different fix approach, or proceed despite failures

### Requirement: Commit changes with Conventional Commits format
Each fix group's changes SHALL be committed with a Conventional Commits message. The commit message SHALL use the `fix` type, reference the alert numbers being resolved, and include a brief description of what was fixed. The commit message SHALL NOT include CVE exploitation details.

#### Scenario: Dependency fix commit
- **WHEN** committing a dependency version bump that resolves alerts #12, #15, and #18
- **THEN** the commit message SHALL follow the format `fix: update package-x to <version> to resolve security vulnerabilities` with a body referencing the alert numbers

#### Scenario: Code scanning fix commit
- **WHEN** committing a code scanning fix for SQL injection findings
- **THEN** the commit message SHALL follow the format `fix: address code scanning findings in <file/area>` without exposing specific exploitation techniques

### Requirement: Information sensitivity guardrails for PR content
The command SHALL ensure that PR titles, descriptions, branch names, and commit messages do not expose vulnerability details beyond what is already public in the GitHub advisory. PR descriptions SHALL link to the relevant GitHub advisory URLs (which are public) but SHALL NOT include exploitation techniques, proof-of-concept code, or internal system architecture details.

#### Scenario: PR description references public advisory
- **WHEN** creating a PR for a fix that resolves CVE-2024-12345
- **THEN** the PR description SHALL link to the GitHub advisory URL but SHALL NOT include exploitation steps or proof-of-concept code

#### Scenario: PR title uses generic description
- **WHEN** creating a PR title for a security fix
- **THEN** the title SHALL use a generic description like `fix: update package-x to resolve security vulnerability` rather than `fix: patch CVE-2024-12345 remote code execution in package-x`

### Requirement: Propose PR creation with human approval
After all approved fix groups are committed on their respective branches, the command SHALL present a summary of each branch with: branch name, commit summary, files changed, and a draft PR title and body. The command SHALL wait for explicit user approval before pushing branches or creating PRs. The user SHALL be able to approve all, approve specific branches, or reject all.

#### Scenario: User approves all PRs
- **WHEN** the user approves all 3 proposed PRs
- **THEN** the command SHALL push each branch and create each PR using `gh pr create`

#### Scenario: User approves subset of PRs
- **WHEN** the user approves PR 1 and 3 but rejects PR 2
- **THEN** the command SHALL push and create PRs only for branches 1 and 3, leaving branch 2 local

#### Scenario: User rejects all PRs
- **WHEN** the user rejects all proposed PRs
- **THEN** the command SHALL NOT push any branches or create any PRs, but SHALL inform the user that the local branches remain for manual review

### Requirement: Command handles non-trivial code fixes gracefully
For code scanning alerts that require non-trivial fixes (business logic changes, architectural modifications), the command SHALL present the alert details and affected code but SHALL NOT attempt an automated fix. Instead, it SHALL recommend manual intervention and provide context for the developer.

#### Scenario: Non-trivial code scanning fix
- **WHEN** a code scanning alert requires understanding business logic to fix (e.g., determining which inputs are trusted)
- **THEN** the command SHALL display the alert, show the affected code, explain the vulnerability, and recommend manual remediation rather than proposing an automated fix

#### Scenario: Trivial code scanning fix
- **WHEN** a code scanning alert has a straightforward fix (e.g., adding input sanitization with a well-known function)
- **THEN** the command SHALL propose the fix and include it in the remediation plan

### Requirement: Final summary after execution
After completing all operations (or after the user stops the workflow), the command SHALL display a summary showing: total alerts collected, fix groups identified, fixes applied, PRs created, alerts remaining unresolved, and any groups flagged for manual intervention.

#### Scenario: All fixes applied successfully
- **WHEN** 10 alerts were collected, grouped into 4 fix groups, all approved and validated
- **THEN** the summary SHALL show 10 alerts collected, 4 PRs created, 0 remaining

#### Scenario: Partial completion
- **WHEN** 10 alerts were collected, 4 fix groups identified, 2 approved, 1 failed validation, 1 rejected
- **THEN** the summary SHALL show 10 alerts collected, 2 PRs created, alerts from the failed and rejected groups listed as remaining
