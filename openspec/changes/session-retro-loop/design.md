## Context

Three local stores contain the signals:

| Store | Contents | Constraint |
|---|---|---|
| `opencode stats --json` | tool reliability, p50 durations, model/token/cost mix | documented CLI, no permission detail |
| `opencode-metrics` database | per-session prompts, waits, duration, compactions, turns, cost, PRs | permission metrics lack the asked resource and are not backfillable |
| OpenCode session database | sessions, messages, tool parts, persisted permission grants | very large; V2 uses `session_message`/`session_part` while legacy rows remain in `message`/`part` |

`permission.asked` and `permission.replied` are ephemeral events. They contain
`sessionID`, `action`, `resources`, optional `save` patterns, source tool, and
the reply (`once`, `always`, `reject`). The metrics plugin already subscribes
to both events but discards everything except a count and a wait duration.

The current role permission policy allows `gh *` and asks for explicit
`-X`/`--method` write forms. `gh api` also performs POST when field flags or
`--input` are present, so the intended gate is incomplete. `git config *` is
allowed in full, including `core.hooksPath` and signing configuration.

## Goals / Non-Goals

**Goals:**

- Produce an evidence-based, local scorecard of session friction and waste.
- Recommend changes for the correct owner: role defaults, personal playbook,
  a concrete repository, or the metrics plugin.
- Keep raw session content local by default and make higher detail explicit.
- Verify whether an accepted change improved the target metric.
- Align the plugin contract and the role helper so both can be implemented in
  parallel without blocking each other.

**Non-Goals:**

- Automatically applying permission rules or editing repositories.
- Auto-learning allow rules from observed agent behavior.
- Reading or summarizing transcripts by default.
- Replacing the Grafana dashboards; the retrospective is decision-oriented,
  not a monitoring UI.
- Resolving every broad permission rule discovered during the audit. The two
  critical gaps are fixed here; the rest become ranked proposals.

## Decisions

### 1. Command plus deterministic helper, not a dashboard or a pure prompt

`/session_retro` follows the `review_pr` pattern: a markdown command defines
the interaction and a portable Python helper performs deterministic reads and
aggregation. The model receives only the scorecard and evidence, not raw
session data. This keeps results reproducible, testable offline, and cheap in
tokens compared with asking a model to read exports.

Alternative rejected: extend Grafana only. Dashboards show trends but do not
rank causes, route ownership, or verify interventions.

### 2. Five friction classes with separate levers

| Class | Primary signal | Lever |
|---|---|---|
| Permission friction | permission events, waits, persisted grants | permission rules, scripts/Make targets |
| Confirmation stalls | `question` calls, end-of-turn questions, short affirmations | autonomy contract, command design |
| Latency | `task` and tool durations, child sessions | model/steps, prompt scope, parallelism |
| Waste | tokens per turn, compactions, duplicate reads/runs | context hygiene, delegation, repo tests |
| Security drift | persisted grants vs role policy, broad allow rules | revoke, split, or narrow rules |

Each finding carries the class so proposals do not mix a behavioral fix with a
policy fix.

### 3. Evidence thresholds and confidence

Defaults: a finding needs at least 7 days and 10 events across 3 sessions.
Latency excludes sessions with wall time above 8 hours or where the tool span
crosses an idle event, to avoid counting overnight sessions as model time.
Rates use prompts per 100 turns and duplicate reads per 1,000 reads so projects
of different sizes are comparable. Confidence is high at 30+ events across 7+
days, medium at 10-29, and low otherwise; low-confidence findings are reported
but not proposed.

### 4. Privacy tiers

- `aggregate` (default): counts, rates, durations, normalized classes only.
- `patterns`: adds canonical command heads such as `git push` and `make test`,
  with arguments, URLs, paths, and environment values removed.
- `snippets`: requires `--allow-content`, warns, and still redacts secrets,
  credentials, tokens, and long encoded values.

The helper never emits message text at `aggregate` or `patterns`. The command
must not read session exports or raw parts unless the user explicitly requests
snippets for a bounded finding.

### 5. Capture belongs in `opencode-metrics`, not a second plugin

