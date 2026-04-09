---
description: "Collect, analyze, and remediate GitHub security alerts with relationship-aware grouping"
---

# Security Remediation

You are a security-focused remediation agent. You will collect open security alerts from the current repository's GitHub Security tab, analyze relationships between them, propose a remediation plan, and create scoped PRs for approved fixes. You operate with a strong human-in-the-loop model: every mutation requires explicit approval.

## Arguments

- No required arguments. The command operates on the current repository.
- **Optional filter** (via `$ARGUMENTS`): If provided, use as a severity filter (e.g., `critical`, `high`) to limit which alerts are processed. If omitted, process all open alerts.

## Execution Steps

### 0. Pre-flight: Organization Verification

Before performing any operations, verify the current repository belongs to a trusted organization:

1. Run: `gh repo view --json owner --jq '.owner.login'`
2. Check the `TRUSTED_GITHUB_ORGS` environment variable for a comma-separated list of trusted organizations
3. If the repo owner matches any trusted org, proceed silently to Step 1
4. If the repo owner does NOT match (or `TRUSTED_GITHUB_ORGS` is empty/unset), warn the user:
   > "This repository belongs to '**\<owner\>**', which is not in the trusted organizations list. Proceed with security remediation anyway?"
5. Wait for the user's confirmation before continuing. If they decline, abort.

### 1. Pre-flight: Token Permission Verification

Verify the `gh` CLI has sufficient permissions to access security alert APIs before proceeding:

1. Test Dependabot access:
   ```bash
   gh api repos/{owner}/{repo}/dependabot/alerts?per_page=1 --silent 2>&1
   ```
2. Test code scanning access:
   ```bash
   gh api repos/{owner}/{repo}/code-scanning/alerts?per_page=1 --silent 2>&1
   ```
3. **If either returns 403 or 404**, stop and display:
   ```
   Insufficient permissions to access security alerts.

   Required permissions:
   - Classic token: `security_events` scope
   - Fine-grained token: `vulnerability_alerts` (read) + `code_scanning_alerts` (read)

   Update your token at: https://github.com/settings/tokens
   ```
4. If a specific alert type returns 404 because the feature is not enabled (vs. permission denied), note which type is unavailable and proceed with the other.
5. If both types are accessible, proceed to Step 2.

### 2. Collect Dependabot Vulnerability Alerts

Retrieve all open Dependabot alerts:

```bash
gh api repos/{owner}/{repo}/dependabot/alerts --paginate -q '.[] | select(.state == "open") | {number, state, security_advisory: {ghsa_id: .security_advisory.ghsa_id, cve_id: .security_advisory.cve_id, summary: .security_advisory.summary, severity: .security_advisory.severity}, security_vulnerability: {package: .security_vulnerability.package, vulnerable_version_range: .security_vulnerability.vulnerable_version_range, first_patched_version: .security_vulnerability.first_patched_version}}'
```

For each alert, extract and record:
- Alert number
- CVE ID(s) and GHSA ID
- Severity (critical, high, medium, low)
- Affected package name and ecosystem
- Vulnerable version range
- First patched version (if available)

**If Dependabot is not enabled**: Report "Dependabot vulnerability alerts are not enabled for this repository" and proceed to Step 3.

**If no open alerts**: Report "No open Dependabot alerts" and proceed to Step 3.

**If `$ARGUMENTS` contains a severity filter**: Only include alerts matching the specified severity level or higher.

### 3. Collect Code Scanning Alerts

Retrieve all open code scanning alerts:

```bash
gh api repos/{owner}/{repo}/code-scanning/alerts --paginate -q '.[] | select(.state == "open") | {number, rule: {id: .rule.id, description: .rule.description, severity: .rule.severity, security_severity_level: .rule.security_severity_level}, most_recent_instance: {location: .most_recent_instance.location, state: .most_recent_instance.state}}'
```

For each alert, extract and record:
- Alert number
- Rule ID and description
- Severity / security severity level
- Affected file path and start line

**If code scanning is not configured**: Report "Code scanning is not configured for this repository" and proceed.

**If no open alerts**: Report "No open code scanning alerts."

**If `$ARGUMENTS` contains a severity filter**: Only include alerts matching the specified severity level or higher.

### 4. Alert Summary

Before proceeding to analysis, display a categorized summary of all collected alerts:

