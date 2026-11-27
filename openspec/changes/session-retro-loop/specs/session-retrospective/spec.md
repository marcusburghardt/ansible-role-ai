# Spec Delta

## ADDED Requirements

### Requirement: Deploy a session retrospective command
The role SHALL deploy `files/commands/session_retro.md` to
`{{ ai_opencode_command_dir }}` with frontmatter containing a `description`,
an H1 title, an Arguments section, and step-by-step execution instructions. The
command SHALL be auto-discovered like other built-in commands and SHALL be
disableable through `ai_opencode_commands_disabled`. The command SHALL accept an
optional day window, an optional project filter, an optional detail level, and
a verification mode.

#### Scenario: Command is deployed and discoverable
- **WHEN** `configure_opencode` runs with the default command settings
- **THEN** `session_retro.md` SHALL be present in the deployed command directory
  and invoke the deployed helper

#### Scenario: Command is disabled
- **WHEN** `ai_opencode_commands_disabled` contains `session_retro`
- **THEN** the command file SHALL NOT be deployed

#### Scenario: Command without arguments
- **WHEN** the user runs `/session_retro` without arguments
- **THEN** the command SHALL analyze the default window for the current project
  and SHALL NOT require a repository workflow framework

### Requirement: Deploy a deterministic read-only helper
The role SHALL deploy `files/scripts/session_insights.py` to
`{{ ai_user_scripts_dir }}` with mode `0750`. The helper SHALL use only the
Python standard library, SHALL require Python 3.10 or newer, and SHALL operate
without network access. It SHALL open OpenCode and metrics databases read-only
and SHALL NEVER modify session data, permission grants, or configuration.

#### Scenario: Helper runs offline
- **WHEN** the host has no network access
- **THEN** the helper SHALL still produce the scorecard from local data

#### Scenario: Helper cannot write session state
- **WHEN** the helper inspects the OpenCode database
- **THEN** it SHALL use read-only access and SHALL leave permissions and
  session rows unchanged

### Requirement: Aggregate local signals with graceful degradation
The helper SHALL combine available local sources: `opencode stats --json`, the
`opencode-metrics` database, and read-only aggregates over OpenCode session
storage. It SHALL support both the legacy `message`/`part` tables and the V2
`session_message`/`session_part` tables. When a source or table is absent, the
helper SHALL report the limitation and continue with the remaining sources.

#### Scenario: Metrics database is absent
- **WHEN** `~/.local/share/opencode-metrics/metrics.db` does not exist
- **THEN** the scorecard SHALL still include tool, duplication, and session
  aggregates with an explicit missing-source notice

#### Scenario: Permission capture is unavailable
- **WHEN** the permission event table or contract version is absent
- **THEN** permission findings SHALL use session-level prompt and wait metrics
  and inferred canonical patterns, and SHALL label the reduced confidence

### Requirement: Produce the five-class scorecard
The helper SHALL produce findings for permission friction, confirmation stalls,
subagent and tool latency, token and context waste, and permission-policy
drift. It SHALL report the analysis window, the sources used, the number of
sessions and turns considered, and the normalized rates used for comparison.

#### Scenario: Full scorecard
- **WHEN** all sources are available for a 30-day window
- **THEN** the output SHALL contain all five finding classes, the window,
  per-source coverage, and session and turn counts

#### Scenario: No actionable findings
- **WHEN** no class exceeds the evidence threshold
- **THEN** the command SHALL report a clean result and SHALL NOT invent a
  recommendation

### Requirement: Default to aggregate and redacted output
At the default detail level the helper SHALL emit counts, rates, durations, and
normalized classes only. It SHALL NOT emit shell arguments, URLs, absolute
paths, environment values, message text, prompts, diffs, or file contents.
Canonical command patterns SHALL be limited to the command head and at most one
subcommand token after removing assignments, quoting, and paths.

#### Scenario: Permission resource contains a secret
- **WHEN** a captured resource contains a token, header value, or credential
- **THEN** the default output SHALL contain only the canonical command head and
  SHALL NOT contain the secret value

#### Scenario: Report is shared
- **WHEN** the user shares the default report outside the machine
- **THEN** the report SHALL NOT reveal repository file contents or user prompts

### Requirement: Require explicit consent for higher-detail levels
The helper SHALL support `patterns` and `snippets` detail levels. The
`snippets` level SHALL require an explicit `--allow-content` flag and SHALL
warn that content may be sensitive. Even at `snippets`, credentials, tokens,
private keys, and long encoded values SHALL be redacted.

#### Scenario: Snippets requested without consent
- **WHEN** the user requests `--detail snippets` without `--allow-content`
- **THEN** the helper SHALL reject the request and explain the consent flag