The plugin already subscribes to permission events, owns a durable local
database, and already classifies sessions and models. Extending it avoids a
second event subscriber and a second schema. The role owns analysis; the
plugin owns capture. Contract version 1 defines the `permission_contract`
marker, the `permission_events` table, the `v_permission_friction` view,
canonical resource rules, and retention. The helper checks for the table and
contract version and falls back to inferred patterns when absent. The initial
config keys are `permission_capture.enabled`, `permission_capture.retention_days`
(default 90), and `permission_capture.store_raw` (default false).

Alternative rejected: parse tool parts to reconstruct asks. Permission events
are ephemeral and the mapping from a tool call to a prompt is ambiguous,
especially for `always` grants and external-directory checks.

### 6. Proposals are routed, never auto-applied

A finding resolves to one target:

- `role`: safe generic defaults shipped by this role.
- `playbook`: environment-specific overrides for the personal playbook.
- `repo`: repository `AGENTS.md`, deterministic test, task runner, or workflow
  improvement.
- `plugin`: a capture or data-quality change in `opencode-metrics`.

The command presents the proposal with evidence, expected effect, risk, and a
concrete diff or snippet. Creating an OpenSpec change or applying a diff
requires explicit selection and confirmation. No proposal is applied implicitly.

### 7. Intervention ledger and verification

Each accepted proposal can be recorded in
`~/.local/state/opencode/retro/interventions.json` with a baseline window,
target metric, expected direction, and review date. `--verify` compares the
current window with the baseline and recommends keep, revert, or extend. The
ledger stores no consent and no raw session content.

### 8. Autonomy contract

Add to `agent-operating-rules.md`:

- Continue without asking for reversible, in-scope actions that are already
  authorized by the task, including local edits, tests, linters, and reads.
- Stop only for irreversible or destructive actions, remote mutations (push,
  PR/issue/review posting, merges, releases), spending, scope or requirement
  ambiguity, credential handling, or an unavailable mandatory gate.
- Do not end a turn with a rhetorical confirmation for work already requested.
- Batch decisions into one question with options instead of serializing them.
- When blocked, state the blocker and the exact unblocked next action.

### 9. Permission hardening in this change

- Ask for implicit `gh api` writes: field flags (`-f`, `-F`, `--field`,
  `--raw-field`) and `--input`, in addition to the explicit method forms.
- Restrict `git config` to read-only forms (`--get`, `--get-*`, `--list`,
  `-l`, `--show-*`) and ask for all other `git config` invocations.
- Keep the broad-rule audit as a first output of the loop: `git branch`,
  `git checkout`, `git stash`, `git worktree`, `git remote`, and `gh alias`/
  `gh extension` are candidates for a follow-up change, not part of this one.

## Parallel Workstreams

| Stream | Repository | Depends on | Deliverable |
|---|---|---|---|
| A. Contract and capture | `~/GIT/me/opencode-metrics` | none | `permission-capture` spec implemented, contract v1 |
| B. Helper and command | this role | contract v1 shape only | `/session_retro`, scorecard, privacy, proposals |
| C. Interventions and verification | this role | B | ledger schema, `--verify` |
| D. Environment proposals | `~/GIT/mbtech/Ansible/dev_ai.yml` | first B report | approved overrides |
| E. Repository proposals | consumer repositories | first B report | `AGENTS.md`/test improvements |

A can land before or alongside B because the helper tolerates a missing table.
The contract is frozen as version 1 before B integrates against it. C and the
external streams start only after B produces a trustworthy scorecard.

## Risks / Trade-offs

- **Plugin API churn in V2** -> keep capture observer-only, fail open, and
  isolate it in the metrics plugin so a plugin failure cannot block sessions.
- **False positives from noisy sessions** -> thresholds, outlier exclusion,
  and confidence levels; low-confidence findings are not proposed.
- **Privacy leakage** -> aggregate default, canonicalization, secret redaction,
  local-only reports with `0700`/`0600` permissions, and no transcript reads.
- **Permission regression** -> every rule change is a reviewed diff with
  explicit before/after behavior; the loop never auto-grants.
- **Overfitting to a short window** -> intervention verification and
  before/after windows; prefer recurring patterns over one-off events.
- **Analysis cost** -> deterministic helper by default; a scheduled model run
  is optional and bounded to the scorecard.

## Migration

No migration is required. The command and helper are additive and read-only.
The permission rules change only the two documented cases. The metrics plugin
schema is additive; existing databases continue to work and permission history
starts when capture is enabled. Session storage remains untouched.
