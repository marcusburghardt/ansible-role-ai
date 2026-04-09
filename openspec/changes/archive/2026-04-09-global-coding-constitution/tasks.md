## 1. Create the Coding Standards File

- [x] 1.1 Create `files/coding-standards.md` with organization-agnostic content extracted from the repository root `constitution.md`: precedence deferral header, Core Principles I-VII with rationales, Contribution Workflow (branching strategy, PR standards excluding commit message/trailer sections), Coding Standards (all-language guidelines, Go, Python, YAML/GitHub Actions, Containers). Exclude: ComplyTime branding, Repository Structure table, Infrastructure Standards Centralization, Governance section, Commit Messages/Trailers subsections.

## 2. Update Default Variables

- [x] 2.1 In `defaults/main.yml`, add `~/.config/opencode/coding-standards.md` to the `ai_opencode_instructions` list, positioned after `~/.config/opencode/commit.md` and before repository-relative paths.

## 3. Update Task File for Deployment

- [x] 3.1 In `tasks/configure_opencode.yml`, add a task to deploy `coding-standards.md` using `ansible.builtin.copy` from `files/coding-standards.md` to `~/.config/opencode/coding-standards.md` with mode `0640`, following the same pattern as the existing `commit.md` deployment task.

## 4. Update Spec Baseline

- [x] 4.1 In `openspec/specs/opencode-configuration/spec.md`, update the "Instructions list includes org governance files by default" scenario to reflect the new default `ai_opencode_instructions` list that includes `~/.config/opencode/coding-standards.md`.

## 5. Verification

- [x] 5.1 Run `ansible-lint` to verify the updated tasks and defaults have no lint issues.
- [x] 5.2 Verify the deployed `coding-standards.md` contains no organization-specific content (no "ComplyTime", "org-infra", Apache License mandates, or governance procedures).
- [x] 5.3 Verify the deployed `coding-standards.md` contains no commit standards (no Conventional Commits, Signed-off-by, or Assisted-by sections) to confirm no overlap with `commit.md`.
