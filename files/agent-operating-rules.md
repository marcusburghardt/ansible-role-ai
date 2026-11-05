# Agent Operating Rules: Context and Tools

These rules keep sessions fast, predictable, and affordable. They apply to
every task. Repository-level rules still take precedence on conflicts.

## Context budget

- Treat roughly **150,000 tokens of context** or **100 assistant turns** as a
  checkpoint. Past that point every turn re-sends the whole transcript and
  cost grows much faster than progress.
- At a checkpoint: summarise the objective, current state, decisions, and
  remaining work; write it to a handoff or task file; then tell the user to
  continue in a **fresh session** from that handoff.
- Prefer several focused sessions over one very long one.
- Keep exploration in subagents. Their reports become part of the parent
  transcript, so ask for conclusions and file references, not full files.
- Do not paste large file contents into the conversation. Read the ranges
  needed and quote only what matters.
- Do not re-read files or re-run commands whose result is already present in
  the conversation.

## Shell commands

- Always set an explicit `timeout` on shell commands: **120s by default**,
  **600s maximum**. Raise it only for a known long build, and say why.
- Never run interactive or indefinitely blocking commands: no `--watch`, no
  `tail -f`, no `watch`, no `sleep`-based polling, no editors, no prompts.
- Poll remote state with short, separate calls (for example `gh pr checks`
  once per call) instead of a blocking follow.
- Prefer the dedicated `read`, `grep`, `glob`, and `edit` tools over shell
  equivalents. They are cheaper and permission-friendly.
- Keep commands single-purpose. Compound lines (`a && b; c`) are parsed and
  permission-checked per command, so every part can trigger its own prompt.

## Delegation

- One subagent call should do one bounded unit of work. If a task would need
  more than about 100 turns, split it and sequence the parts.
- Give the subagent the files, constraints, and acceptance criteria it needs
  so it does not rediscover them.
- Ask for a short report: what changed, what was verified, what remains.

## When something stalls

- If a command produces no output for longer than its timeout, stop and
  report the command and the error instead of retrying it unchanged.
- If the same tool call fails three times, change approach or ask the user.