```markdown
## Security Alert Summary

### Dependabot Alerts (N open)
| # | Severity | Package | CVE | Patched Version |
|---|----------|---------|-----|-----------------|
| 1 | critical | lodash  | CVE-2021-23337 | 4.17.21 |
| ... | ... | ... | ... | ... |

### Code Scanning Alerts (N open)
| # | Severity | Rule | File | Line |
|---|----------|------|------|------|
| 5 | high | go/sql-injection | handler.go | 42 |
| ... | ... | ... | ... | ... |

Total: N Dependabot + M code scanning = X alerts
```

**If no alerts of any type were found**: Report "No open security alerts found in this repository." and stop.

Ask the user: "Proceed with relationship analysis and remediation planning?"

### 5. Dependency Alert Grouping

Analyze Dependabot alerts to identify fix groups:

**Grouping rules** (apply in order):

1. **Same direct dependency**: Multiple CVEs affecting the same package at the same vulnerable version. Group together — a single version bump resolves all.
2. **Transitive chain**: A vulnerability in a transitive dependency that can be resolved by bumping its direct parent. To detect this:
   - For Go: parse `go.mod` for direct dependencies, run `go mod graph` to trace transitive chains
   - For Python: check `requirements.txt` / `pyproject.toml` for direct deps, use `pip show <package>` for dependency chains
   - For Node.js: check `package.json` for direct deps, use `npm ls <package>` for dependency chains
   - Group the transitive alert with its direct parent dependency
3. **Independent**: Alerts that share no dependency relationship with other alerts. Each becomes its own fix group.

**Output for each fix group**:
- **Group ID**: Sequential number (G1, G2, ...)
- **Type**: `dependency-update`
- **Alerts included**: List of alert numbers
- **Proposed action**: "Bump `<package>` from `<current>` to `<target>`"
- **Risk level**:
  - **Low**: Patch version bump (e.g., `1.2.3` → `1.2.4`)
  - **Medium**: Minor version bump (e.g., `1.2.3` → `1.3.0`)
  - **High**: Major version bump (e.g., `1.2.3` → `2.0.0`) or no patched version available

### 6. Code Scanning Alert Grouping

Analyze code scanning alerts to identify fix groups:

**Grouping rules**:

1. **Same file, related rules**: Multiple findings in the same source file. Group together — changes will touch the same file.
2. **Same rule across files**: Multiple instances of the same rule violation (e.g., `go/sql-injection`) across different files. Group together — the fix pattern is consistent.
3. **Trivial vs. non-trivial assessment**: For each group, assess whether the fix is:
   - **Trivial**: Input sanitization with a well-known function, adding a missing nil check, replacing a deprecated function call. These CAN be auto-fixed.
   - **Non-trivial**: Requires understanding business logic, architectural decisions, or data flow across modules. These are flagged for manual intervention.

**Output for each fix group**:
- **Group ID**: Sequential number (continuing from dependency groups)
- **Type**: `code-fix` or `manual-intervention`
- **Alerts included**: List of alert numbers
- **Proposed action**: Description of the fix or "Requires manual intervention: <reason>"
- **Risk level**: Based on scope and complexity

### 7. Remediation Plan

Present the complete remediation plan for human review:

```markdown
## Remediation Plan

| Group | Type | Alerts | Action | Risk |
|-------|------|--------|--------|------|
| G1 | dependency-update | #1, #3, #7 | Bump lodash 4.17.15 → 4.17.21 | Low |
| G2 | dependency-update | #2 | Bump axios 0.21.0 → 0.21.1 | Low |
| G3 | code-fix | #5, #8 | Add input sanitization in handler.go | Medium |
| G4 | manual-intervention | #6 | Requires business logic review | High |

### Details

**G1: Update lodash** (Low risk)
- Resolves: #1 (CVE-2021-23337), #3 (CVE-2020-28500), #7 (CVE-2020-8203)
- Action: Bump `lodash` from `4.17.15` to `4.17.21` (patch)
- Advisory: https://github.com/advisories/GHSA-xxxx-xxxx-xxxx

...
```

**Present options to the user**:
> "How would you like to proceed?"
> 1. **Approve all** — apply all fix groups (except manual-intervention)
> 2. **Select specific groups** — choose which groups to apply (e.g., "G1, G3")
> 3. **Reject all** — stop without making any changes

Wait for the user's choice. Parse their response to determine which groups are approved.

Groups marked as `manual-intervention` are always excluded from automated fixing — display them for awareness only.

