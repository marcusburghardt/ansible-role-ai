#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Deterministic, read-only retrospective scorecard for OpenCode sessions.

The helper reads three local sources: ``opencode stats --json``, the
``opencode-metrics`` database, and read-only aggregates over OpenCode session
storage. It never writes to those databases and never emits raw prompts,
message text, paths, or command arguments at the default detail level.

Only the Python standard library is used, and no network access is performed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sqlite3
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

SCHEMA = "session-insights/v1"
LEDGER_SCHEMA = "session-insights-ledger/v1"

MIN_DAYS = 7.0
MIN_EVENTS = 10
MIN_SESSIONS = 3
HIGH_EVENTS = 30
MAX_SESSION_WALL_SECONDS = 8 * 60 * 60
MAX_TOOL_SPAN_SECONDS = 60 * 60
DETAIL_LEVELS = ("aggregate", "patterns", "snippets")

RISKY_COMMAND_HEADS = frozenset(
    {
        "chmod",
        "chown",
        "dd",
        "git config",
        "git push",
        "git reset",
        "git rm",
        "gh api",
        "rm",
        "sudo",
    }
)

SYSTEM_DIRS = frozenset({"boot", "etc", "proc", "sys", "usr", "var"})
SHELL_TOOL_NAMES = frozenset({"bash", "shell", "Bash", "Shell"})
READ_TOOL_NAMES = frozenset({"read", "read_file", "Read", "ReadFile"})
TASK_TOOL_NAMES = frozenset({"task", "Task", "subagent", "Subagent"})

ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SAFE_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")

PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
URL_CREDENTIALS_RE = re.compile(r"(https?://)[^/@\s]+@")
AUTH_HEADER_RE = re.compile(
    r"(?i)((?:authorization|proxy-authorization)\s*[:=]\s*)(?:bearer\s+|basic\s+)?\S+"
)
BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
TOKEN_RE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,}"
    r"|sk-[A-Za-z0-9_-]{8,}|xox[baprs]-[A-Za-z0-9-]{8,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{12,})\b"
)
SECRET_FLAG_RE = re.compile(
    r"(?i)(--?(?:password|passwd|token|secret|api-key|apikey|auth)\s*[= ]\s*)\S+"
)
ENV_SECRET_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|KEY|CREDENTIAL)[A-Z0-9_]*)="
    r"[^\s]+"
)
LONG_ENCODED_RE = re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b")
WHITESPACE_RE = re.compile(r"\s+")


def utc_now() -> datetime:
    """Return the current time in UTC."""
    return datetime.now(timezone.utc)


def to_ms(value: Any) -> int | None:
    """Normalize seconds or milliseconds to integer milliseconds."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    if number < 100_000_000_000:
        number *= 1000
    return int(number)


def iso_from_ms(value: int | None) -> str | None:
    """Render milliseconds since the epoch as an ISO-8601 UTC timestamp."""
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp, accepting a trailing ``Z``."""
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def percentile(values: list[float], fraction: float) -> float | None:
    """Return a linearly interpolated percentile for a small sample."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def redact(value: str | None) -> str:
    """Remove credentials, tokens, and long encoded values from text."""
    if not value:
        return ""
    text = str(value)
    text = PRIVATE_KEY_RE.sub("[REDACTED:private-key]", text)
    text = URL_CREDENTIALS_RE.sub(r"\1[REDACTED]@", text)
    text = AUTH_HEADER_RE.sub(r"\1[REDACTED]", text)
    text = BEARER_RE.sub("Bearer [REDACTED]", text)
    text = TOKEN_RE.sub("[REDACTED]", text)
    text = SECRET_FLAG_RE.sub(r"\1[REDACTED]", text)
    text = ENV_SECRET_RE.sub(r"\1=[REDACTED]", text)
    text = LONG_ENCODED_RE.sub("[REDACTED]", text)
    return text


def canonical_command(command: str | None) -> str:
    """Reduce a shell command to its head and at most one safe token.

    Assignments, quoting, URLs, paths, environment values, and secrets are
    removed before the first simple command segment is tokenized.
    """
    if not command:
        return "unknown"
    text = redact(command).strip()
    first_segment = re.split(r"\s*(?:&&|\|\||[;|])\s*", text, maxsplit=1)[0]
    try:
        tokens = shlex.split(first_segment)
    except ValueError:
        tokens = first_segment.split()
    if not tokens:
        return "unknown"
    while tokens and ASSIGNMENT_RE.match(tokens[0]):
        tokens.pop(0)
    if tokens and tokens[0] in {"command", "env", "nice", "time"}:
        tokens.pop(0)
        while tokens and ASSIGNMENT_RE.match(tokens[0]):
            tokens.pop(0)
    if not tokens:
        return "unknown"
    head = redact(Path(tokens[0]).name)
    if not head or head in {".", ".."}:
        return "unknown"
    for token in tokens[1:]:
        candidate = token.strip("\"'")
        if SAFE_TOKEN_RE.match(candidate) and "." not in candidate:
            return f"{head} {candidate}"
    return head


def path_class(raw_path: str | None) -> tuple[str, str]:
    """Return a coarse path class and extension without revealing the path."""
    if not raw_path:
        return "unknown", "none"
    path = raw_path.strip()
    home = str(Path.home())
    if path.startswith("~"):
        group = "home"
    elif path.startswith(home + os.sep) or path == home:
        group = "home"
    elif path == "/tmp" or path.startswith("/tmp/"):
        group = "tmp"
    elif path.startswith("/"):
        first = path.split("/", 2)[1]
        group = "system" if first in SYSTEM_DIRS else "external"
    else:
        group = "project"
    extension = Path(path).suffix.lower() or "none"
    return group, extension


def path_key(raw_path: str | None) -> str:
    """Normalize a path for internal duplicate detection only.

    The key is never emitted. It must distinguish different files in the same
    directory and with the same extension, unlike the coarse path class.
    """
    if not raw_path:
        return "unknown"
    text = raw_path.strip()
    if text.startswith("~"):
        text = str(Path.home()) + text[1:]
    return os.path.normpath(text)


def file_pattern(action: str, raw_path: str | None) -> str:
    """Build a path-class resource label for a file permission."""
    group, extension = path_class(raw_path)
    return f"{action}:{group}:{extension}"


def confidence_level(events: int, sessions: int, days: float) -> str:
    """Return high, medium, or low confidence for a finding."""
    if days < MIN_DAYS or sessions < MIN_SESSIONS or events < MIN_EVENTS:
        return "low"
    if events >= HIGH_EVENTS:
        return "high"
    return "medium"


def is_proposable(events: int, sessions: int, days: float) -> bool:
    """Return whether a finding clears every threshold for a proposal."""
    return (
        events >= MIN_EVENTS
        and sessions >= MIN_SESSIONS
        and days >= MIN_DAYS
        and confidence_level(events, sessions, days) != "low"
    )


def model_label(raw: Any) -> str:
    """Render an OpenCode model field as ``provider/model#variant``."""
    if not raw:
        return "unknown"
    if isinstance(raw, dict):
        payload = raw
    else:
        try:
            payload = json.loads(str(raw))
        except (TypeError, json.JSONDecodeError):
            return str(raw)
    if not isinstance(payload, dict):
        return str(raw)
    provider = payload.get("providerID") or payload.get("provider") or ""
    model = payload.get("id") or payload.get("modelID") or ""
    label = "/".join(part for part in (provider, model) if part) or str(raw)
    variant = payload.get("variant")
    return f"{label}#{variant}" if variant else label


def observed_days(timestamps: list[int]) -> float:
    """Return the observed span in days for the supplied timestamps."""
    if not timestamps:
        return 0.0
    span_ms = max(timestamps) - min(timestamps)
    return round(span_ms / 86_400_000, 2)


