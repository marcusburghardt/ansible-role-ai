---
description: "Checkout a remote PR locally for review"
---

# Checkout PR

Checkout PR number $ARGUMENTS locally for review.

## Pre-flight: Organization Verification

Before performing any operations, verify the current repository belongs to a trusted organization:

1. Run: `gh repo view --json owner --jq '.owner.login'`
2. Check the `TRUSTED_GITHUB_ORGS` environment variable for a comma-separated list of trusted organizations
3. If the repo owner matches any trusted org, proceed silently to the checkout steps
4. If the repo owner does NOT match (or `TRUSTED_GITHUB_ORGS` is empty/unset), warn the user:
   > "This repository belongs to '**\<owner\>**', which is not in the trusted organizations list. Proceed with checkout anyway?"
5. Wait for the user's confirmation before continuing. If they decline, abort.

## Checkout Steps

Follow these exact steps:

1. Set the branch name to REVIEW_PR_$ARGUMENTS
2. Run: git fetch upstream pull/$ARGUMENTS/head:REVIEW_PR_$ARGUMENTS
3. If the fetch succeeds, the branch is new. Run: git checkout REVIEW_PR_$ARGUMENTS
4. If the fetch fails (branch already exists), checkout the branch first with: git checkout REVIEW_PR_$ARGUMENTS, then update it with: git pull upstream pull/$ARGUMENTS/head --rebase --force
5. After checkout, show a short summary: the current branch name, the latest commit on it, and confirm whether it was a fresh checkout or an update.

Do NOT create commits, do NOT push anything. This is a read-only review operation.

### Next Steps

After the PR is checked out, suggest the most relevant next actions:

- "Run `/review_pr $ARGUMENTS` for a full AI-assisted review of this PR."
- If a `Makefile` exists: "Run local tests: `make test` (or `make lint` for lint checks)."
- If `go.mod` exists: "Run Go tests: `go test ./...`"
- If `pyproject.toml` or `setup.py` exists: "Run Python tests: `pytest`"
- "When done, switch back to main: `git checkout main`"
- "Run `/workflow_next` to see what else needs attention."
