# Pull Request Standards (Baseline Defaults)

These are baseline PR standards applied globally. They are a **floor**, not a
replacement for repository policy.

A repository may add requirements in its own guidance (such as `CONTRIBUTING.md`,
`AGENTS.md`, `.specify/memory/constitution.md`, or similar). Repository rules
take precedence only where they are **stricter** or explicitly waive a specific
rule below. A repository that is silent on a rule does not opt out of it.

## PR Title

PR titles MUST use the same Conventional Commits format as commit messages:

```text
<type>[optional scope][!]: <description>
```

- Use the types defined in `commit.md`.
- Keep the complete title at or below **72 characters**.
- Do not end the title with a period.
- Use the imperative mood, for example `feat: add parser cache`.
- Mark a breaking change with `!` and describe the migration in the body.

The title becomes the squash-merge commit subject in many repositories, so it
must stand on its own.

## PR Template

Before creating a pull request, **always** check for a PR template in the
repository. Look for these files in order:

1. `.github/pull_request_template.md`
2. `.github/PULL_REQUEST_TEMPLATE.md`
3. `.github/PULL_REQUEST_TEMPLATE/` (directory with multiple templates)

If a template exists, the PR body **must** follow the template's structure and
sections exactly, filling in the placeholders with relevant content from the
changes being proposed. Never generate a custom PR body format when a template
is available.

## PR Body Without a Template

If no template exists, use a concise body with:

- **Summary**: what changed and why
- **Related issues**: links or `Fixes #<number>`
- **Review hints**: risky areas, validation performed, and anything reviewers
  should check first

Do not describe internal system architecture or security-sensitive details that
could aid an attacker.

## Validation

Check the title before creating the pull request:

```bash
python3 ~/bin/pr_workflow.py validate-pr-title --title "<type>(<scope>): <summary>"
```

A nonzero exit means the title does not meet the baseline. Fix the title rather
than bypassing the check.