def state_root() -> Path:
    """Return the private retrospective state directory."""
    override = os.environ.get("SESSION_INSIGHTS_STATE_HOME")
    if override:
        return Path(override)
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state) / "opencode" / "retro"
    return Path.home() / ".local" / "state" / "opencode" / "retro"


def reports_root() -> Path:
    """Return the private report directory."""
    return state_root() / "reports"


def ledger_path() -> Path:
    """Return the intervention ledger path."""
    return state_root() / "interventions.json"


def opencode_db_path() -> Path:
    """Return the OpenCode session database path."""
    override = os.environ.get("SESSION_INSIGHTS_OPENCODE_DB")
    if override:
        return Path(override)
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "opencode" / "opencode.db"
    return Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def metrics_db_path() -> Path:
    """Return the opencode-metrics database path."""
    override = os.environ.get("SESSION_INSIGHTS_METRICS_DB")
    if override:
        return Path(override)
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "opencode-metrics" / "metrics.db"
    return Path.home() / ".local" / "share" / "opencode-metrics" / "metrics.db"


def ensure_private_dir(path: Path) -> None:
    """Create a directory with owner-only permissions."""
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def write_private(path: Path, content: str) -> None:
    """Write a file with owner-only permissions, replacing it atomically."""
    ensure_private_dir(path.parent)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        os.fchmod(handle, 0o600)
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def open_readonly(path: Path) -> sqlite3.Connection | None:
    """Open a SQLite database read-only, or return None when unavailable."""
    if not path.exists():
        return None
    uri = "file:" + quote(str(path), safe="/:") + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=5)
    except sqlite3.Error:
        return None
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def table_names(connection: sqlite3.Connection) -> set[str]:
    """Return the table names in a database."""
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
    )
    return {row[0] for row in rows}


def table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    """Return the column names for a table."""
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def chunks(values: list[str], size: int = 500) -> list[list[str]]:
    """Split a list into fixed-size chunks for SQL placeholders."""
    return [values[index : index + size] for index in range(0, len(values), size)]


def source(name: str, status: str, detail: str = "", **coverage: Any) -> dict[str, Any]:
    """Build a source report entry."""
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "coverage": coverage,
    }


def load_stats() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Load ``opencode stats --json`` from a file or the CLI."""
    stats_file = os.environ.get("SESSION_INSIGHTS_STATS_FILE")
    try:
        if stats_file:
            payload = json.loads(Path(stats_file).read_text(encoding="utf-8"))
        else:
            completed = subprocess.run(
                ["opencode", "stats", "--json"],
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            if completed.returncode != 0:
                return None, source(
                    "stats",
                    "error",
                    f"opencode stats exited {completed.returncode}",
                )
            payload = json.loads(completed.stdout)
    except FileNotFoundError:
        return None, source("stats", "missing", "opencode CLI not found")
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as error:
        return None, source("stats", "error", f"could not read stats: {error}")
    coverage = {
        "sessions": payload.get("sessions"),
        "prompts": payload.get("prompts"),
        "tool_calls": (payload.get("tools") or {}).get("totals", {}).get("calls"),
    }
    return payload, source("stats", "ok", "opencode stats --json", **coverage)


def load_sessions(
    connection: sqlite3.Connection,
    since_ms: int,
    until_ms: int,
    project_filter: str | None,
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    """Load sessions from both legacy and V2 session tables."""
    sessions: dict[str, dict[str, Any]] = {}
    present: list[str] = []
    warnings: list[str] = []
    wanted = [
        "id",
        "project_id",
        "parent_id",
        "directory",
        "time_created",
        "time_updated",
        "agent",
        "model",
        "cost",
        "tokens_input",
        "tokens_output",
        "tokens_reasoning",
        "tokens_cache_read",
        "tokens_cache_write",
    ]
    needle = (project_filter or "").lower()
    for table in ("session", "session_v2"):
        if table not in table_names(connection):
            continue
        present.append(table)
        available = table_columns(connection, table)
        columns = [column for column in wanted if column in available]
        selected = ", ".join(columns)
        query = (
            f"SELECT {selected} FROM {table} "
            "WHERE time_updated >= ? AND time_created <= ?"
        )
        try:
            rows = connection.execute(query, (since_ms, until_ms)).fetchall()
        except sqlite3.Error as error:
            warnings.append(f"{table}: {error}")
            continue
        for row in rows:
            record = {column: row[column] for column in columns}
            directory = record.get("directory") or ""
            if needle and needle not in directory.lower():
                continue
            session_id = record.get("id")
            if not session_id or session_id in sessions:
                continue
            sessions[session_id] = {
                "id": session_id,
                "project_id": record.get("project_id"),
                "parent_id": record.get("parent_id"),
                "directory": directory,
                "time_created": int(record.get("time_created") or 0),
                "time_updated": int(record.get("time_updated") or 0),
                "agent": record.get("agent") or "unknown",
                "model": record.get("model") or "unknown",
                "cost": float(record.get("cost") or 0.0),
                "tokens_input": int(record.get("tokens_input") or 0),
                "tokens_output": int(record.get("tokens_output") or 0),
                "tokens_reasoning": int(record.get("tokens_reasoning") or 0),
                "tokens_cache_read": int(record.get("tokens_cache_read") or 0),
                "tokens_cache_write": int(record.get("tokens_cache_write") or 0),
                "source": table,
            }
    return sessions, present, warnings


def parse_tool_payload(
    session_id: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    """Parse a tool payload from a legacy part, V2 part, or message content."""
    if payload.get("type") != "tool":
        return None
    state = payload.get("state") or {}
    data = state.get("input") if isinstance(state.get("input"), dict) else {}
    time_data = state.get("time") or payload.get("time") or {}
    start = to_ms(
        time_data.get("start")
        or time_data.get("created")
        or (payload.get("time") or {}).get("created")
    )
    end = to_ms(
        time_data.get("end")
        or time_data.get("completed")
        or time_data.get("ran")
        or (payload.get("time") or {}).get("completed")
    )
    return {
        "session_id": session_id,
        "call_id": payload.get("id") or payload.get("callID") or payload.get("call_id"),
        "name": payload.get("tool") or payload.get("name") or "unknown",
        "status": state.get("status") or "",
        "start": start,
        "end": end,
        "command": data.get("command"),
        "path": data.get("path") or data.get("filePath") or data.get("file"),
    }


def parse_tool_part(session_id: str, raw: str) -> dict[str, Any] | None:
    """Parse a legacy or V2 tool part into a common shape."""
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return parse_tool_payload(session_id, payload)


def load_tool_calls(
    connection: sqlite3.Connection, session_ids: list[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Load tool calls from legacy, V2 part, and V2 message-content storage."""
    calls: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[tuple[Any, ...]] = set()
    if not session_ids:
        return calls, warnings
    tables = table_names(connection)

    def add(call: dict[str, Any] | None) -> None:
        if not call:
            return
        key = (
            call["session_id"],
            call.get("call_id") or call["name"],
            call["start"],
            call["end"],
            call["name"],
        )
        if key in seen:
            return
        seen.add(key)
        calls.append(call)

    for group in chunks(session_ids):
        placeholders = ",".join("?" for _ in group)
        if "part" in tables:
            try:
                rows = connection.execute(
                    f"SELECT session_id, data FROM part WHERE session_id IN ({placeholders})",
                    group,
                )
                for row in rows:
                    add(parse_tool_part(row["session_id"], row["data"]))
            except sqlite3.Error as error:
                warnings.append(f"part: {error}")
        if "session_part" in tables:
            try:
                rows = connection.execute(
                    "SELECT session_id, data FROM session_part "
                    f"WHERE type = 'tool' AND session_id IN ({placeholders})",
                    group,
                )
                for row in rows:
                    add(parse_tool_part(row["session_id"], row["data"]))
            except sqlite3.Error as error:
                warnings.append(f"session_part: {error}")
        if "session_message" in tables:
            # Some V2 sessions have no session_part rows; tool calls live in
            # the assistant message content. Extract only tool items so large
            # transcripts are never loaded into Python.
            try:
                rows = connection.execute(
                    "SELECT m.session_id AS session_id, je.value AS item "
                    "FROM session_message m, json_each("
                    "CASE WHEN json_valid(m.data) THEN m.data ELSE '{}' END, "
                    "'$.content') je "
                    "WHERE m.type = 'assistant' "
                    "AND json_extract(je.value, '$.type') = 'tool' "
                    f"AND m.session_id IN ({placeholders})",
                    group,
                )
                for row in rows:
                    try:
                        item = json.loads(row["item"])
                    except (TypeError, json.JSONDecodeError):
                        continue
                    if isinstance(item, dict):
                        add(parse_tool_payload(row["session_id"], item))
            except sqlite3.Error as error:
                warnings.append(f"session_message: {error}")
    return calls, warnings