#### Scenario: Snippet redaction
- **WHEN** a snippet contains a bearer token or private key marker
- **THEN** the helper SHALL replace the sensitive value before writing output

### Requirement: Apply evidence thresholds and confidence
The helper SHALL require a minimum window, event count, and session spread
before proposing a change. It SHALL exclude sessions with extreme wall times or
tool spans that cross idle events from latency statistics. It SHALL label every
finding with high, medium, or low confidence and SHALL report low-confidence
findings without proposing them.

#### Scenario: Single outlier session
- **WHEN** one session accounts for most observed wait time
- **THEN** the finding SHALL be marked low confidence and SHALL NOT become a
  proposal

#### Scenario: Recurring pattern
- **WHEN** a canonical pattern recurs across at least 10 events in 3 sessions
  over at least 7 days
- **THEN** the finding SHALL be eligible for a proposal with its confidence
  level

### Requirement: Route proposals to the correct owner
Every proposal SHALL declare one target: role defaults, personal playbook,
repository guidance or tests, or the metrics plugin. A role proposal SHALL
describe a generic default safe for multiple users. A playbook proposal SHALL
describe an environment-specific override. A repository proposal SHALL
identify the repository and the concrete file or test to change. A plugin
proposal SHALL reference the permission-capture contract.

#### Scenario: Environment-specific path
- **WHEN** a finding depends on a user-specific path or organization
- **THEN** the proposal SHALL target the playbook rather than role defaults

#### Scenario: Generic default
- **WHEN** a finding applies to any user of the role and is risk-classified as
  safe
- **THEN** the proposal SHALL target role defaults

### Requirement: Never mutate automatically
The command SHALL NOT apply a permission rule, edit a repository, install a
hook, or create an OpenSpec change without explicit user selection and
confirmation. It SHALL present evidence, expected effect, risk, and a concrete
diff or snippet before requesting confirmation. It SHALL NOT interpret silence
as consent.

#### Scenario: Proposal is displayed
- **WHEN** the command presents a proposal
- **THEN** it SHALL wait for an explicit choice and SHALL leave the system
  unchanged if the user declines

#### Scenario: User selects an OpenSpec proposal
- **WHEN** the user approves creating a change for a role or repository
  proposal
- **THEN** the command SHALL create it only in the selected repository after
  confirmation

### Requirement: Store reports and interventions privately
The helper SHALL write reports under
`${XDG_STATE_HOME:-~/.local/state}/opencode/retro/` with directories mode
`0700` and files mode `0600`. Reports SHALL persist the scorecard and the
selected detail level. The command SHALL NOT create project workflow
directories or change project `.gitignore` files.

#### Scenario: Report written
- **WHEN** the helper completes an analysis
- **THEN** the report directory and files SHALL have private permissions

#### Scenario: Project remains untouched
- **WHEN** the command runs inside a repository
- **THEN** no file SHALL be written into that repository unless the user
  approves a proposal

### Requirement: Record and verify interventions
The helper SHALL maintain an intervention ledger containing an identifier,
creation time, target, change reference, hypothesis, target metric, baseline
window and value, expected direction, review date, status, and result. It SHALL
provide a verification mode that compares the current window with the baseline
and recommends keep, revert, or extend. The ledger SHALL NOT store user consent
or raw session content.

#### Scenario: Baseline comparison
- **WHEN** the user verifies an intervention after its review date
- **THEN** the helper SHALL report the baseline and current values, the change,
  and a keep, revert, or extend recommendation

#### Scenario: Insufficient follow-up data
- **WHEN** the current window has too few sessions for comparison
- **THEN** the helper SHALL report insufficient evidence and SHALL NOT claim
  success or failure

### Requirement: Test the helper without real user data
The role SHALL include offline unit tests using synthetic fixtures for both
session storage schemas, a synthetic metrics database, permission events, and
intervention records. Tests SHALL cover redaction, evidence thresholds, source
degradation, and verification outcomes.

#### Scenario: Synthetic fixture suite
- **WHEN** the test suite runs
- **THEN** it SHALL use temporary databases and SHALL NOT read the user's real
  session or metrics data

#### Scenario: Redaction regression
- **WHEN** a fixture contains a secret-bearing resource
- **THEN** the test SHALL fail if the secret appears in any output level below
  `snippets`

### Requirement: Document the retrospective workflow
The README SHALL document the command, its privacy levels, the expected
proposal targets, the intervention ledger, and the relationship with
`opencode-metrics` and `workflow_next`.

#### Scenario: User reads the documentation
- **WHEN** a user looks up `/session_retro`
- **THEN** the README SHALL explain what data is read, what is emitted, and
  that no change is applied automatically
