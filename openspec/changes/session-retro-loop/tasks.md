## 1. Helper: data collection and scorecard

- [x] 1.1 Create `files/scripts/session_insights.py` with a read-only SQLite
  layer that handles both `message`/`part` and `session_message`/`session_part`
  schemas and opens databases with `mode=ro`.
- [x] 1.2 Implement source adapters for `opencode stats --json`, the
  `opencode-metrics` database, and session storage, including explicit
  missing-source reporting.
- [x] 1.3 Implement the five finding classes: permission friction,
  confirmation stalls, subagent/tool latency, token and context waste, and
  permission-policy drift.
- [x] 1.4 Implement canonical command normalization and path classes, including
  removal of assignments, quoting, URLs, paths, and secret-bearing values.
- [x] 1.5 Implement evidence thresholds, outlier exclusion, rates per 100 turns
  and per 1,000 reads, and high/medium/low confidence.
- [x] 1.6 Implement the JSON scorecard schema and a markdown renderer with the
  window, sources, coverage, findings, evidence, expected effect, risk, and
  proposal target.
- [x] 1.7 Implement the `aggregate`, `patterns`, and `snippets` detail levels;
  require `--allow-content` for snippets and redact secrets at every level.
- [x] 1.8 Implement private report output under
  `${XDG_STATE_HOME:-~/.local/state}/opencode/retro/reports/` with `0700`
  directories and `0600` files.
- [x] 1.9 Implement the intervention ledger and `--verify` comparison against a
  baseline window, including the insufficient-data outcome.

## 2. Command

- [x] 2.1 Create `files/commands/session_retro.md` with frontmatter, arguments,
  preflight checks, helper invocation, scorecard presentation, proposal
  selection, and explicit confirmation boundaries.
- [x] 2.2 Define the proposal routing rules for role defaults, personal
  playbook, repository guidance/tests, and the metrics plugin.
- [x] 2.3 Ensure the command never reads session exports or raw parts unless the
  user requests snippets for a bounded finding.
- [x] 2.4 Ensure the command can create an OpenSpec change only after explicit
  approval and only in the selected repository.
- [x] 2.5 Add a `Next Steps` pointer from `workflow_next` clean-state output to
  `/session_retro` when a retrospective is due, without changing the priority
  ladder.

## 3. Permission hardening

- [x] 3.1 Add ask rules for implicit `gh api` writes: `-f`, `-F`, `--field`,
  `--raw-field`, and `--input`, after the `gh *` allow rule.
- [x] 3.2 Replace the broad `git config *` allow rule with read-only forms and
  an ask rule for all other `git config` invocations, preserving last-match-wins
  ordering.
- [x] 3.3 Add a short comment explaining why the new rules must follow the broad
  allow rules.

## 4. Autonomy contract

- [x] 4.1 Add the continue/stop conditions, anti-rhetorical-confirmation rule,
  and decision batching to `files/agent-operating-rules.md`.
- [x] 4.2 Review shipped commands for text that invites unnecessary
  confirmation and align them with the contract where it does not weaken a
  mandatory gate.

## 5. Tests and documentation

- [x] 5.1 Add `tests/test_session_insights.py` with synthetic legacy and V2
  session schemas, a synthetic metrics database, synthetic permission events,
  and intervention records.
- [x] 5.2 Cover redaction, thresholds, source degradation, canonicalization,
  and keep/revert/extend verification in the unit tests.
- [x] 5.3 Extend `tests/test.yml` to assert command and helper deployment,
  modes, autonomy-contract content, and permission rule ordering.
- [x] 5.4 Add the new test target to `Makefile` and include it in `make test`.
- [x] 5.5 Document `/session_retro`, privacy levels, proposal targets,
  intervention verification, and the hardened rules in `README.md`.
- [x] 5.6 Run `make test`, `make lint`, and `openspec validate
  session-retro-loop --strict`.

## 6. Parallel: opencode-metrics permission capture

External repository: `~/GIT/me/opencode-metrics`.

- [x] 6.1 Create an OpenSpec change in `opencode-metrics` from the
  `permission-capture` capability in this change.
- [x] 6.2 Add the version-1 permission event table, unique permission
  identifier, upsert behavior, and contract version marker.
- [x] 6.3 Persist asked/replied timestamps, action, canonical resource, salted
  hash, reply, save patterns, source tool/message, project, agent, and model.
- [x] 6.4 Implement canonicalization and redaction at capture time; keep raw
  resources disabled by default.
- [x] 6.5 Add the friction view with prompt count, median/p95 wait, always and
  reject counts, and first/last seen.
- [x] 6.6 Add retention cleanup (default 90 days), the disable switch, and
  owner-only database permissions.
- [x] 6.7 Add tests for ingestion, duplicates, late replies, redaction,
  retention, the view, and fail-open behavior.
- [x] 6.8 Document the contract, table and view names, sanitization, retention,
  and the no-backfill limitation.
- [x] 6.9 Release the plugin and record the minimum contract version the role
  helper can consume.

## 7. Parallel: environment and repository proposals

These tasks consume the first trustworthy scorecard; they do not block the
helper or the plugin.

- [x] 7.1 Run `/session_retro --days 30` in the main working environment and
  review the first scorecard.
- [x] 7.2 Apply approved environment-specific overrides to
  `~/GIT/mbtech/Ansible/dev_ai.yml` in a separate change.
- [x] 7.3 For each repository-level finding, create a scoped proposal for the
  identified `AGENTS.md`, deterministic test, task runner, or workflow change.
- [ ] 7.4 Record accepted interventions in the ledger with baseline windows and
  review dates.
- [ ] 7.5 Re-run verification after the review date and keep, revert, or extend
  each intervention based on the measured result.