def load_idle_events(
    connection: sqlite3.Connection, session_ids: list[str]
) -> dict[str, list[int]]:
    """Return idle event timestamps per session for latency exclusion."""
    idle: dict[str, list[int]] = defaultdict(list)
    if not session_ids or "session_message" not in table_names(connection):
        return idle
    for group in chunks(session_ids):
        placeholders = ",".join("?" for _ in group)
        rows = connection.execute(
            "SELECT session_id, time_created FROM session_message "
            f"WHERE type = 'idle' AND session_id IN ({placeholders})",
            group,
        )
        for row in rows:
            idle[row["session_id"]].append(int(row["time_created"]))
    return idle


def load_grants(
    connection: sqlite3.Connection,
) -> tuple[list[dict[str, Any]], str | None]:
    """Load persisted permission grants from the OpenCode database."""
    tables = table_names(connection)
    if "permission" not in tables:
        return [], "permission table absent"
    columns = table_columns(connection, "permission")
    has_project = "project" in tables
    selected = [
        f"permission.{column} AS {column}"
        for column in (
            "id",
            "action",
            "resource",
            "time_created",
            "time_updated",
        )
        if column in columns
    ]
    join = ""
    if has_project:
        project_columns = [
            column
            for column in ("id", "name", "worktree")
            if column in table_columns(connection, "project")
        ]
        join = " LEFT JOIN project p ON p.id = permission.project_id"
        selected.append("p.id AS project_id")
        selected.extend(
            f"p.{column} AS project_{column}"
            for column in project_columns
            if column != "id"
        )
    elif "project_id" in columns:
        selected.append("permission.project_id AS project_id")
    query = f"SELECT {', '.join(selected)} FROM permission{join}"
    try:
        rows = connection.execute(query).fetchall()
    except sqlite3.Error as error:
        return [], f"permission table unreadable: {error}"
    grants = [dict(row) for row in rows]
    return grants, None