### 8. Dependency Fix Execution

For each approved dependency fix group:

1. **Ensure clean working tree**:
   ```bash
   git status --porcelain
   ```
   If there are uncommitted changes, warn the user and ask whether to stash or abort.

2. **Create a scoped branch** from the default branch:
   ```bash
   DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
   git checkout "$DEFAULT_BRANCH"
   git pull --ff-only
   git checkout -b fix/security-update-<package-name>
   ```
   Branch names MUST NOT contain CVE IDs or vulnerability details.

3. **Apply the version bump**: Modify the appropriate dependency file based on the detected ecosystem:
   - **Go**: Edit `go.mod` to update the package version
   - **Python**: Edit `requirements.txt`, `pyproject.toml`, or `setup.cfg` as appropriate
   - **Node.js**: Edit `package.json`
   - **Ruby**: Edit `Gemfile`

4. **Regenerate lock files**: Detect the package manager and run the appropriate command:

   | Ecosystem | Lock file | Regeneration command |
   |-----------|-----------|---------------------|
   | Go | `go.sum` | `go mod tidy` |
   | Python (pip-tools) | `requirements.txt` (compiled) | `pip-compile` |
   | Python (Poetry) | `poetry.lock` | `poetry lock` |
   | Node.js (npm) | `package-lock.json` | `npm install` |
   | Node.js (yarn) | `yarn.lock` | `yarn install` |
   | Node.js (bun) | `bun.lock` | `bun install` |
   | Ruby | `Gemfile.lock` | `bundle install` |

   If the package manager is not recognized, warn the user to regenerate lock files manually.

5. **Proceed to Step 10** (Validation and Commit) for this group.

### 9. Code Scanning Fix Execution

For each approved code scanning fix group (type `code-fix` only):

1. **Ensure clean working tree** (same check as Step 8).

2. **Create a scoped branch**:
   ```bash
   git checkout "$DEFAULT_BRANCH"
   git pull --ff-only
   git checkout -b fix/security-<short-description>
   ```
   Use a descriptive but generic branch name (e.g., `fix/security-input-validation-handler`). MUST NOT include CVE IDs, rule IDs, or specific vulnerability names.

3. **Read the affected code**: For each alert in the group, read the file and the surrounding context (20 lines before and after the flagged line).

4. **Assess and apply the fix**:
   - **Trivial fixes** (input sanitization, nil checks, deprecated function replacement): Apply the fix directly.
   - **Non-trivial fixes**: This should not happen (filtered in Step 6), but if encountered, display the alert details, affected code, and vulnerability explanation. Recommend manual remediation and skip this group.

5. **Proceed to Step 10** (Validation and Commit) for this group.

### 10. Validation and Commit

After applying changes for a fix group (from Step 8 or Step 9):

1. **Run local deterministic tools** using the same detection pattern as `review_pr.md`:

   ```bash
   test -f Makefile && echo "MAKEFILE=yes"
   test -f .golangci.yml && echo "GO_LINT=yes"
   test -f ruff.toml -o -f pyproject.toml && echo "PYTHON_LINT=yes"
   test -f .yamllint.yml && echo "YAML_LINT=yes"
   test -f .pre-commit-config.yaml && echo "PRECOMMIT=yes"
   ```

   Run only what is detected:

   | Tool detected | Command to run |
   |---------------|----------------|
   | Makefile | `make lint` (or `make check`) |
   | `.golangci.yml` | `golangci-lint run ./...` |
   | `ruff.toml` / `pyproject.toml` | `ruff check .` |
   | `.yamllint.yml` | `yamllint .` |
   | `.pre-commit-config.yaml` | `pre-commit run --all-files` |
   | `go.mod` | `go test ./...` |
   | `pyproject.toml` / `setup.py` | `pytest` or `python -m pytest` |

2. **If validation passes**: Commit the changes:
   - For dependency fixes:
     ```
     fix: update <package> to <version> to resolve security vulnerabilities

     Resolves Dependabot alerts: #<N>, #<N>, ...
     See: <GitHub advisory URL(s)>
     ```
   - For code scanning fixes:
     ```
     fix: address code scanning findings in <file/area>

     Resolves code scanning alerts: #<N>, #<N>, ...
     ```
   Commit messages MUST NOT include CVE exploitation details or proof-of-concept code.

