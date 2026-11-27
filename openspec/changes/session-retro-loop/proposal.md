## Why

Session friction is currently visible only in aggregate dashboards and is not
turned into configuration improvements. Local measurements show the cost:

- 557 permission prompts across 342 captured sessions, with roughly 646,000
  seconds of cumulative wait.
- 559 `question` tool calls across 179 sessions: median wait 92 seconds, p95
  20 minutes.
- Subagent `task` calls: p50 2.3 minutes, p95 24 minutes; some agent/model
  combinations average tens of minutes per run.
- 3,201 duplicate file reads and 1,496 repeated identical shell commands.
- 846 persisted permission grants across 10 repositories, including
  `git push *`, `git reset *`, `git rm *`, and unusable patterns such as
  `$cmd *` that teach nothing reusable.
- A policy gap: `gh *` is allowed while only explicit `-X`/`--method` writes
  ask, so implicit POST forms such as `gh api -f ...` and `--input` bypass the
  intended confirmation.

The data needed to act on this exists across `opencode stats`, the
`opencode-metrics` database, and read-only aggregates over OpenCode session
storage. What is missing is a repeatable loop that measures friction, ranks
opportunities with evidence, proposes changes for the right target, and checks
afterwards whether the change helped.

## What Changes

- Add a `/session_retro` command and a deterministic `session_insights.py`
  helper that produce a local scorecard for permission friction, confirmation
  stalls, subagent/tool latency, token and context waste, and permission-policy
  drift.
- Default to aggregate, redacted output. Raw commands, paths, message text, and
  transcripts never leave the machine unless an explicit higher-detail flag and
  consent are used.
- Route proposals by target: generic role defaults (this role), environment
  overrides (the personal playbook), repository guidance/tests (per-repo
  `AGENTS.md` or deterministic checks), and capture/data gaps (the
  `opencode-metrics` plugin).
- Add an intervention ledger and a verification mode so a configuration change
  is compared against its baseline window instead of being judged by feel.
- Define a versioned permission-capture contract for the `opencode-metrics`
  plugin, implemented in that repository as a parallel workstream. The plugin
  records only sanitized `permission.asked`/`permission.replied` events and
  exposes a friction view for the role helper to consume.
- Add an explicit autonomy contract to `agent-operating-rules.md` that says
  when an agent must continue, when it must stop, and how to batch decisions
  instead of serializing confirmations.
- Harden the two permission issues found during discovery: implicit-write
  `gh api` forms and the broad `git config *` allow rule.

## Capabilities

### New Capabilities

- `session-retrospective`: The `/session_retro` workflow, deterministic
  scorecard, privacy tiers, proposal routing, and intervention verification.
- `permission-capture`: The observer-only permission event contract implemented
  by `opencode-metrics` and consumed by the retrospective helper.

### Modified Capabilities

- `opencode-configuration`: Deploy the retrospective command and helper, add
  the autonomy contract, and close the identified permission-policy gaps.

## Impact

- **Files added**: `files/commands/session_retro.md`,
  `files/scripts/session_insights.py`, `tests/test_session_insights.py`,
  `openspec/changes/session-retro-loop/`.
- **Files modified**: `files/agent-operating-rules.md`,
  `vars/configure_opencode.yml`, `tests/test.yml`, `Makefile`, `README.md`.
- **Defaults**: no new role variables are required. Optional settings may be
  introduced for the report directory and retention, with safe defaults.
- **Compatibility**: the command and helper are opt-in and read-only. The
  capture contract is additive; consumers degrade gracefully when the metrics
  database or the permission table is absent. No existing permission decision
  changes except the two documented hardening rules.
- **Parallel repositories**: `~/GIT/me/opencode-metrics` implements the
  `permission-capture` contract. `~/GIT/mbtech/Ansible/dev_ai.yml` consumes
  environment-specific proposals. Other repositories receive proposals only;
  this change does not modify them.
