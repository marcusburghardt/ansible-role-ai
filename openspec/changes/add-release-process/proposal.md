## Why

Every push to `main` triggers an Ansible Galaxy import, meaning Galaxy always reflects the
latest commit with no versioning, no changelog, and no way for consumers to pin a
known-good state. Breaking changes (like the recent default model switch) ship silently.
A proper release process provides semantic versioning, changelogs from conventional
commits, and ensures Galaxy only updates on intentional releases.

## What Changes

- **Add release-please GitHub Actions workflow**: A new `ci_release.yml` workflow triggers
  on push to `main`, analyzes conventional commits, opens a release PR with version bump
  and changelog updates. When the PR is merged, it creates a git tag and GitHub Release.
- **Modify Galaxy publish workflow**: Change `ci_galaxy_publish.yml` trigger from
  `push: main` to `release: published`, so Galaxy only imports when a formal release
  exists. Galaxy reads the version from the git tag automatically.
- **Add CHANGELOG.md**: Generated and maintained by release-please from conventional commit
  messages.
- **Add .release-please-manifest.json and release-please-config.json**: Configuration
  files that tell release-please the current version and how to manage releases.
- **Bootstrap initial version at v0.1.0**: Create the initial release-please manifest
  starting at version `0.1.0`.

## Capabilities

### New Capabilities

- `release-process`: Covers the release-please configuration, the release workflow,
  changelog generation, and the Galaxy publish trigger change.

### Modified Capabilities

_(none -- the Galaxy publish workflow changes are purely operational, not spec-level
behavior changes to the role itself)_

## Impact

- **`.github/workflows/ci_release.yml`**: New workflow for automated release PR creation.
- **`.github/workflows/ci_galaxy_publish.yml`**: Trigger changes from `push` to `release`.
- **`.release-please-manifest.json`**: New file tracking current version.
- **`release-please-config.json`**: New file configuring release-please behavior.
- **`CHANGELOG.md`**: New file, auto-maintained.
- **No changes to role behavior**: This is purely CI/CD infrastructure.
- **GitHub permissions**: The release workflow needs `contents: write` and
  `pull-requests: write` for creating tags and PRs.
