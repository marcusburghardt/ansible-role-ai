# Spec Delta

## ADDED Requirements

### Requirement: Deploy the retrospective helper
`configure_opencode` SHALL deploy `files/scripts/session_insights.py` to
`{{ ai_user_scripts_dir }}` with mode `0750`. The deployment SHALL be
independent of the command blocklist, so disabling the command does not remove
the helper.

#### Scenario: Helper deployed with the default configuration
- **WHEN** `configure_opencode` runs
- **THEN** `session_insights.py` SHALL exist in the user scripts directory with
  executable permissions

#### Scenario: Command disabled
- **WHEN** `ai_opencode_commands_disabled` contains `session_retro`
- **THEN** the helper SHALL still be deployed and usable directly

### Requirement: Continue authorized and reversible work
`files/agent-operating-rules.md` SHALL require continued execution for
reversible, in-scope actions already authorized by the task, including local
edits, reads, tests, and linters.

#### Scenario: Authorized local validation
- **WHEN** an implementation task is in scope and the repository provides a
  local test or lint command
- **THEN** the agent SHALL run it without asking for confirmation and report the
  result

#### Scenario: In-scope follow-up edit
- **WHEN** a failing local test requires a change inside the requested scope
- **THEN** the agent SHALL make the change and re-run the test without pausing
  for confirmation

### Requirement: Stop for irreversible or external actions
`files/agent-operating-rules.md` SHALL require stopping for irreversible or
destructive actions, remote mutations, spending, scope or requirement ambiguity,
credential handling, and unavailable mandatory gates.

#### Scenario: Remote mutation
- **WHEN** the next step would push, open a pull request, post a review, or
  merge
- **THEN** the agent SHALL stop and obtain explicit confirmation

#### Scenario: Ambiguous scope
- **WHEN** the requested outcome conflicts with the repository policy or the
  specification
- **THEN** the agent SHALL stop and state the conflict and the exact decision
  needed

### Requirement: Batch decisions and avoid rhetorical confirmations
`files/agent-operating-rules.md` SHALL prohibit ending a turn with a rhetorical
confirmation for work already requested. It SHALL require batching independent
decisions into a single question with options.

#### Scenario: Serialized questions
- **WHEN** several independent decisions are required before work can continue
- **THEN** the agent SHALL ask them together in one decision request rather than
  one at a time

#### Scenario: Work already authorized
- **WHEN** the requested task authorizes the next local action
- **THEN** the agent SHALL proceed and report the result instead of asking
  whether to proceed

### Requirement: Require confirmation for implicit GitHub API writes
The default permission policy SHALL ask before any `gh api` invocation that can
write, including explicit method forms and implicit write forms using `-f`,
`-F`, `--field`, `--raw-field`, or `--input`. Read-only `gh api` invocations
SHALL remain allowed.

#### Scenario: Explicit method write
- **WHEN** the agent runs `gh api -X POST /repos/owner/repo/issues`
- **THEN** the policy SHALL ask for confirmation

#### Scenario: Implicit field write
- **WHEN** the agent runs `gh api /repos/owner/repo/issues -f title=example`
- **THEN** the policy SHALL ask for confirmation

#### Scenario: Read-only request
- **WHEN** the agent runs `gh api /repos/owner/repo/pulls/1`
- **THEN** the policy SHALL allow the request without a prompt

### Requirement: Restrict git configuration reads and writes
The default permission policy SHALL allow only read-only `git config` forms such
as `--get`, `--get-*`, `--list`, `-l`, and `--show-*`. Any other `git config`
invocation SHALL ask for confirmation so that hooks and signing configuration
cannot be changed without review.

#### Scenario: Read a configuration value
- **WHEN** the agent runs `git config --get user.email`
- **THEN** the policy SHALL allow the command

#### Scenario: Change a configuration value
- **WHEN** the agent runs `git config core.hooksPath /tmp/hooks`
- **THEN** the policy SHALL ask for confirmation

#### Scenario: List configuration
- **WHEN** the agent runs `git config --list`
- **THEN** the policy SHALL allow the command

### Requirement: Verify deployment and policy in tests
The Ansible smoke test SHALL assert that the retrospective command and helper
are deployed with the expected modes, that the autonomy contract is present in
the deployed instruction file, and that the hardened permission rules are
rendered in the expected order relative to the allow rules they override.

#### Scenario: Test asserts the command and helper
- **WHEN** the smoke test inspects the isolated home
- **THEN** it SHALL fail if the command or helper is missing or has the wrong
  mode

#### Scenario: Test asserts the permission override order
- **WHEN** the smoke test parses the rendered `opencode.json`
- **THEN** it SHALL fail if an implicit `gh api` write rule or the `git config`
  write rule does not appear after the broader allow rules

### Requirement: Document the retrospective command and policy changes
The README SHALL document `/session_retro`, the helper, the privacy levels, the
proposal targets, the intervention ledger, and the two hardened permission
rules. It SHALL state that the retrospective is advisory and that no permission
grant is applied automatically.

#### Scenario: Reader looks up the command
- **WHEN** a user reads the README command section
- **THEN** the privacy defaults and the manual approval boundary SHALL be
  explicit
