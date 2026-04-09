## Context

The Ansible role deploys OpenCode commands as `.md` files to `~/.config/opencode/command/`. Commands are auto-discovered from `files/commands/` and follow a consistent pattern: YAML frontmatter with a `description`, an H1 title, `$ARGUMENTS` for user input, step-by-step prose instructions, and guardrails constraining agent behavior. Existing commands like `review_pr.md` (341 lines) demonstrate that complex, multi-phase workflows work well in this format.

GitHub exposes security alerts through the `gh` CLI and API:
- **Dependabot alerts**: `gh api repos/{owner}/{repo}/dependabot/alerts` -- vulnerability alerts for dependencies with CVE data, severity, affected package, and suggested fix versions
- **Code scanning alerts**: `gh api repos/{owner}/{repo}/code-scanning/alerts` -- static analysis findings from CodeQL or third-party scanners with rule IDs, locations, and severity
- **Secret scanning alerts**: `gh api repos/{owner}/{repo}/secret-scanning/alerts` -- exposed credentials and tokens

The `gh` CLI requires appropriate token permissions (`security_events` scope for classic tokens, or `vulnerability_alerts` + `code_scanning_alerts` read permissions for fine-grained tokens).

## Goals / Non-Goals

**Goals:**
- Provide a single command that collects, analyzes, and proposes remediation for open security alerts in the current repository
- Group related vulnerabilities (shared root dependency, same CVE across transitive chains) to produce batch fixes instead of one-per-alert PRs
- Create scoped branches and commits per independent fix group, each with minimal focused changes
- Validate fixes locally (run CI-equivalent tools) before proposing PR creation
- Ensure PR content does not disclose vulnerability exploitation details beyond what is already in the public advisory
- Maintain human-in-the-loop: every remote operation (push, PR creation) requires explicit user approval

**Non-Goals:**
- Cross-repository remediation in a single command invocation (each run targets the current repo)
- Secret scanning remediation (credential rotation requires out-of-band actions that cannot be safely automated)
- Automatic merging of PRs or bypassing branch protection rules
- Replacing Dependabot's auto-PR feature (this command handles the cases where Dependabot PRs are not sufficient -- e.g., major version bumps, code-scanning fixes, multi-dependency coordination)
- Support for package managers beyond what the repository uses (the command detects the project's ecosystem at runtime)

## Decisions

### 1. Command structure: phased pipeline with human gates

The command follows a pipeline: **Collect → Analyze → Plan → Remediate → Validate → Propose**. Human confirmation gates are placed before any mutation (branch creation, commits) and before any remote operation (push, PR creation).

**Rationale**: Mirrors the `review_pr.md` pattern of progressive disclosure. The user sees the full remediation plan before any action is taken, and can approve/reject individual fix groups.

**Alternatives considered**: Single-shot "fix everything" approach. Rejected because: large-scale changes without human review violate the Incremental Improvement principle, and batch mutations are harder to undo.

### 2. Alert collection: Dependabot + code scanning only

Collect Dependabot vulnerability alerts and code scanning alerts. Exclude secret scanning.

**Rationale**: Dependabot and code scanning alerts have well-defined remediation paths (version bumps, code fixes) that an AI agent can propose. Secret scanning alerts require credential rotation and service reconfiguration that is out-of-band and organization-specific.

### 3. Relationship analysis: dependency-graph-based grouping

Group alerts using these relationships:
- **Same root dependency**: Multiple CVEs in the same direct dependency (one version bump fixes all)
- **Transitive chain**: A vulnerability in a transitive dependency that can be resolved by bumping its parent
- **Shared fix version**: Multiple alerts across different packages that are all resolved by the same coordinated version bump
- **Independent**: Alerts with no relationship to other alerts -- each gets its own fix branch

For code scanning alerts, group by:
- **Same file**: Multiple findings in the same source file
- **Same rule**: Multiple instances of the same rule violation

**Rationale**: Grouping reduces PR count and ensures related changes are atomic. A single direct dependency bump that resolves 5 transitive CVEs is better as 1 PR than 5.

### 4. Branch and PR scoping strategy

Each independent fix group gets its own branch: `fix/security-<short-description>`. Branch names MUST NOT include CVE IDs or vulnerability details to avoid disclosing specific attack vectors in branch listings.

**Rationale**: Scoped PRs are easier to review, test independently, and revert if needed. The naming convention avoids information leakage while remaining descriptive.

### 5. Dependency version selection: conservative upgrade strategy

For dependency updates, the command SHALL:
1. Check if a patch-level fix exists (prefer `1.2.3` → `1.2.4` over `1.2.3` → `2.0.0`)
2. If only a minor/major bump is available, warn the user about potential breaking changes
3. Check the dependency's changelog/release notes for breaking change indicators
4. Run local tests after the version bump to detect regressions

**Rationale**: Patch-level fixes minimize risk. Major version bumps require human judgment about migration effort.

**Alternatives considered**: Always use the latest version. Rejected because: major version bumps can introduce breaking API changes that the agent cannot fully evaluate.

### 6. Information sensitivity in PR content

PR titles use generic descriptions (e.g., "fix: update package-x to resolve security vulnerability"). PR bodies reference the GitHub advisory URL (already public) but MUST NOT include:
- Exploitation techniques or proof-of-concept details
- Internal system architecture details that could aid attackers
- Specific vulnerable code paths beyond what the public advisory describes

**Rationale**: GitHub advisories are public by design, so linking to them is safe. Adding exploitation details in PR descriptions expands the attack surface window during the PR review period.

### 7. CI validation: reuse review_pr.md's local tool detection

The command reuses the same local tool detection pattern from `review_pr.md` (Step 3): check for `Makefile`, `.golangci.yml`, `ruff.toml`, `.pre-commit-config.yaml`, etc., and run the appropriate tools after each fix to validate the change doesn't break anything.

**Rationale**: Consistency with existing patterns. The detection logic is well-tested and covers the common toolchains.

### 8. Token permissions: fail-fast with clear guidance

If the `gh` CLI returns a 403 or 404 for security alert endpoints, the command SHALL stop early and display the exact permissions needed, with instructions for both classic and fine-grained tokens.

**Rationale**: Security alert APIs require elevated permissions that users may not have configured. A clear error message is better than silently processing an empty alert list.

## Risks / Trade-offs

- **[Dependency resolution complexity]** Some ecosystems have complex dependency trees where a bump in one package requires coordinated bumps in others. → Mitigation: The command presents the plan for human review before acting. If the dependency graph is too complex, it warns rather than guessing.
- **[Breaking changes from version bumps]** A patch-level fix might still introduce behavioral changes. → Mitigation: Local test execution after each fix validates the change. If tests fail, the fix group is flagged for manual intervention.
- **[Rate limiting]** GitHub API rate limits may be hit on repositories with many alerts. → Mitigation: Use a single paginated API call per alert type, process locally. The `gh` CLI handles pagination natively.
- **[Stale lock files]** Dependency version bumps may require regenerating lock files (`package-lock.json`, `go.sum`, `poetry.lock`). → Mitigation: The command detects the package manager and runs the appropriate lock file regeneration command after each version bump.
- **[Large command file size]** The command may approach 400+ lines, similar to `review_pr.md`. → Mitigation: This is an established pattern in the role. The command's complexity justifies the length.
- **[Code scanning fixes require code understanding]** Code scanning alerts (e.g., SQL injection, XSS) require contextual code changes, not just version bumps. → Mitigation: For code scanning fixes, the command presents the alert details, shows the affected code, and proposes a fix. If the fix is non-trivial, it flags for manual intervention rather than guessing.
