## Context

The Ansible role currently deploys a `commit.md` global instruction file to `~/.config/opencode/` using `ansible.builtin.copy` from `files/commit.md`. This file is referenced in the `ai_opencode_instructions` list and loaded into every OpenCode session. The role also deploys `opencode.json` from a Jinja2 template with the instructions array populated from the `ai_opencode_instructions` variable.

The repository contains a `constitution.md` at the root with mature coding principles developed for the ComplyTime organization. These principles (Core Principles I-VII, language-specific coding standards, contribution workflow) are universally applicable but currently only available to projects that explicitly include the file. There is no mechanism for these principles to apply globally across all AI-assisted contributions.

The user's global `opencode.json` already includes `~/.config/opencode/commit.md` as the first instruction, establishing a precedence pattern where global baseline files appear before project-relative paths.

## Goals / Non-Goals

**Goals:**
- Deploy an organization-agnostic coding standards file as a global OpenCode instruction file
- Ensure the coding standards file follows the same precedence-deferral pattern as `commit.md` (project rules override)
- Follow the established role pattern: static file deployed via `ansible.builtin.copy`
- Keep the coding standards file modular and non-overlapping with `commit.md` (avoid duplicating commit standards)
- Update the default `ai_opencode_instructions` to include the new file

**Non-Goals:**
- Templating the coding standards file with Jinja2 variables (unnecessary complexity; the file is a static reference document)
- Replacing or modifying project-level constitutions or `AGENTS.md` files
- Making the coding standards file cover organization-specific governance, amendment procedures, or repo structure requirements
- Consolidating `commit.md` into the coding standards file (they serve distinct, focused purposes)

## Decisions

### 1. Static file deployment (not a Jinja2 template)

Deploy `coding-standards.md` as a static file using `ansible.builtin.copy`, identical to the pattern used for `commit.md`.

**Rationale**: The file contains reference principles, not per-user configuration. A Jinja2 template would add complexity without meaningful benefit. Users who need customization can either override `ai_opencode_instructions` to exclude it or rely on project-level files to take precedence.

**Alternatives considered**: Jinja2 template with toggleable language sections (Go, Python, YAML). Rejected because: the principles are advisory, the LLM naturally focuses on relevant sections, and the template adds maintenance burden without clear value.

### 2. Content extraction: what to include vs. exclude

**Include** (organization-agnostic):
- Core Principles I-VII (single source of truth, simplicity, incremental improvement, readability, composability, do not reinvent the wheel, convention over configuration)
- All-language coding standards (line endings, pre-commit hooks, Makefile, testing, line length, lint)
- Language-specific guidelines (Go, Python, YAML/GitHub Actions, Containers)
- Contribution workflow (branching strategy, PR standards)

**Exclude** (organization-specific or already covered):
- "ComplyTime Constitution" branding -- replace with generic title
- Repository Structure & Standards table (mandates Apache License, specific files)
- Infrastructure Standards Centralization (references `org-infra` repo)
- Governance section (amendment procedures, compliance review, versioning)
- "Incrementing This Constitution" (org-specific extension model)
- Commit Messages and Commit Trailers subsections (already covered by `commit.md`)

**Rationale**: The commit standards are intentionally kept separate in `commit.md` to avoid duplication and maintain single responsibility. The coding standards file focuses on coding principles and standards.

### 3. Precedence header pattern

Add a precedence header identical in structure to `commit.md`:

> These are baseline coding principles applied globally. If the current repository provides its own coding principles or constitution in any repository-level file (such as `constitution.md`, `AGENTS.md`, `CONTRIBUTING.md`, or similar), those repository-level rules take precedence over the defaults below.

**Rationale**: Consistent with the established pattern. The LLM respects this directive, as demonstrated by `commit.md` already working correctly in practice.

### 4. Instruction ordering in `ai_opencode_instructions`

Position the coding standards file after `commit.md` but before project-relative paths:

```yaml
ai_opencode_instructions:
  - "~/.config/opencode/commit.md"
  - "~/.config/opencode/coding-standards.md"
  - ".specify/memory/constitution.md"
  - "AGENTS.md"
  - "CLAUDE.md"
```

**Rationale**: Global baseline files load first, project-level files load after. Combined with the explicit precedence header, this ensures project rules override global defaults.

### 5. File location and naming

Deploy to `~/.config/opencode/coding-standards.md` -- same directory as `commit.md`.

**Rationale**: Consistent with existing file layout. The name `coding-standards.md` is self-explanatory, pairs well with `commit.md` (both are domain-specific baseline files), and avoids collision with project-level `constitution.md` files or SpecKit terminology.

## Risks / Trade-offs

- **[Token budget]** Adding the full coding standards file to every session increases the base prompt size by ~2-3K tokens. → Mitigation: The document is well-structured with clear sections; the LLM can reference relevant sections as needed. This is comparable to a typical AGENTS.md file.
- **[Section relevance]** Language-specific sections (Go, Python, etc.) may not apply to every project. → Mitigation: The LLM naturally focuses on relevant sections. The precedence header allows project-level files to narrow scope. Acceptable trade-off for universal coverage.
- **[Overlap with commit.md]** The original constitution includes commit standards. → Mitigation: Explicitly exclude commit-related sections from the coding standards file, keeping `commit.md` as the single source for commit standards.
- **[Existing users]** Users who have already overridden `ai_opencode_instructions` will not get the new file automatically. → Mitigation: Document the new file in role README/changelog so users can add it manually if desired.
