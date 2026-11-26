## 1. Standards files

- [x] 1.1 Rewrite `files/commit.md` so the baseline is a floor, expand the
  Conventional Commits type set, document breaking changes, exemptions, and
  validation.
- [x] 1.2 Rewrite `files/pr.md` with Conventional Commit PR titles, template
  discovery, fallback body structure, and title validation.

## 2. Deployment

- [x] 2.1 Deploy `pr.md` from `tasks/configure_opencode.yml`.
- [x] 2.2 Add `~/.config/opencode/pr.md` to `ai_opencode_instructions` after
  `commit.md`.

## 3. PR title validation

- [x] 3.1 Keep `validate-pr-title` in `files/scripts/pr_workflow.py`.
- [x] 3.2 Remove commit-message validation from the helper; it moves to
  `ansible-role-git`.

## 4. Command alignment

- [x] 4.1 Update `workflow_next.md`, `refresh_spec_frameworks.md`,
  `security_remediation.md`, and `address_feedback.md` to use and reference the
  standards.

## 5. Tests and documentation

- [x] 5.1 Update `tests/test_pr_workflow.py` for PR title validation.
- [x] 5.2 Extend `tests/test.yml` to assert instruction deployment.
- [x] 5.3 Update `README.md` with commit/PR standards and the Git role handoff.
- [x] 5.4 Run `make test` and `make lint`.
