## 1. Release-please Configuration

- [x] 1.1 Create `.release-please-manifest.json` with initial version `0.1.0`
- [x] 1.2 Create `release-please-config.json` with release type `simple`, changelog sections for `feat`/`fix`/`chore`/`docs`/`refactor`, and `include-component-in-tag: false` (single-package repo)

## 2. GitHub Actions Workflows

- [x] 2.1 Create `.github/workflows/ci_release.yml` -- triggers on push to `main`, uses `google-github-actions/release-please-action@v4` (SHA-pinned), with `contents: write` and `pull-requests: write` permissions
- [x] 2.2 Modify `.github/workflows/ci_galaxy_publish.yml` -- change trigger from `push: branches: [main]` to `release: types: [published]`

## 3. Verification

- [x] 3.1 Validate workflow YAML syntax with `yamllint`
- [x] 3.2 Commit and push -- verify release-please opens a release PR on GitHub
