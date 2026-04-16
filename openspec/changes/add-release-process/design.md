## Context

The repository uses conventional commits consistently but has no release process. Every
push to `main` triggers an Ansible Galaxy import via `ci_galaxy_publish.yml`. There are
no git tags, no versions, and no changelog. Galaxy always reflects HEAD of `main`.

The repository already has SHA-pinned GitHub Actions, Dependabot configured with `chore:`
prefix, and a `GALAXY_API_KEY` secret for Galaxy authentication.

## Goals / Non-Goals

**Goals:**
- Automated semantic versioning derived from conventional commits.
- PR-based release flow: release-please opens a PR, maintainer reviews and merges to
  release.
- Auto-generated CHANGELOG.md from commit messages.
- Galaxy imports only on formal releases (tagged versions), not on every push.
- Bootstrap at version `0.1.0`.

**Non-Goals:**
- Fully automatic releases (no PR review step) -- planned for later.
- Automating local role updates on consumer machines -- separate concern.
- Signing releases or adding SLSA provenance -- out of scope for now.
- CI lint/test workflows -- separate concern.

## Decisions

### D1: Use release-please for version management

**Decision**: Use Google's `release-please-action` (v4) in a GitHub Actions workflow.

**Rationale**: release-please is the standard tool for conventional-commit-based releases.
It creates a release PR that bumps the version and updates the changelog. When merged, it
creates the git tag and GitHub Release. It requires no external services -- only
`GITHUB_TOKEN`. It supports the "simple" release type which works for any project without
needing language-specific version files.

**Alternatives considered**:
- *semantic-release (npm)*: More mature but heavier -- requires Node.js, npm plugins, and
  more configuration. Designed for npm packages primarily.
- *Custom script*: Lightweight but fragile. Would need to parse conventional commits,
  compute versions, and manage tags manually. Reinvents what release-please does.
- *Manual tagging*: No automation. Error-prone and easy to forget.

### D2: Release type "simple"

**Decision**: Use release-please's `simple` release type.

**Rationale**: The `simple` type manages a version number without needing language-specific
files (like `package.json` or `setup.py`). It tracks the version in
`.release-please-manifest.json` and updates `CHANGELOG.md`. This is appropriate for an
Ansible role which has no native version file -- Galaxy reads the version from git tags.

### D3: Galaxy publish triggers on release, not push

**Decision**: Change `ci_galaxy_publish.yml` trigger from `on: push: branches: [main]`
to `on: release: types: [published]`.

**Rationale**: Galaxy should only import a role when a formal release exists. This ensures
every Galaxy version corresponds to a tagged, intentional release with a changelog entry.
The workflow is otherwise unchanged -- same `ansible-galaxy role import` command.

### D4: Bootstrap version at 0.1.0

**Decision**: Start with version `0.1.0` in the release-please manifest.

**Rationale**: The role is functional but actively evolving with expected breaking changes.
Starting at `0.x` signals pre-stable status per semver convention. The recent Ollama
changes (breaking defaults) would have warranted a major bump if we were at `1.x`.

### D5: Workflow permissions follow least privilege

**Decision**: The release workflow uses explicit per-job permissions:
`contents: write` and `pull-requests: write`. The Galaxy publish workflow retains
`contents: read` only.

**Rationale**: Follows the repository's existing security pattern (SHA-pinned actions,
minimal permissions). release-please needs write access to create PRs and tags.
Galaxy publish only needs to read the repo for import.

## Risks / Trade-offs

- **[release-please is a Google dependency]** --> It is widely adopted, open-source
  (Apache-2.0), and used by Google's own projects. The action is versioned and can be
  SHA-pinned. Risk is low.

- **[PR-based flow adds friction]** --> Every release requires merging an extra PR. This
  is intentional for now (review before release). Can be switched to fully automatic
  later by having the workflow auto-merge the release PR.

- **[Existing commits have no tag baseline]** --> release-please needs a starting point.
  The manifest bootstraps at `0.1.0`. The first release PR will include all commits
  since the beginning of the repo in the changelog, which may be large. Subsequent
  releases will be incremental.

## Migration Plan

1. Create release-please config files (manifest + config).
2. Create the `ci_release.yml` workflow.
3. Modify the `ci_galaxy_publish.yml` trigger.
4. Push to `main` -- release-please opens the first release PR.
5. Review and merge the release PR -- tag `v0.1.0` is created, Galaxy imports.
6. Verify Galaxy shows version `0.1.0`.