def load_permission_events(
    connection: sqlite3.Connection, since_ms: int
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Load contract-v1 permission events, reporting missing or unsupported."""
    tables = table_names(connection)
    if "permission_contract" not in tables:
        return None, "permission_contract table absent"
    contract_columns = table_columns(connection, "permission_contract")
    version_column = next(
        (
            column
            for column in ("version", "contract_version", "value")
            if column in contract_columns
        ),
        None,
    )
    if not version_column:
        return None, "permission contract version column absent"
    try:
        row = connection.execute(
            f"SELECT {version_column} AS version FROM permission_contract LIMIT 1"
        ).fetchone()
    except sqlite3.Error as error:
        return None, f"permission contract unreadable: {error}"
    if row is None:
        return None, "permission contract marker empty"
    try:
        version = int(row["version"])
    except (TypeError, ValueError):
        return None, "permission contract version is not an integer"
    if version != 1:
        return None, f"unsupported permission contract version {version}"
    if "permission_events" not in tables:
        return None, "permission_events table absent"
    columns = table_columns(connection, "permission_events")
    selected = [
        column
        for column in (
            "permission_id",
            "session_id",
            "project_id",
            "agent",
            "model",
            "action",
            "resource_hash",
            "reply",
            "asked_at",
            "replied_at",
            "wait_ms",
            "source_tool",
            "source_message_id",
            "contract_version",
            "raw_resource",
        )
        if column in columns
    ]
    # Contract v1 permits either a canonical_resource column or a generic
    # resource column; accept both shapes without parsing unknown fields.
    resource_column = (
        "canonical_resource"
        if "canonical_resource" in columns
        else "resource"
        if "resource" in columns
        else None
    )
    if resource_column:
        selected.append(f"{resource_column} AS canonical_resource")
    save_column = (
        "save_pattern"
        if "save_pattern" in columns
        else "save_patterns"
        if "save_patterns" in columns
        else None
    )
    if save_column:
        selected.append(f"{save_column} AS save_pattern")
    timestamp_column = "asked_at" if "asked_at" in columns else None
    if not timestamp_column:
        return None, "permission_events asked_at column absent"
    try:
        rows = connection.execute(
            f"SELECT {', '.join(selected)} FROM permission_events WHERE asked_at >= ?",
            (since_ms,),
        ).fetchall()
    except sqlite3.Error as error:
        return None, f"permission_events unreadable: {error}"
    events = []
    for row in rows:
        record = dict(row)
        record["asked_at"] = to_ms(record.get("asked_at"))
        record["replied_at"] = to_ms(record.get("replied_at"))
        if record.get("wait_ms") is not None:
            try:
                record["wait_ms"] = float(record["wait_ms"])
            except (TypeError, ValueError):
                record["wait_ms"] = None
        events.append(record)
    return events, None


def load_metrics(
    path: Path, since_ms: int, project_filter: str | None
) -> tuple[dict[str, dict[str, Any]] | None, dict[str, Any], list[str]]:
    """Load per-session metrics from the opencode-metrics database."""
    connection = open_readonly(path)
    if connection is None:
        return None, source("metrics", "missing", f"{path} not found"), []
    warnings: list[str] = []
    try:
        tables = table_names(connection)
        if "sessions" not in tables or "measurements" not in tables:
            return (
                None,
                source("metrics", "degraded", "sessions or measurements table absent"),
                warnings,
            )
        columns = table_columns(connection, "sessions")
        selected = [
            column
            for column in (
                "session_id",
                "project_id",
                "agent",
                "model",
                "started_at",
                "ended_at",
                "parent_session_id",
            )
            if column in columns
        ]
        rows = connection.execute(
            f"SELECT {', '.join(selected)} FROM sessions"
        ).fetchall()
        needle = (project_filter or "").lower()
        sessions: dict[str, dict[str, Any]] = {}
        for row in rows:
            ended = to_ms(row["ended_at"]) if "ended_at" in columns else None
            started = to_ms(row["started_at"]) if "started_at" in columns else None
            if (ended or started or 0) < since_ms:
                continue
            session_id = row["session_id"]
            sessions[session_id] = {
                "session_id": session_id,
                "project_id": row["project_id"] if "project_id" in columns else None,
                "agent": row["agent"] if "agent" in columns else "unknown",
                "model": row["model"] if "model" in columns else "unknown",
                "started_at": started,
                "ended_at": ended,
                "metrics": {},
                "project": "",
            }
        project_names: dict[str, str] = {}
        if "projects" in tables:
            project_columns = table_columns(connection, "projects")
            selected_projects = [
                column
                for column in ("project_id", "name", "worktree")
                if column in project_columns
            ]
            for row in connection.execute(
                f"SELECT {', '.join(selected_projects)} FROM projects"
            ):
                project_names[row["project_id"]] = (
                    row["name"] if "name" in selected_projects else ""
                ) or (row["worktree"] if "worktree" in selected_projects else "")
        for session in sessions.values():
            session["project"] = project_names.get(session["project_id"] or "", "")
        if needle:
            sessions = {
                session_id: session
                for session_id, session in sessions.items()
                if needle in (session["project"] or "").lower()
            }
        if sessions:
            for group in chunks(list(sessions)):
                placeholders = ",".join("?" for _ in group)
                measurements = connection.execute(
                    "SELECT session_id, metric_name, value FROM measurements "
                    f"WHERE session_id IN ({placeholders})",
                    group,
                )
                for row in measurements:
                    if row["session_id"] in sessions:
                        sessions[row["session_id"]]["metrics"][row["metric_name"]] = (
                            float(row["value"] or 0.0)
                        )
        return (
            sessions,
            source(
                "metrics",
                "ok",
                path.name,
                sessions=len(sessions),
                measurements=sum(len(item["metrics"]) for item in sessions.values()),
            ),
            warnings,
        )
    finally:
        connection.close()


def metric_total(sessions: dict[str, dict[str, Any]], name: str) -> float:
    """Sum a metric across sessions."""
    return sum(session["metrics"].get(name, 0.0) for session in sessions.values())


def metric_map(sessions: dict[str, dict[str, Any]], name: str) -> dict[str, float]:
    """Return per-session values for one metric."""
    return {
        session_id: session["metrics"][name]
        for session_id, session in sessions.items()
        if name in session["metrics"]
    }


def finding(
    class_id: str,
    title: str,
    *,
    events: int,
    session_ids: set[str],
    days: float,
    evidence: dict[str, Any],
    expected: str,
    risk: str,
    target: str,
    proposal: str | None,
    note: str = "",
) -> dict[str, Any]:
    """Build a scorecard finding with confidence and proposal eligibility."""
    confidence = confidence_level(events, len(session_ids), days)
    proposable = is_proposable(events, len(session_ids), days)
    if not proposable:
        proposal = None
    status = "ok" if events else "no_data"
    return {
        "id": class_id,
        "class": class_id,
        "title": title,
        "status": status,
        "confidence": confidence,
        "proposable": proposable,
        "events": events,
        "sessions": len(session_ids),
        "days_observed": days,
        "evidence": evidence,
        "expected_effect": expected,
        "risk": risk,
        "target": target,
        "proposal": proposal,
        "note": note,
    }


def no_data_finding(class_id: str, title: str, note: str) -> dict[str, Any]:
    """Build a finding representing a class with no usable data."""
    return finding(
        class_id,
        title,
        events=0,
        session_ids=set(),
        days=0.0,
        evidence={},
        expected="No change recommended.",
        risk="low",
        target="role",
        proposal=None,
        note=note,
    )


def permission_target(resources: list[str]) -> str:
    """Route a permission finding to role defaults or the personal playbook."""
    if not resources:
        return "role"
    path_like = 0
    for resource in resources:
        lowered = resource.lower()
        if (
            re.match(r"^(?:read|edit|external_directory):", lowered)
            or lowered.startswith("home:")
            or lowered.startswith("tmp:")
            or lowered.startswith("external:")
        ):
            path_like += 1
    return "playbook" if path_like * 2 > len(resources) else "role"


def permission_friction_finding(
    events: list[dict[str, Any]] | None,
    metrics_sessions: dict[str, dict[str, Any]] | None,
    grants: list[dict[str, Any]],
    detail: str,
    allow_content: bool,
    contract_note: str | None,
    turns: int,
) -> dict[str, Any]:
    """Build the permission-friction finding."""
    class_id = "permission_friction"
    title = "Permission friction"
    if events:
        groups: dict[tuple[str, str], dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "sessions": set(),
                "waits": [],
                "always": 0,
                "reject": 0,
                "timestamps": [],
                "samples": [],
            }
        )
        for event in events:
            action = str(event.get("action") or "unknown")
            resource = str(event.get("canonical_resource") or "unknown")
            key = (action, resource)
            group = groups[key]
            group["count"] += 1
            if event.get("session_id"):
                group["sessions"].add(event["session_id"])
            if event.get("wait_ms") is not None:
                group["waits"].append(float(event["wait_ms"]) / 1000)
            if event.get("reply") == "always":
                group["always"] += 1
            elif event.get("reply") == "reject":
                group["reject"] += 1
            if event.get("asked_at"):
                group["timestamps"].append(int(event["asked_at"]))
            if detail == "snippets" and allow_content and event.get("raw_resource"):
                group["samples"].append(redact(str(event["raw_resource"]))[:200])
        session_ids = {
            event["session_id"] for event in events if event.get("session_id")
        }
        timestamps = [
            int(event["asked_at"]) for event in events if event.get("asked_at")
        ]
        days = observed_days(timestamps)
        waits = [
            float(event["wait_ms"]) / 1000
            for event in events
            if event.get("wait_ms") is not None
        ]
        action_counts: dict[str, int] = defaultdict(int)
        for (action, _resource), group in groups.items():
            action_counts[action] += group["count"]
        top = sorted(
            groups.items(),
            key=lambda item: (item[1]["count"], len(item[1]["sessions"])),
            reverse=True,
        )[:5]
        evidence: dict[str, Any] = {
            "events": len(events),
            "sessions": len(session_ids),
            "median_wait_seconds": round(statistics.median(waits), 2)
            if waits
            else None,
            "p95_wait_seconds": round(percentile(waits, 0.95), 2) if waits else None,
            "always": sum(group["always"] for group in groups.values()),
            "reject": sum(group["reject"] for group in groups.values()),
            "action_counts": dict(sorted(action_counts.items())),
            "per_100_turns": round(len(events) / turns * 100, 2) if turns else None,
            "source": "permission_events",
        }
        if detail != "aggregate":
            evidence["patterns"] = [
                {
                    "pattern": key[1],
                    "action": key[0],
                    "count": group["count"],
                    "sessions": len(group["sessions"]),
                    "median_wait_seconds": (
                        round(statistics.median(group["waits"]), 2)
                        if group["waits"]
                        else None
                    ),
                    "always": group["always"],
                    "reject": group["reject"],
                }
                for key, group in top
            ]
        if detail == "snippets" and allow_content:
            evidence["snippets"] = [
                sample for _key, group in top for sample in group["samples"]
            ][:3]
        proposal = (
            "Add a narrow allow rule or a script/Make target for the most frequent "
            "repeated approval, keeping write forms behind an ask rule."
        )
        return finding(
            class_id,
            title,
            events=len(events),
            session_ids=session_ids,
            days=days,
            evidence=evidence,
            expected="Fewer prompts and shorter waits for recurring approvals.",
            risk="medium",
            target=permission_target([key[1] for key in groups]),
            proposal=proposal,
            note="",
        )
    if metrics_sessions:
        prompts = {
            session_id: value
            for session_id, value in metric_map(
                metrics_sessions, "permission_prompts"
            ).items()
            if value > 0
        }
        waits = list(metric_map(metrics_sessions, "permission_wait_seconds").values())
        timestamps = [
            session["started_at"]
            for session in metrics_sessions.values()
            if session.get("started_at")
        ]
        events_count = int(sum(prompts.values()))
        if events_count:
            evidence = {
                "events": events_count,
                "sessions": len(prompts),
                "total_wait_seconds": round(sum(waits), 2),
                "median_wait_seconds": (
                    round(statistics.median(waits), 2) if waits else None
                ),
                "p95_wait_seconds": (
                    round(percentile(waits, 0.95), 2) if waits else None
                ),
                "per_100_turns": (
                    round(events_count / turns * 100, 2) if turns else None
                ),
                "source": "session_metrics",
            }
            if detail != "aggregate":
                inferred = sorted(
                    {
                        canonical_command(str(grant.get("resource") or ""))
                        for grant in grants
                        if grant.get("action") == "shell"
                    }
                )
                evidence["inferred_patterns"] = inferred[:10]
            base_note = (
                "Permission capture unavailable; counts use session-level metrics "
                "and inferred patterns, so confidence is reduced."
            )
            note = f"{base_note} ({contract_note})" if contract_note else base_note
            result = finding(
                class_id,
                title,
                events=events_count,
                session_ids=set(prompts),
                days=observed_days(timestamps),
                evidence=evidence,
                expected="Fewer prompts and shorter waits for recurring approvals.",
                risk="medium",
                target=permission_target(
                    [
                        canonical_command(str(grant.get("resource") or ""))
                        for grant in grants
                        if grant.get("action") == "shell"
                    ]
                ),
                proposal=(
                    "Add a narrow allow rule for the most frequent repeated approval, "
                    "or a deterministic script/Make target that avoids the prompt."
                ),
                note=note,
            )
            # Without capture, the finding is still useful but one confidence
            # level lower than the same evidence would earn with exact events.
            downgraded = {"high": "medium", "medium": "low", "low": "low"}
            result["confidence"] = downgraded[result["confidence"]]
            result["proposable"] = (
                result["confidence"] != "low"
                and events_count >= MIN_EVENTS
                and len(prompts) >= MIN_SESSIONS
                and result["days_observed"] >= MIN_DAYS
            )
            if not result["proposable"]:
                result["proposal"] = None
            return result
    return no_data_finding(
        class_id,
        title,
        contract_note or "No permission events or session-level prompt metrics found.",
    )


def confirmation_finding(
    calls: list[dict[str, Any]],
    turns: int,
    session_ids: set[str],
    days: float,
) -> dict[str, Any]:
    """Build the confirmation-stall finding from question tool calls."""
    questions = [call for call in calls if call["name"] == "question"]
    waits = [
        (call["end"] - call["start"]) / 1000
        for call in questions
        if call.get("start") and call.get("end") and call["end"] >= call["start"]
    ]
    if not questions:
        return no_data_finding(
            "confirmation_stalls",
            "Confirmation stalls",
            "No question tool calls found in the window.",
        )
    question_sessions = {call["session_id"] for call in questions}
    rate = round(len(questions) / turns * 100, 2) if turns else None
    evidence = {
        "question_calls": len(questions),
        "sessions": len(question_sessions),
        "median_wait_seconds": round(statistics.median(waits), 2) if waits else None,
        "p95_wait_seconds": round(percentile(waits, 0.95), 2) if waits else None,
        "per_100_turns": rate,
    }
    return finding(
        "confirmation_stalls",
        "Confirmation stalls",
        events=len(questions),
        session_ids=question_sessions,
        days=days,
        evidence=evidence,
        expected="Fewer blocked turns and shorter waits for decisions.",
        risk="low",
        target="role",
        proposal=(
            "Apply the autonomy contract: continue authorized reversible work, "
            "stop only for irreversible actions, and batch independent decisions "
            "into one question."
        ),
    )


def latency_finding(
    calls: list[dict[str, Any]],
    sessions: dict[str, dict[str, Any]],
    idle: dict[str, list[int]],
    days: float,
) -> dict[str, Any]:
    """Build the subagent and tool latency finding with outlier exclusion."""

    def crossed_idle(call: dict[str, Any]) -> bool:
        start, end = call.get("start"), call.get("end")
        if not start or not end:
            return False
        return any(
            start <= moment <= end for moment in idle.get(call["session_id"], [])
        )

    usable = []
    excluded = 0
    for call in calls:
        if not call.get("start") or not call.get("end"):
            continue
        session = sessions.get(call["session_id"], {})
        wall = (session.get("time_updated", 0) - session.get("time_created", 0)) / 1000
        duration = (call["end"] - call["start"]) / 1000
        if duration <= 0:
            continue
        if wall > MAX_SESSION_WALL_SECONDS or duration > MAX_TOOL_SPAN_SECONDS:
            excluded += 1
            continue
        if crossed_idle(call):
            excluded += 1
            continue
        usable.append({**call, "duration": duration})
    tasks = [call for call in usable if call["name"] in TASK_TOOL_NAMES]
    selected = tasks if len(tasks) >= MIN_EVENTS else usable
    if not selected:
        return no_data_finding(
            "latency",
            "Subagent and tool latency",
            "No usable tool durations found in the window.",
        )
    durations = [call["duration"] for call in selected]
    selected_sessions = {call["session_id"] for call in selected}
    task_sessions = {call["session_id"] for call in tasks}
    slow_groups: list[dict[str, Any]] = []
    if tasks:
        grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
        for call in tasks:
            session = sessions.get(call["session_id"], {})
            grouped[
                (session.get("agent", "unknown"), session.get("model", "unknown"))
            ].append(call["duration"])
        slow_groups = [
            {
                "agent": agent,
                "model": model_label(model),
                "count": len(values),
                "p50_seconds": round(statistics.median(values), 2),
            }
            for (agent, model), values in sorted(
                grouped.items(),
                key=lambda item: statistics.median(item[1]),
                reverse=True,
            )[:3]
        ]
    evidence = {
        "tool_calls": len(usable),
        "task_calls": len(tasks),
        "measured_calls": len(selected),
        "sessions": len(selected_sessions),
        "task_sessions": len(task_sessions),
        "p50_seconds": round(percentile(durations, 0.50) or 0.0, 2),
        "p95_seconds": round(percentile(durations, 0.95) or 0.0, 2),
        "max_seconds": round(max(durations), 2),
        "excluded_outliers": excluded,
    }
    if slow_groups:
        evidence["slowest_agent_model"] = slow_groups
    return finding(
        "latency",
        "Subagent and tool latency",
        events=len(selected),
        session_ids=selected_sessions,
        days=days,
        evidence=evidence,
        expected="Lower task p95 by narrowing subagent scope or routing to a faster model.",
        risk="low",
        target="playbook",
        proposal=(
            "Narrow subagent prompts, split large tasks, or route slow agent/model "
            "combinations through an environment-specific model override."
        ),
    )


def waste_finding(
    calls: list[dict[str, Any]],
    metrics_sessions: dict[str, dict[str, Any]] | None,
    project_filter: str | None,
    detail: str,
    allow_content: bool,
    days: float,
) -> dict[str, Any]:
    """Build the token, context, duplicate-read, and repeated-command finding."""
    read_calls = [call for call in calls if call["name"] in READ_TOOL_NAMES]
    shell_calls = [
        call
        for call in calls
        if call["name"] in SHELL_TOOL_NAMES and call.get("command")
    ]
    path_counts: dict[str, dict[str, Any]] = {}
    for call in read_calls:
        key = path_key(call.get("path"))
        group, extension = path_class(call.get("path"))
        entry = path_counts.setdefault(
            key, {"count": 0, "sessions": set(), "class": f"{group}:{extension}"}
        )
        entry["count"] += 1
        entry["sessions"].add(call["session_id"])
    command_counts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "sessions": set(), "samples": [], "canonical": "unknown"}
    )
    for call in shell_calls:
        normalized = WHITESPACE_RE.sub(" ", redact(str(call["command"]))).strip()
        entry = command_counts[normalized]
        entry["count"] += 1
        entry["sessions"].add(call["session_id"])
        if entry["canonical"] == "unknown":
            entry["canonical"] = canonical_command(str(call["command"]))
        if detail == "snippets" and allow_content:
            entry["samples"].append(normalized[:200])
    duplicate_reads = sum(max(0, entry["count"] - 1) for entry in path_counts.values())
    repeated_commands = sum(
        max(0, entry["count"] - 1) for entry in command_counts.values()
    )
    duplicate_sessions: set[str] = set()
    for entry in path_counts.values():
        if entry["count"] > 1:
            duplicate_sessions.update(entry["sessions"])
    for entry in command_counts.values():
        if entry["count"] > 1:
            duplicate_sessions.update(entry["sessions"])
    compactions = (
        int(metric_total(metrics_sessions, "compactions")) if metrics_sessions else 0
    )
    if metrics_sessions:
        duplicate_sessions.update(
            session_id
            for session_id, value in metric_map(metrics_sessions, "compactions").items()
            if value > 0
        )
    turns = (
        int(metric_total(metrics_sessions, "turns_total")) if metrics_sessions else 0
    )
    tokens = 0.0
    if metrics_sessions:
        # Cache-read tokens are cheap context reuse, so exclude them from the
        # per-turn cost signal; input, output, and reasoning reflect new work.
        tokens = sum(
            metric_total(metrics_sessions, name)
            for name in ("tokens_input", "tokens_output", "tokens_reasoning")
        )
    events = duplicate_reads + repeated_commands + compactions
    if not events:
        return no_data_finding(
            "waste",
            "Token and context waste",
            "No duplicate reads, repeated commands, or compactions found.",
        )
    evidence = {
        "duplicate_reads": duplicate_reads,
        "repeated_commands": repeated_commands,
        "reads": len(read_calls),
        "commands": len(shell_calls),
        "duplicate_rate_per_1000_reads": (
            round(duplicate_reads / len(read_calls) * 1000, 2) if read_calls else None
        ),
        "repeat_rate_per_1000_commands": (
            round(repeated_commands / len(shell_calls) * 1000, 2)
            if shell_calls
            else None
        ),
        "compactions": compactions,
        "tokens_per_turn": round(tokens / turns, 1) if turns else None,
        "turns": turns,
    }
    if detail != "aggregate":
        class_duplicates: dict[str, int] = defaultdict(int)
        for entry in path_counts.values():
            if entry["count"] > 1:
                class_duplicates[entry["class"]] += entry["count"] - 1
        evidence["duplicate_path_classes"] = [
            {"class": key, "count": count}
            for key, count in sorted(
                class_duplicates.items(), key=lambda item: item[1], reverse=True
            )[:5]
        ]
        canonical_patterns: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "sessions": set()}
        )
        for entry in command_counts.values():
            if entry["count"] > 1:
                pattern = canonical_patterns[entry["canonical"]]
                pattern["count"] += entry["count"]
                pattern["sessions"].update(entry["sessions"])
        evidence["repeated_patterns"] = [
            {
                "pattern": pattern,
                "count": value["count"],
                "sessions": len(value["sessions"]),
            }
            for pattern, value in sorted(
                canonical_patterns.items(),
                key=lambda item: item[1]["count"],
                reverse=True,
            )[:5]
        ]
    if detail == "snippets" and allow_content:
        evidence["snippets"] = [
            sample
            for entry in sorted(
                command_counts.values(), key=lambda item: item["count"], reverse=True
            )
            if entry["count"] > 1
            for sample in entry["samples"]
        ][:3]
    target = "repo" if project_filter else "role"
    return finding(
        "waste",
        "Token and context waste",
        events=events,
        session_ids=duplicate_sessions,
        days=days,
        evidence=evidence,
        expected="Fewer duplicate reads, repeated commands, and compactions per session.",
        risk="low",
        target=target,
        proposal=(
            "Add a deterministic task-runner target or repository guidance that "
            "reuses prior reads and avoids repeating identical commands."
        ),
    )


def drift_finding(
    grants: list[dict[str, Any]],
    detail: str,
    days: float,
) -> dict[str, Any]:
    """Build the permission-policy drift finding from persisted grants."""
    if not grants:
        return no_data_finding(
            "permission_policy_drift",
            "Permission-policy drift",
            "No persisted permission grants found.",
        )
    risky: list[dict[str, Any]] = []
    for grant in grants:
        action = str(grant.get("action") or "unknown")
        resource = str(grant.get("resource") or "")
        if action == "shell":
            canonical = canonical_command(resource)
        else:
            canonical = file_pattern(action, resource)
        risk = ""
        if "$" in resource or "{" in resource:
            risk = "unusable_parameterized"
        elif action == "shell" and canonical in RISKY_COMMAND_HEADS:
            risk = "broad_destructive"
        if risk:
            risky.append(
                {
                    "action": action,
                    "canonical_resource": canonical,
                    "risk": risk,
                    "project_id": grant.get("project_id"),
                    "timestamps": [
                        to_ms(grant.get(column))
                        for column in ("time_created", "time_updated")
                        if grant.get(column)
                    ],
                }
            )
    if not risky:
        return no_data_finding(
            "permission_policy_drift",
            "Permission-policy drift",
            f"{len(grants)} persisted grants found; none classified as broad or unusable.",
        )
    projects = {str(item["project_id"]) for item in risky if item.get("project_id")}
    timestamps = [moment for item in risky for moment in item["timestamps"] if moment]
    evidence = {
        "total_grants": len(grants),
        "risky_grants": len(risky),
        "projects": len(projects),
        "risk_counts": {
            risk: sum(1 for item in risky if item["risk"] == risk)
            for risk in {item["risk"] for item in risky}
        },
    }
    if detail != "aggregate":
        grouped_risky: dict[tuple[str, str], int] = defaultdict(int)
        for item in risky:
            grouped_risky[(item["canonical_resource"], item["risk"])] += 1
        evidence["patterns"] = [
            {"pattern": pattern, "risk": risk, "count": count}
            for (pattern, risk), count in sorted(
                grouped_risky.items(), key=lambda item: item[1], reverse=True
            )[:10]
        ]
    return finding(
        "permission_policy_drift",
        "Permission-policy drift",
        events=len(risky),
        session_ids=projects,
        days=observed_days(timestamps),
        evidence=evidence,
        expected="Broad or unusable grants replaced by narrow read-only allows and write asks.",
        risk="medium",
        target=permission_target([item["canonical_resource"] for item in risky]),
        proposal=(
            "Revoke the broad grants and replace them with read-only allow forms "
            "plus an ask rule for the matching write operations."
        ),
    )


def analyze(
    days: int = 30,
    project: str | None = None,
    detail: str = "aggregate",
    allow_content: bool = False,
    save_report: bool = True,
) -> dict[str, Any]:
    """Collect local signals and build the retrospective scorecard."""
    if detail not in DETAIL_LEVELS:
        raise ValueError(f"detail must be one of {', '.join(DETAIL_LEVELS)}")
    if detail == "snippets" and not allow_content:
        raise ValueError("detail 'snippets' requires --allow-content")
    if days < 1:
        raise ValueError("--days must be at least 1")

    now = utc_now()
    since = now - timedelta(days=days)
    since_ms = int(since.timestamp() * 1000)
    until_ms = int(now.timestamp() * 1000)

    sources: list[dict[str, Any]] = []
    warnings: list[str] = []

    stats, stats_source = load_stats()
    sources.append(stats_source)
    del stats

    sessions: dict[str, dict[str, Any]] = {}
    calls: list[dict[str, Any]] = []
    grants: list[dict[str, Any]] = []
    idle: dict[str, list[int]] = {}
    session_present: list[str] = []

    opencode_path = opencode_db_path()
    opencode_connection = open_readonly(opencode_path)
    if opencode_connection is None:
        sources.append(
            source(
                "sessions",
                "missing",
                f"{opencode_path.name} not found or unreadable",
            )
        )
    else:
        try:
            sessions, session_present, session_warnings = load_sessions(
                opencode_connection, since_ms, until_ms, project
            )
            warnings.extend(session_warnings)
            calls, call_warnings = load_tool_calls(opencode_connection, list(sessions))
            warnings.extend(call_warnings)
            idle = load_idle_events(opencode_connection, list(sessions))
            grants, grant_note = load_grants(opencode_connection)
            if grant_note:
                warnings.append(grant_note)
            if project and any(
                "project_worktree" in grant or "project_name" in grant
                for grant in grants
            ):
                needle = project.lower()
                grants = [
                    grant
                    for grant in grants
                    if needle in str(grant.get("project_worktree") or "").lower()
                    or needle in str(grant.get("project_name") or "").lower()
                ]
            status = "ok" if sessions else "degraded"
            sources.append(
                source(
                    "sessions",
                    status,
                    f"tables: {', '.join(session_present) or 'none'}",
                    sessions=len(sessions),
                    tool_calls=len(calls),
                    grants=len(grants),
                )
            )
        finally:
            opencode_connection.close()

    metrics_sessions: dict[str, dict[str, Any]] | None = None
    metrics_connection = open_readonly(metrics_db_path())
    if metrics_connection is None:
        sources.append(
            source("metrics", "missing", f"{metrics_db_path().name} not found")
        )
        permission_events: list[dict[str, Any]] | None = None
        contract_note = "Metrics database absent; permission capture unavailable."
    else:
        metrics_connection.close()
        metrics_sessions, metrics_source, metric_warnings = load_metrics(
            metrics_db_path(), since_ms, project
        )
        sources.append(metrics_source)
        warnings.extend(metric_warnings)
        metrics_connection = open_readonly(metrics_db_path())
        if metrics_connection is None:
            permission_events = None
            contract_note = (
                "Metrics database unreadable; permission capture unavailable."
            )
        else:
            try:
                permission_events, contract_note = load_permission_events(
                    metrics_connection, since_ms
                )
            finally:
                metrics_connection.close()
            if project and permission_events and sessions:
                permission_events = [
                    event
                    for event in permission_events
                    if event.get("session_id") in sessions
                ]
            if permission_events is not None:
                sources.append(
                    source(
                        "permission_events",
                        "ok",
                        "contract version 1",
                        events=len(permission_events),
                    )
                )
            else:
                sources.append(
                    source(
                        "permission_events",
                        "degraded",
                        contract_note or "permission capture unavailable",
                    )
                )

    all_session_ids = set(sessions) | set(metrics_sessions or {})
    timestamps = [
        session["time_created"]
        for session in sessions.values()
        if session["time_created"]
    ]
    timestamps.extend(
        session["started_at"]
        for session in (metrics_sessions or {}).values()
        if session.get("started_at")
    )
    days_observed = observed_days(timestamps) if timestamps else float(days)
    turns = (
        int(metric_total(metrics_sessions, "turns_total")) if metrics_sessions else 0
    )
    reads = sum(1 for call in calls if call["name"] in READ_TOOL_NAMES)
    tool_calls = len(calls)

    findings = [
        permission_friction_finding(
            permission_events,
            metrics_sessions,
            grants,
            detail,
            allow_content,
            contract_note,
            turns,
        ),
        confirmation_finding(calls, turns, all_session_ids, days_observed),
        latency_finding(calls, sessions, idle, days_observed),
        waste_finding(
            calls, metrics_sessions, project, detail, allow_content, days_observed
        ),
        drift_finding(grants, detail, days_observed),
    ]
    metrics_snapshot = {
        "permission_prompts": (
            int(metric_total(metrics_sessions, "permission_prompts"))
            if metrics_sessions
            else 0
        ),
        "permission_wait_seconds": (
            round(metric_total(metrics_sessions, "permission_wait_seconds"), 2)
            if metrics_sessions
            else 0.0
        ),
        "question_calls": findings[1]["events"],
        "question_wait_p95_seconds": findings[1]["evidence"].get("p95_wait_seconds"),
        "task_p50_seconds": findings[2]["evidence"].get("p50_seconds"),
        "task_p95_seconds": findings[2]["evidence"].get("p95_seconds"),
        "duplicate_reads": findings[3]["evidence"].get("duplicate_reads", 0),
        "repeated_commands": findings[3]["evidence"].get("repeated_commands", 0),
        "tokens_per_turn": findings[3]["evidence"].get("tokens_per_turn"),
        "compactions": findings[3]["evidence"].get("compactions", 0),
    }

    scorecard = {
        "schema": SCHEMA,
        "generated_at": now.isoformat(),
        "window": {
            "days": days,
            "start": since.isoformat(),
            "end": now.isoformat(),
            "start_ms": since_ms,
            "end_ms": until_ms,
        },
        "project": os.path.basename((project or "").rstrip("/")) or "all",
        "detail": detail,
        "allow_content": bool(allow_content),
        "sources": sources,
        "coverage": {
            "sessions": len(all_session_ids),
            "turns": turns,
            "tool_calls": tool_calls,
            "reads": reads,
            "conversation_sessions": len(sessions),
            "metrics_sessions": len(metrics_sessions or {}),
            "days_observed": days_observed,
        },
        "thresholds": {
            "min_days": MIN_DAYS,
            "min_events": MIN_EVENTS,
            "min_sessions": MIN_SESSIONS,
            "high_events": HIGH_EVENTS,
            "max_session_wall_seconds": MAX_SESSION_WALL_SECONDS,
        },
        "findings": findings,
        "clean": not any(item["proposable"] for item in findings),
        "metrics": metrics_snapshot,
        "warnings": sorted(set(warnings)),
    }
    if save_report:
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        report_dir = reports_root()
        ensure_private_dir(report_dir)
        json_path = report_dir / f"{stamp}-{detail}.json"
        markdown_path = report_dir / f"{stamp}-{detail}.md"
        write_private(json_path, json.dumps(scorecard, indent=2, sort_keys=True))
        write_private(markdown_path, render_markdown(scorecard))
        scorecard["report"] = {
            "json": json_path.name,
            "markdown": markdown_path.name,
        }
    return scorecard


def _format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def render_markdown(scorecard: dict[str, Any]) -> str:
    """Render a scorecard as a compact markdown report."""
    window = scorecard["window"]
    coverage = scorecard["coverage"]
    lines = [
        "# Session Retrospective",
        "",
        f"- **Window:** {window['start'][:10]} to {window['end'][:10]} "
        f"({window['days']} days)",
        f"- **Project:** {scorecard['project']}",
        f"- **Detail:** {scorecard['detail']}",
        f"- **Generated:** {scorecard['generated_at']}",
        "",
        "## Sources",
        "",
        "| Source | Status | Detail | Coverage |",
        "|---|---|---|---|",
    ]
    for item in scorecard["sources"]:
        coverage_text = ", ".join(
            f"{key}={_format_value(value)}"
            for key, value in item["coverage"].items()
            if value is not None
        )
        lines.append(
            f"| {item['name']} | {item['status']} | {item['detail']} | "
            f"{coverage_text or 'n/a'} |"
        )
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Sessions: {coverage['sessions']}",
            f"- Turns: {coverage['turns']}",
            f"- Tool calls: {coverage['tool_calls']}",
            f"- Reads: {coverage['reads']}",
            f"- Observed days: {coverage['days_observed']}",
            "",
            "## Findings",
            "",
        ]
    )
    if scorecard["clean"]:
        lines.append(
            "No finding clears the evidence threshold for a proposal. "
            "Reported items remain advisory."
        )
        lines.append("")
    for item in scorecard["findings"]:
        lines.append(f"### {item['title']}")
        lines.append("")
        lines.append(
            f"- **Status:** {item['status']} | **Confidence:** {item['confidence']} "
            f"| **Proposable:** {'yes' if item['proposable'] else 'no'}"
        )
        lines.append(
            f"- **Events:** {item['events']} across {item['sessions']} sessions"
        )
        if item["evidence"]:
            evidence = ", ".join(
                f"{key}={_format_value(value)}"
                for key, value in item["evidence"].items()
                if not isinstance(value, (dict, list))
            )
            if evidence:
                lines.append(f"- **Evidence:** {evidence}")
            for key in ("patterns", "inferred_patterns", "duplicate_path_classes"):
                values = item["evidence"].get(key)
                if values:
                    lines.append(f"- **{key.replace('_', ' ').title()}:**")
                    for value in values:
                        lines.append(f"  - {json.dumps(value, sort_keys=True)}")
            snippets = item["evidence"].get("snippets")
            if snippets:
                lines.append("- **Snippets (redacted):**")
                for snippet in snippets:
                    lines.append(f"  - `{snippet}`")
        lines.append(f"- **Expected effect:** {item['expected_effect']}")
        lines.append(f"- **Risk:** {item['risk']}")
        lines.append(f"- **Proposal target:** {item['target']}")
        if item["proposal"]:
            lines.append(f"- **Proposal:** {item['proposal']}")
        if item["note"]:
            lines.append(f"- **Note:** {item['note']}")
        lines.append("")
    if scorecard["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in scorecard["warnings"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_ledger() -> dict[str, Any]:
    """Load the intervention ledger, returning an empty structure if absent."""
    path = ledger_path()
    if not path.exists():
        return {"schema": LEDGER_SCHEMA, "interventions": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema": LEDGER_SCHEMA, "interventions": []}
    if not isinstance(payload, dict):
        return {"schema": LEDGER_SCHEMA, "interventions": []}
    payload.setdefault("schema", LEDGER_SCHEMA)
    payload.setdefault("interventions", [])
    return payload


def save_ledger(ledger: dict[str, Any]) -> None:
    """Persist the intervention ledger privately."""
    write_private(ledger_path(), json.dumps(ledger, indent=2, sort_keys=True))


def record_intervention(record: dict[str, Any]) -> dict[str, Any]:
    """Add an intervention to the ledger."""
    required = [
        "target",
        "change_ref",
        "hypothesis",
        "metric",
        "expected_direction",
        "review_date",
    ]
    missing = [key for key in required if not record.get(key)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    direction = str(record["expected_direction"]).lower()
    if direction not in {"decrease", "increase"}:
        raise ValueError("expected_direction must be 'decrease' or 'increase'")
    if not parse_iso(str(record["review_date"])):
        raise ValueError("review_date must be an ISO-8601 date or timestamp")
    baseline = record.get("baseline") or {}
    if not isinstance(baseline, dict):
        raise ValueError("baseline must be an object")
    if baseline.get("value") is None:
        raise ValueError("baseline.value is required")
    ledger = load_ledger()
    intervention_id = record.get("id") or (
        "int-" + utc_now().strftime("%Y%m%dT%H%M%S%fZ")
    )
    if any(item.get("id") == intervention_id for item in ledger["interventions"]):
        raise ValueError(f"intervention id already exists: {intervention_id}")
    intervention = {
        "id": intervention_id,
        "created_at": utc_now().isoformat(),
        "target": record["target"],
        "change_ref": record["change_ref"],
        "hypothesis": record["hypothesis"],
        "metric": record["metric"],
        "baseline": {
            "start": baseline.get("start"),
            "end": baseline.get("end"),
            "value": float(baseline["value"]),
            "sessions": int(baseline.get("sessions") or 0),
        },
        "expected_direction": direction,
        "review_date": record["review_date"],
        "status": record.get("status") or "pending",
        "result": None,
    }
    ledger["interventions"].append(intervention)
    save_ledger(ledger)
    return intervention


def verify_interventions(
    intervention_id: str | None = None,
    days: int | None = None,
    project: str | None = None,
) -> list[dict[str, Any]]:
    """Compare current metrics with each intervention baseline."""
    ledger = load_ledger()
    selected = [
        item
        for item in ledger["interventions"]
        if intervention_id is None or item.get("id") == intervention_id
    ]
    if intervention_id and not selected:
        raise ValueError(f"intervention not found: {intervention_id}")
    results = []
    for item in selected:
        baseline = item.get("baseline") or {}
        window_days = days
        if window_days is None:
            start = parse_iso(baseline.get("start"))
            end = parse_iso(baseline.get("end"))
            if start and end and end > start:
                window_days = max(1, round((end - start).total_seconds() / 86_400))
            else:
                window_days = 30
        current = analyze(
            days=window_days,
            project=project,
            detail="aggregate",
            allow_content=False,
            save_report=False,
        )
        metric = item.get("metric")
        current_value = current["metrics"].get(metric)
        baseline_value = baseline.get("value")
        sessions = current["coverage"]["sessions"]
        insufficient = sessions < MIN_SESSIONS or current_value in (None, 0)
        recommendation = "insufficient-data"
        change_percent = None
        if not insufficient and baseline_value not in (None, 0):
            change_percent = round(
                (float(current_value) - float(baseline_value))
                / abs(float(baseline_value))
                * 100,
                2,
            )
            threshold = 10.0
            if item.get("expected_direction") == "decrease":
                if change_percent <= -threshold:
                    recommendation = "keep"
                elif change_percent >= threshold:
                    recommendation = "revert"
                else:
                    recommendation = "extend"
            else:
                if change_percent >= threshold:
                    recommendation = "keep"
                elif change_percent <= -threshold:
                    recommendation = "revert"
                else:
                    recommendation = "extend"
        result = {
            "id": item.get("id"),
            "metric": metric,
            "baseline_value": baseline_value,
            "current_value": current_value,
            "change_percent": change_percent,
            "expected_direction": item.get("expected_direction"),
            "sessions": sessions,
            "window_days": window_days,
            "recommendation": recommendation,
            "review_date": item.get("review_date"),
        }
        item["result"] = result
        item["last_verified_at"] = utc_now().isoformat()
        results.append(result)
    save_ledger(ledger)
    return results


def render_verification(results: list[dict[str, Any]]) -> str:
    """Render intervention verification as markdown."""
    if not results:
        return "No interventions recorded.\n"
    lines = ["# Intervention Verification", ""]
    for result in results:
        lines.extend(
            [
                f"## {result['id']}",
                "",
                f"- **Metric:** {result['metric']}",
                f"- **Baseline:** {_format_value(result['baseline_value'])}",
                f"- **Current:** {_format_value(result['current_value'])}",
                f"- **Change:** {_format_value(result['change_percent'])}%",
                f"- **Expected direction:** {result['expected_direction']}",
                f"- **Sessions in window:** {result['sessions']}",
                f"- **Recommendation:** {result['recommendation']}",
                "",
            ]
        )
        if result["recommendation"] == "insufficient-data":
            lines.append(
                "Insufficient follow-up data; success or failure cannot be claimed."
            )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Produce a local, read-only OpenCode session retrospective."
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser(
        "analyze", help="analyze a window and print a scorecard"
    )
    analyze_parser.add_argument("--days", type=int, default=30)
    analyze_parser.add_argument("--project", default=None)
    analyze_parser.add_argument("--detail", choices=DETAIL_LEVELS, default="aggregate")
    analyze_parser.add_argument("--allow-content", action="store_true")
    analyze_parser.add_argument("--json", action="store_true", dest="as_json")
    analyze_parser.add_argument("--no-save", action="store_true")

    record_parser = subparsers.add_parser(
        "record", help="record an accepted intervention"
    )
    record_parser.add_argument("--file", required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="verify recorded interventions"
    )
    verify_parser.add_argument("--id", default=None)
    verify_parser.add_argument("--days", type=int, default=None)
    verify_parser.add_argument("--project", default=None)
    verify_parser.add_argument("--json", action="store_true", dest="as_json")

    # Default to analyze when no subcommand is supplied for compatibility with
    # the /session_retro command invocation.
    parser.set_defaults(command="analyze", days=30, project=None, detail="aggregate")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the helper and return a process exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] not in {"analyze", "record", "verify"}:
        arguments = ["analyze", *arguments]
    parser = build_parser()
    args = parser.parse_args(arguments)
    try:
        if args.command == "record":
            payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
            intervention = record_intervention(payload)
            print(json.dumps(intervention, indent=2, sort_keys=True))
            return 0
        if args.command == "verify":
            results = verify_interventions(args.id, args.days, args.project)
            if args.as_json:
                print(json.dumps(results, indent=2, sort_keys=True))
            else:
                print(render_verification(results), end="")
            return 0
        scorecard = analyze(
            days=args.days,
            project=args.project,
            detail=args.detail,
            allow_content=args.allow_content,
            save_report=not args.no_save,
        )
        if args.as_json:
            print(json.dumps(scorecard, indent=2, sort_keys=True))
        else:
            print(render_markdown(scorecard), end="")
        return 0
    except (ValueError, OSError, sqlite3.Error) as error:
        print(f"session_insights: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
