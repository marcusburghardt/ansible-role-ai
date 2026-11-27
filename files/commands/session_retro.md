---
description: "Measure local session friction and propose evidence-based configuration changes"
---

# Session Retro

Measure permission friction, confirmation stalls, subagent and tool latency,
token and context waste, and permission-policy drift. The helper reads local
stores only, emits aggregate data by default, and never applies a change. It does
not require a repository workflow framework and is safe to run from any
directory.

## Arguments

- **Day window** (optional): `--days <N>`. Defaults to `30` and must be at
  least `1`.
- **Project filter** (optional): `--project <path-or-name>`. Defaults to the
  current repository name. The report shows only the basename, never the full
  path.
- **Detail level** (optional): `--detail aggregate|patterns|snippets`. Defaults
  to `aggregate`.
- **Verification mode** (optional): `--verify` with `--id <intervention-id>`.
  Compares a recorded intervention with its baseline window.
- **Content consent** (optional): `--allow-content`. Required before the helper
  will emit the `snippets` detail level.

## Execution Steps

### 1. Preflight

Resolve the deployed helper without assuming a repository layout:

```bash
HELPER="${XDG_BIN_HOME:-$HOME/bin}/session_insights.py"
test -x "$HELPER" || { echo "session_insights.py is not deployed; run the ansible-role-ai configure_opencode task."; exit 1; }
python3 --version
```

Require Python 3.10 or newer and an executable helper. Do not install packages
or contact the network. If the helper is missing, stop and report the exact
remediation; do not substitute a model-generated analysis.

### 2. Parse arguments and resolve defaults

- `DAYS` defaults to `30`.
- `DETAIL` defaults to `aggregate`.
- `PROJECT` defaults to the basename of the current repository
  (`git rev-parse --show-toplevel` when available, otherwise the current
  directory). Pass a user-supplied value through unchanged; the helper reduces
  it to a basename in output.
- Reject `--detail snippets` unless the user also passed `--allow-content` and
  explicitly asked for snippets for a bounded finding.
- `--verify` switches to the verification path in Step 8.

### 3. Run the deterministic helper

For a scorecard:

```bash
"$HELPER" analyze --days "$DAYS" --detail "$DETAIL" ${PROJECT:+--project "$PROJECT"}
```

For machine-readable output, add `--json`. The helper writes the JSON and
markdown report under
`${XDG_STATE_HOME:-$HOME/.local/state}/opencode/retro/reports/` with private
permissions. Call the helper once per requested window; do not re-run it for
each finding.

### 4. Present the scorecard

Show the analysis window, the sources used with their status, any missing or
degraded source notices, the session and turn coverage, and the normalized
rates. Then present one row per finding class:

| Class | Events | Sessions | Confidence | Proposable | Target |
|---|---|---|---|---|---|

- High confidence means at least 30 events over at least 7 days; medium means
  10-29; low means fewer than 10 events, fewer than 3 sessions, or fewer than 7
  observed days.
- Report low-confidence findings but do not turn them into proposals.
- If no finding is proposable, say explicitly that the result is clean and do
  not invent a recommendation.

### 5. Select proposals

List only the proposable findings, numbered, with target, expected effect, and
risk. Ask one batched decision using the `question` tool:

- which findings to turn into proposals,
- whether to show redacted snippets for one bounded finding,
- whether to record an intervention,
- or stop with no change.

Do not serialize these into separate confirmations. Do not edit anything before
an explicit selection.

### 6. Escalate detail only on request

The command never opens session exports, raw parts, transcripts, or the SQLite
tables directly. If the user asks for snippets for a bounded finding, re-run the
helper with the same window and project:

```bash
"$HELPER" analyze --days "$DAYS" --detail snippets --allow-content ${PROJECT:+--project "$PROJECT"}
```

Warn that snippets may contain sensitive context. Even then, credentials,
tokens, private keys, URLs, and long encoded values are redacted by the helper.

### 7. Draft proposals for selected findings

Each proposal must declare exactly one target and show evidence, expected
effect, risk, and a concrete diff or snippet. Do not apply the proposal in this
step.

- **Role defaults:** a generic, safe change in this role's defaults or
  `vars/configure_opencode.yml`. Show the exact rule or setting and its
  before/after behavior.
- **Personal playbook:** an environment-specific override for the user's
  playbook (for example a model route or a host-specific path). Show the
  override snippet; do not edit the playbook from this command.
- **Repository:** a concrete `AGENTS.md`, deterministic test, Make target, or
  workflow change in the repository named by the finding. Show the file and the
  proposed change.
- **Metrics plugin:** a capture or data-quality change in `opencode-metrics`,
  referencing contract version `1` and the `permission-capture` capability.

Creating an OpenSpec change is allowed only after explicit approval and only in
the selected repository. If the user has not selected a repository, ask which
one. Never create a change in a repository that was not selected.

### 8. Record an accepted intervention

When the user accepts an intervention, record its baseline and review date. Use
the scorecard's metric snapshot for the baseline value:

```bash
INTERVENTION_FILE="$(mktemp)"
cat > "$INTERVENTION_FILE" <<'JSON'
{
  "target": "role",
  "change_ref": "openspec/changes/<change-name>",
  "hypothesis": "<what should improve and why>",
  "metric": "permission_prompts",
  "baseline": {
    "start": "<window start>",
    "end": "<window end>",
    "value": 0,
    "sessions": 0
  },
  "expected_direction": "decrease",
  "review_date": "YYYY-MM-DD"
}
JSON
"$HELPER" record --file "$INTERVENTION_FILE"
rm -f "$INTERVENTION_FILE"
```

Replace the placeholder values with the actual scorecard window and metric. The
ledger stores no consent and no raw session content.

### 9. Verification mode

With `--verify`, run:

```bash
"$HELPER" verify ${INTERVENTION_ID:+--id "$INTERVENTION_ID"} --days "$DAYS" ${PROJECT:+--project "$PROJECT"}
```

Present the baseline value, current value, percent change, the expected
direction, and the recommendation (`keep`, `revert`, or `extend`). When the
helper reports `insufficient-data`, state that success or failure cannot be
claimed and recommend extending the window; do not speculate.

## Proposal Routing

| Finding class | Default target | Typical lever |
|---|---|---|
| Permission friction | role, or playbook for user-specific paths | narrow allow rule, script, Make target |
| Confirmation stalls | role | autonomy contract, command design |
| Latency | playbook | prompt scope, splitting work, model routing |
| Waste | role or repository | context hygiene, deterministic test target |
| Permission-policy drift | role, or playbook for user-specific paths | revoke, split, or narrow grants |

## Confirmation Boundaries

- Reading local data and drafting a proposal are reversible and in scope.
- Applying a rule, editing a repository, installing a hook, creating an
  OpenSpec change, pushing, opening a pull request, or posting a review
  requires explicit user selection and confirmation.
- Silence is not consent. Never auto-grant a permission or auto-apply a diff.
- The report is advisory. The system remains unchanged unless a later,
  explicitly approved change is made.

## Output Format

```markdown
## Session Retrospective

**Window:** <start> to <end> (<days> days) | **Project:** <basename> | **Detail:** <level>

### Sources
<source table with status and coverage; call out missing or degraded sources>

### Coverage
<sessions, turns, tool calls, reads, observed days, normalized rates>

### Findings
<one row per class: events, sessions, confidence, proposable, target, note>

### Proposals
<only proposable findings; evidence, expected effect, risk, target, diff/snippet>

### Next Step
<one batched choice: draft a selected proposal, show bounded snippets, record an
intervention, verify an intervention, or stop>
```