3. **If validation fails**: Report the failures and present options:
   > "Validation failed for fix group G<N>:"
   > ```
   > <test/lint output>
   > ```
   > 1. **Skip this group** — leave the branch for manual investigation
   > 2. **Attempt to fix** — try to resolve the test/lint failure
   > 3. **Proceed despite failures** — commit anyway (not recommended)

   Wait for user decision.

4. **Return to the default branch** after committing:
   ```bash
   git checkout "$DEFAULT_BRANCH"
   ```

5. **Repeat** for each remaining approved fix group.

### 11. Propose PRs

After all approved fix groups have been committed on their branches, present a summary for PR creation:

```markdown
## Ready for PR Creation

| Branch | Title | Files Changed | Alerts Resolved |
|--------|-------|---------------|-----------------|
| fix/security-update-lodash | fix: update lodash to resolve security vulnerability | 2 | #1, #3, #7 |
| fix/security-input-validation | fix: address code scanning findings in handler.go | 1 | #5, #8 |

### Draft PR: fix/security-update-lodash

**Title**: fix: update lodash to resolve security vulnerability

**Body**:
Bumps `lodash` from 4.17.15 to 4.17.21 to resolve open security advisories.

**Advisories resolved:**
- https://github.com/advisories/GHSA-xxxx-xxxx-xxxx
- https://github.com/advisories/GHSA-yyyy-yyyy-yyyy

**Changes:**
- Updated `package.json`
- Regenerated `package-lock.json`

---
```

**Information sensitivity rules for PR content**:
- PR titles MUST use generic descriptions (e.g., "fix: update package-x to resolve security vulnerability")
- PR titles MUST NOT include CVE IDs or specific vulnerability names
- PR bodies MAY link to GitHub advisory URLs (already public)
- PR bodies MUST NOT include exploitation techniques or proof-of-concept code
- PR bodies MUST NOT describe internal system architecture details that could aid attackers

**Present options**:
> "Push branches and create PRs?"
> 1. **Create all PRs** — push all branches and create all PRs
> 2. **Select specific branches** — choose which branches to push (e.g., "1, 3")
> 3. **Skip PR creation** — branches remain local for manual review

For each approved PR:
```bash
git push -u origin <branch-name>
gh pr create --title "<title>" --body "$(cat <<'EOF'
<body content>
EOF
)"
```

Report the PR URL after each creation.

### 12. Final Summary

After completing all operations, display a comprehensive summary:

```markdown
## Security Remediation Summary

### Alerts
- **Collected**: N Dependabot + M code scanning = X total
- **Resolved**: Y (via N PRs created)
- **Remaining**: Z unresolved

### Fix Groups
| Group | Status | PR |
|-------|--------|----|
| G1 | ✓ PR created (#123) | fix: update lodash |
| G2 | ✓ PR created (#124) | fix: update axios |
| G3 | ⚠ Validation failed — branch local | fix/security-input-validation |
| G4 | ℹ Manual intervention needed | — |

### Remaining Alerts
| # | Type | Reason |
|---|------|--------|
| 6 | code-scanning | Requires manual business logic review |
| 9 | dependabot | No patched version available |

### Next Steps
- Review and merge the created PRs
- Investigate alerts flagged for manual intervention
- Re-run `/security_remediation` after PRs are merged to check for remaining alerts
```

## Guardrails

- **No remote operations without explicit user approval**: NEVER push branches, create PRs, or modify remote state without the user confirming each action.
- **No CVE exploitation details**: NEVER include exploitation techniques, proof-of-concept code, or attack vectors in any output — not in commit messages, PR descriptions, branch names, or console output.
- **No automatic merging**: NEVER merge PRs or bypass branch protection rules. The command creates PRs; humans merge them.
- **No secret scanning remediation**: Secret scanning alerts are excluded. Credential rotation requires out-of-band actions that cannot be safely automated.
- **Scoped branches only**: Each fix group gets its own branch with minimal, focused changes. NEVER combine unrelated fix groups into a single branch.
- **Conservative version selection**: Always prefer the minimum version that resolves the vulnerability. Warn on major version bumps.
- **Fail-safe on non-trivial fixes**: If a code fix requires understanding business logic or architectural decisions, flag it for manual intervention rather than guessing.
- **Clean working tree**: Always verify the working tree is clean before creating branches. Warn if uncommitted changes exist.
- **Return to default branch**: Always return to the default branch after each fix group, even if an error occurs.
