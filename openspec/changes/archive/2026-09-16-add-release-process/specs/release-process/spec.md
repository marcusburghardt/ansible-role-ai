## ADDED Requirements

### Requirement: Automated release PR from conventional commits
The repository SHALL have a GitHub Actions workflow (`ci_release.yml`) that triggers on
push to `main` and uses `release-please-action` (v4) to analyze conventional commit
messages since the last release tag. When releasable commits are detected (`feat:`, `fix:`,
or commits with `BREAKING CHANGE`), the action SHALL open or update a release PR that
bumps the version according to semver and updates `CHANGELOG.md`.

#### Scenario: Feature commit triggers minor version bump
- **WHEN** a commit with prefix `feat:` is pushed to `main`
- **THEN** release-please SHALL open (or update) a release PR proposing a minor version
  bump (e.g., `0.1.0` to `0.2.0`)

#### Scenario: Fix commit triggers patch version bump
- **WHEN** a commit with prefix `fix:` is pushed to `main`
- **THEN** release-please SHALL open (or update) a release PR proposing a patch version
  bump (e.g., `0.1.0` to `0.1.1`)

#### Scenario: Breaking change triggers major version bump
- **WHEN** a commit contains `BREAKING CHANGE` in the footer or uses `!` suffix
- **THEN** release-please SHALL open (or update) a release PR proposing a major version
  bump (e.g., `0.1.0` to `1.0.0`)

#### Scenario: Non-releasable commits do not trigger a release PR
- **WHEN** only `chore:`, `docs:`, `refactor:`, or `test:` commits are pushed to `main`
- **THEN** release-please SHALL NOT open a release PR

### Requirement: Release PR creates tag and GitHub Release when merged
When the release PR opened by release-please is merged, the action SHALL create a git tag
(format: `v<version>`, e.g., `v0.1.0`) and a GitHub Release with the changelog as the
release body.

#### Scenario: Merging the release PR creates a tag
- **WHEN** the maintainer merges the release PR
- **THEN** a git tag matching the new version SHALL be created on the merge commit

#### Scenario: Merging the release PR creates a GitHub Release
- **WHEN** the maintainer merges the release PR
- **THEN** a GitHub Release SHALL be created with the tag and changelog contents

### Requirement: CHANGELOG.md is auto-maintained
The release-please action SHALL update `CHANGELOG.md` in the release PR with entries
derived from conventional commit messages. The changelog SHALL group entries by type
(`feat`, `fix`, etc.) and include the version number and date.

#### Scenario: Changelog is updated in the release PR
- **WHEN** release-please opens or updates a release PR
- **THEN** the PR SHALL include changes to `CHANGELOG.md` reflecting all releasable
  commits since the last tag

### Requirement: Galaxy publishes only on formal releases
The `ci_galaxy_publish.yml` workflow SHALL trigger on `release: types: [published]`
instead of `push: branches: [main]`. Galaxy SHALL only import the role when a GitHub
Release is published.

#### Scenario: Push to main does not trigger Galaxy import
- **WHEN** a commit is pushed to `main` without a release being published
- **THEN** the Galaxy publish workflow SHALL NOT run

#### Scenario: Publishing a release triggers Galaxy import
- **WHEN** a GitHub Release is published (via release-please PR merge)
- **THEN** the Galaxy publish workflow SHALL run and import the role to Galaxy

### Requirement: Release-please configuration files
The repository SHALL contain `.release-please-manifest.json` (tracking the current
version) and `release-please-config.json` (configuring release-please behavior). The
manifest SHALL bootstrap at version `0.1.0`. The config SHALL use release type `simple`.

#### Scenario: Initial version is 0.1.0
- **WHEN** examining `.release-please-manifest.json` after initial setup
- **THEN** the version SHALL be `0.1.0`

#### Scenario: Release type is simple
- **WHEN** examining `release-please-config.json`
- **THEN** the release type SHALL be `simple`

### Requirement: Workflow permissions follow least privilege
The release workflow SHALL use `contents: write` and `pull-requests: write` permissions
(required for creating tags and PRs). The Galaxy publish workflow SHALL retain
`contents: read` only.

#### Scenario: Release workflow has write permissions
- **WHEN** examining `ci_release.yml`
- **THEN** the job SHALL have `contents: write` and `pull-requests: write` permissions

#### Scenario: Galaxy workflow has read-only permissions
- **WHEN** examining `ci_galaxy_publish.yml`
- **THEN** the job SHALL have `contents: read` permission only
