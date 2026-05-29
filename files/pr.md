# Pull Request Standards (Baseline Defaults)

These are baseline PR standards applied globally. **If the current repository
provides its own PR guidelines** in any repository-level file (such as
`AGENTS.md`, `CONTRIBUTING.md`, or similar), **those repository-level rules
take precedence** over the defaults below.

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

If no template exists, use a concise format with: summary of changes, related
issues, and any review hints.
