## 1. Create Command File Structure

- [x] 1.1 Create `files/commands/security_remediation.md` with YAML frontmatter (`description` field), H1 title, Arguments section (no required arguments -- operates on the current repository), and the overall Execution Steps / Guardrails skeleton following the established command pattern from `review_pr.md`.

## 2. Pre-flight Steps

- [x] 2.1 Write Step 0 (Organization Verification): reuse the same `TRUSTED_GITHUB_ORGS` check pattern from `review_pr.md` and `checkout_pr.md`.
- [x] 2.2 Write Step 1 (Token Permission Verification): test access to Dependabot and code scanning alert APIs, fail-fast with clear permission guidance for classic and fine-grained tokens if access is denied.

## 3. Alert Collection

- [x] 3.1 Write Step 2 (Collect Dependabot Alerts): paginated API call to `repos/{owner}/{repo}/dependabot/alerts?state=open`, extract alert number, CVE IDs, severity, package name, ecosystem, vulnerable range, and patched version. Handle "not enabled" gracefully.
- [x] 3.2 Write Step 3 (Collect Code Scanning Alerts): paginated API call to `repos/{owner}/{repo}/code-scanning/alerts?state=open`, extract alert number, rule ID, description, severity, file path, and start line. Handle "not enabled" gracefully.
- [x] 3.3 Write the alert summary display: categorized table showing all collected alerts by type, severity, and package/rule before proceeding to analysis.

## 4. Relationship Analysis

- [x] 4.1 Write Step 4 (Dependency Alert Grouping): analyze Dependabot alerts for same-root-dependency groups, transitive chain resolution, and independent alerts. Output fix groups with group ID, included alerts, and proposed action.
- [x] 4.2 Write Step 5 (Code Scanning Alert Grouping): group code scanning alerts by file and by rule. Output fix groups with group ID, included alerts, and proposed action (code fix or manual intervention flag).

## 5. Remediation Plan

- [x] 5.1 Write Step 6 (Present Remediation Plan): structured display of all fix groups with description, included alerts, proposed action, estimated risk (low/medium/high), and fix type (dependency update vs. code change). Wait for user approval with options: approve all, approve specific groups, reject all.

## 6. Fix Execution

- [x] 6.1 Write Step 7 (Dependency Fix Execution): for each approved dependency fix group, create branch from default branch, apply version bump, detect package manager and regenerate lock files (`go mod tidy`, `poetry lock`, `npm install`, etc.), run local validation tools.
- [x] 6.2 Write Step 8 (Code Scanning Fix Execution): for approved code scanning fix groups, create branch, apply code fixes for trivial cases, flag non-trivial fixes for manual intervention, run local validation tools.
- [x] 6.3 Write Step 9 (Validation and Commit): run local deterministic tools per `review_pr.md` pattern, commit with Conventional Commits format. Handle test failures by flagging for manual intervention.

## 7. PR Proposal

- [x] 7.1 Write Step 10 (Propose PRs): present summary of each branch with draft PR title and body, apply information sensitivity guardrails (no CVE IDs in titles/branch names, link to public advisories only, no exploitation details). Wait for user approval per branch before push and `gh pr create`.

## 8. Summary and Guardrails

- [x] 8.1 Write Step 11 (Final Summary): display total alerts collected, fix groups identified, fixes applied, PRs created, alerts remaining, and groups flagged for manual intervention.
- [x] 8.2 Write the Guardrails section: no remote operations without explicit user approval, no CVE exploitation details in any output, no automatic merging, no secret scanning remediation, scoped branches only.

## 9. Verification

- [x] 9.1 Verify the command file is valid: check YAML frontmatter parses correctly, all steps are numbered and referenced consistently, and guardrails section is present.
- [x] 9.2 Run `ansible-lint` to verify no lint issues are introduced.
