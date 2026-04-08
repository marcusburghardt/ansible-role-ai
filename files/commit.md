# Commit Standards (Baseline Defaults)

These are baseline commit standards applied globally. **If the current repository
provides its own commit guidelines** in any repository-level file used by AI tools
(such as `constitution.md`, `.specify/memory/constitution.md`, `AGENTS.md`,
`CONTRIBUTING.md`, or similar), **those repository-level rules take precedence**
over the defaults below. When a conflict exists, always follow the repository's
rules.

## Commit Message Format

All commit messages MUST follow the **Conventional Commits** specification
(https://www.conventionalcommits.org/).

Format: `<type>[optional scope]: <description>`

Common types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or correcting tests
- `chore`: Changes to build process, auxiliary tools, or maintenance

## Required Trailers

### Signed-off-by

All commits MUST include a `Signed-off-by` trailer with the author's name and
email. This certifies the contributor's right to submit the code under the
project's license (Developer Certificate of Origin).

When creating commits, always use the `-s` flag: `git commit -s`

### Assisted-by

Commits that were authored or substantially assisted by an AI tool MUST include
an `Assisted-by` trailer identifying the tool and model used.

Format: `Assisted-by: <tool> (<model>)`

Example: `Assisted-by: OpenCode (claude-opus-4-6)`

Use your actual tool name and model identifier when creating commits.

## Example

```
feat: add user authentication endpoint

Implement JWT-based authentication with token refresh support.

Signed-off-by: Jane Doe <jane@example.com>
Assisted-by: OpenCode (claude-opus-4-6)
```
