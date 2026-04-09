## Why

Maintainers of multiple GitHub repositories face a growing volume of security alerts across Dependabot vulnerability alerts, code scanning findings, and secret scanning notifications. Triaging and remediating these alerts manually is time-consuming and error-prone: vulnerabilities are often interrelated (e.g., a transitive dependency fix that resolves multiple CVEs), fixes can break CI or introduce regressions if dependency versions aren't carefully validated, and remediation PRs can inadvertently expose sensitive information. There is no built-in tooling that analyzes these relationships, batches related fixes, and produces scoped, CI-aware PRs with security-conscious content.

## What Changes

- Add a new `security_remediation.md` command to `files/commands/` that instructs OpenCode to:
  - Collect and categorize all open security alerts from GitHub's Security tab (Dependabot vulnerability alerts and code scanning alerts) for the current repository
  - Analyze relationships between alerts (shared root dependency, overlapping fix paths, same CVE across transitive chains)
  - Produce a remediation plan that groups related fixes and identifies independent fixes
  - For each independent fix group, create a scoped branch and commit with minimal, focused changes
  - Validate fixes against CI by running local deterministic tools before proposing the PR
  - Apply security guardrails: ensure PR descriptions, branch names, and commit messages do not expose vulnerability details beyond what is already public in the advisory
  - Present the full plan and each PR for human review before any remote operations (push, PR creation)

## Capabilities

### New Capabilities
- `security-remediation`: The command for collecting, analyzing, and remediating GitHub security alerts with relationship-aware grouping, scoped PR creation, CI validation, and information-sensitivity guardrails

### Modified Capabilities

## Impact

- **Files added**: `files/commands/security_remediation.md` (new command file, auto-discovered by existing command deployment mechanism)
- **No task/defaults changes needed**: The command-autodiscovery system (`files/commands/*.md` auto-discovery) deploys new commands automatically
- **Dependencies**: Requires `gh` CLI with access to the repository's security alerts (the `security_events` scope or appropriate fine-grained token permissions)
- **Existing commands unaffected**: No modifications to `review_pr.md`, `checkout_pr.md`, or `refresh_spec_frameworks.md`
