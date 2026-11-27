# SPDX-License-Identifier: Apache-2.0
"""Offline tests for the session retrospective helper.

Every fixture is synthetic and lives in a temporary directory. The tests never
read the user's real OpenCode or metrics databases.
"""

import importlib.util
import json
import os
import sqlite3
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "files/scripts/session_insights.py"
SPEC = importlib.util.spec_from_file_location("session_insights", HELPER)
insights = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(insights)


def days_ago(days: float) -> int:
    """Return an epoch-millisecond timestamp a number of days in the past."""
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return int(moment.timestamp() * 1000)


def tool_part(name: str, start: int, duration_ms: int, **input_data) -> dict:
    """Build a legacy-shaped tool part payload."""
    return {
        "type": "tool",
        "tool": name,
        "callID": f"call-{name}-{start}",
        "state": {
            "status": "completed",
            "input": input_data,
            "time": {"start": start, "end": start + duration_ms},
        },
    }


def v2_tool_part(name: str, start: int, duration_ms: int, **input_data) -> dict:
    """Build a V2-shaped tool part payload."""
    return {
        "type": "tool",
        "id": f"call-{name}-{start}",
        "name": name,
        "state": {"status": "completed", "input": input_data},
        "time": {"created": start, "completed": start + duration_ms},
    }


def create_legacy_db(path: Path, session_count: int = 4, span_days: int = 10) -> None:
    """Create a synthetic legacy OpenCode database."""
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE project (
            id TEXT PRIMARY KEY, worktree TEXT, name TEXT
        );
        CREATE TABLE session (
            id TEXT PRIMARY KEY, project_id TEXT, parent_id TEXT,
            directory TEXT, time_created INTEGER, time_updated INTEGER,
            agent TEXT, model TEXT, cost REAL,
            tokens_input INTEGER, tokens_output INTEGER, tokens_reasoning INTEGER,
            tokens_cache_read INTEGER, tokens_cache_write INTEGER
        );
        CREATE TABLE message (
            id TEXT PRIMARY KEY, session_id TEXT,
            time_created INTEGER, time_updated INTEGER, data TEXT
        );
        CREATE TABLE part (
            id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT,
            time_created INTEGER, time_updated INTEGER, data TEXT
        );
        CREATE TABLE permission (
            id TEXT PRIMARY KEY, project_id TEXT, action TEXT, resource TEXT,
            time_created INTEGER, time_updated INTEGER
        );
        """
    )
    connection.execute(
        "INSERT INTO project VALUES ('p1', '/home/test/project', 'project')"
    )
    for index in range(session_count):
        start = days_ago(span_days - index * (span_days / max(session_count, 1)))
        session_id = f"ses_legacy_{index}"
        connection.execute(
            "INSERT INTO session VALUES (?, ?, NULL, ?, ?, ?, 'build', 'model-a', 0,"
            " 100, 50, 10, 0, 0)",
            (
                session_id,
                "p1",
                "/home/test/project",
                start,
                start + 3_600_000,
            ),
        )
        connection.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?, ?)",
            (
                f"msg_{index}",
                session_id,
                start,
                start + 3_600_000,
                json.dumps({"role": "user"}),
            ),
        )
        parts = []
        for offset in range(3):
            moment = start + offset * 1000
            parts.append(
                (
                    f"question_{index}_{offset}",
                    tool_part(
                        "question",
                        moment,
                        90_000,
                        questions=[{"question": "Proceed?", "header": "Confirm"}],
                    ),
                )
            )
            parts.append(
                (
                    f"task_{index}_{offset}",
                    tool_part("task", moment, 120_000, description="Explore"),
                )
            )
        for offset in range(10):
            moment = start + 10_000 + offset * 1000
            parts.append(
                (
                    f"read_{index}_{offset}",
                    tool_part(
                        "read",
                        moment,
                        200,
                        path=(
                            "src/module.py"
                            if offset % 2 == 0
                            else "tests/test_module.py"
                        ),
                    ),
                )
            )
        commands = [
            "make test",
            "make test",
            "git status --short",
            "GITHUB_TOKEN=ghp_abcdefgh12345678 gh api -f title=secret",
        ]
        for offset, command in enumerate(commands):
            moment = start + 20_000 + offset * 1000
            parts.append(
                (
                    f"shell_{index}_{offset}",
                    tool_part("shell", moment, 500, command=command),
                )
            )
        for part_id, payload in parts:
            connection.execute(
                "INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                (
                    part_id,
                    f"msg_{index}",
                    session_id,
                    start,
                    start,
                    json.dumps(payload),
                ),
            )
    for grant in (
        ("grant-1", "p1", "shell", "git push *"),
        ("grant-2", "p1", "shell", "$cmd *"),
        ("grant-3", "p1", "shell", "git config --get *"),
    ):
        connection.execute(
            "INSERT INTO permission VALUES (?, ?, ?, ?, ?, ?)",
            (*grant, days_ago(5), days_ago(1)),
        )
    connection.commit()
    connection.close()


def create_v2_db(path: Path, session_count: int = 4, span_days: int = 10) -> None:
    """Create a synthetic V2 OpenCode database."""
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE session_v2 (
            id TEXT PRIMARY KEY, project_id TEXT, parent_id TEXT,
            directory TEXT, time_created INTEGER, time_updated INTEGER,
            agent TEXT, model TEXT, cost REAL,
            tokens_input INTEGER, tokens_output INTEGER, tokens_reasoning INTEGER,
            tokens_cache_read INTEGER, tokens_cache_write INTEGER
        );
        CREATE TABLE session_message (
            id TEXT PRIMARY KEY, session_id TEXT, type TEXT, seq INTEGER,
            time_created INTEGER, time_updated INTEGER, data TEXT
        );
        CREATE TABLE session_part (
            message_id TEXT NOT NULL, session_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL, type TEXT, call_id TEXT,
            time_created INTEGER, time_updated INTEGER, data TEXT,
            PRIMARY KEY (message_id, ordinal)
        );
        """
    )
    for index in range(session_count):
        start = days_ago(span_days - index * (span_days / max(session_count, 1)))
        session_id = f"ses_v2_{index}"
        connection.execute(
            "INSERT INTO session_v2 VALUES (?, ?, NULL, ?, ?, ?, 'plan', 'model-b',"
            " 0, 200, 80, 5, 0, 0)",
            (session_id, "p2", "/home/test/v2", start, start + 3_600_000),
        )
        message_id = f"msg_v2_{index}"
        connection.execute(
            "INSERT INTO session_message VALUES (?, ?, 'assistant', 0, ?, ?, '{}')",
            (message_id, session_id, start, start + 3_600_000),
        )
        connection.execute(
            "INSERT INTO session_message VALUES (?, ?, 'idle', 1, ?, ?, '{}')",
            (
                f"idle_{index}",
                session_id,
                start + 60_000,
                start + 60_000,
            ),
        )
        ordinal = 0
        for offset in range(3):
            moment = start + offset * 1000
            for name, duration, data in (
                (
                    "question",
                    30_000,
                    {"questions": [{"question": "Continue?"}]},
                ),
                ("task", 600_000, {"description": "Explore"}),
                ("read", 100, {"path": "src/app.ts"}),
            ):
                payload = v2_tool_part(name, moment, duration, **data)
                connection.execute(
                    "INSERT INTO session_part VALUES (?, ?, ?, 'tool', ?, ?, ?, ?)",
                    (
                        message_id,
                        session_id,
                        ordinal,
                        payload["id"],
                        moment,
                        moment + duration,
                        json.dumps(payload),
                    ),
                )
                ordinal += 1
    connection.commit()
    connection.close()


def create_v2_message_only_db(path: Path, session_count: int = 4) -> None:
    """Create a V2 database whose tool calls live only in message content."""
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE session_v2 (
            id TEXT PRIMARY KEY, project_id TEXT, parent_id TEXT,
            directory TEXT, time_created INTEGER, time_updated INTEGER,
            agent TEXT, model TEXT, cost REAL,
            tokens_input INTEGER, tokens_output INTEGER, tokens_reasoning INTEGER,
            tokens_cache_read INTEGER, tokens_cache_write INTEGER
        );
        CREATE TABLE session_message (
            id TEXT PRIMARY KEY, session_id TEXT, type TEXT, seq INTEGER,
            time_created INTEGER, time_updated INTEGER, data TEXT
        );
        CREATE TABLE session_part (
            message_id TEXT NOT NULL, session_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL, type TEXT, call_id TEXT,
            time_created INTEGER, time_updated INTEGER, data TEXT,
            PRIMARY KEY (message_id, ordinal)
        );
        """
    )
    for index in range(session_count):
        start = days_ago(10 - index * 2)
        session_id = f"ses_v2msg_{index}"
        connection.execute(
            "INSERT INTO session_v2 VALUES (?, 'p3', NULL, ?, ?, ?, 'build',"
            " 'model-c', 0, 100, 40, 5, 0, 0)",
            (session_id, "/home/test/v2msg", start, start + 3_600_000),
        )
        content = []
        for offset in range(3):
            moment = start + offset * 1000
            for name, duration, data in (
                ("question", 30_000, {"questions": [{"question": "Continue?"}]}),
                ("task", 120_000, {"description": "Explore"}),
                ("read", 100, {"path": f"src/file{offset}.py"}),
                ("shell", 100, {"command": "make test"}),
            ):
                content.append(
                    {
                        "type": "tool",
                        "id": f"call-{index}-{offset}-{name}",
                        "name": name,
                        "state": {"status": "completed", "input": data},
                        "time": {"created": moment, "completed": moment + duration},
                    }
                )
        connection.execute(
            "INSERT INTO session_message VALUES (?, ?, 'assistant', 0, ?, ?, ?)",
            (
                f"msg_v2msg_{index}",
                session_id,
                start,
                start + 3_600_000,
                json.dumps({"content": content}),
            ),
        )
    connection.commit()
    connection.close()


def create_metrics_db(
    path: Path,
    *,
    session_count: int = 4,
    prompts: int = 50,
    turns: int = 200,
    with_contract: bool = False,
    events: int = 0,
    span_days: int = 10,
) -> None:
    """Create a synthetic opencode-metrics database."""
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY, name TEXT, worktree TEXT
        );
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY, project_id TEXT, agent TEXT, model TEXT,
            started_at INTEGER, ended_at INTEGER, parent_session_id TEXT
        );
        CREATE TABLE measurements (
            session_id TEXT, metric_name TEXT, value REAL, recorded_at INTEGER,
            PRIMARY KEY (session_id, metric_name)
        );
        """
    )
    connection.execute(
        "INSERT INTO projects VALUES ('p1', 'example/project', '/home/test/project')"
    )
    per_session_prompts = prompts / session_count
    per_session_turns = turns / session_count
    for index in range(session_count):
        session_id = f"ses_metric_{index}"
        start = days_ago(span_days - index * (span_days / max(session_count, 1)))
        connection.execute(
            "INSERT INTO sessions VALUES (?, 'p1', 'build', 'model-a', ?, ?, NULL)",
            (session_id, start, start + 3_600_000),
        )
        metrics = {
            "permission_prompts": per_session_prompts,
            "permission_wait_seconds": per_session_prompts * 60,
            "turns_total": per_session_turns,
            "tokens_input": per_session_turns * 100,
            "tokens_output": per_session_turns * 40,
            "tokens_reasoning": per_session_turns * 10,
            "compactions": 1,
        }
        for name, value in metrics.items():
            connection.execute(
                "INSERT INTO measurements VALUES (?, ?, ?, ?)",
                (session_id, name, value, start),
            )
    if with_contract:
        connection.executescript(
            """
            CREATE TABLE permission_contract (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL, salt TEXT, created_at INTEGER
            );
            CREATE TABLE permission_events (
                permission_id TEXT PRIMARY KEY, session_id TEXT, project_id TEXT,
                agent TEXT, model TEXT, action TEXT NOT NULL, resource TEXT,
                resource_hash TEXT, raw_resource TEXT, reply TEXT,
                asked_at INTEGER, replied_at INTEGER, wait_ms INTEGER,
                source_tool TEXT, source_message_id TEXT, save_patterns TEXT,
                save_reusable INTEGER, contract_version INTEGER NOT NULL DEFAULT 1
            );
            """
        )
        connection.execute(
            "INSERT INTO permission_contract VALUES (1, 1, 'salt', ?)",
            (days_ago(span_days),),
        )
        for index in range(events):
            asked = (
                days_ago(span_days - index * (span_days / max(events - 1, 1)))
                + 3_600_000
            )
            connection.execute(
                "INSERT INTO permission_events VALUES (?, ?, 'p1', 'build',"
                " 'model-a', 'shell', 'git push', 'hash', NULL, 'always', ?, ?,"
                " 60000, 'tool', 'msg', '[\"git push *\"]', 1, 1)",
                (
                    f"per_{index}",
                    f"ses_metric_{index % session_count}",
                    asked,
                    asked + 60_000,
                ),
            )
    connection.commit()
    connection.close()


class SessionInsightsTestCase(unittest.TestCase):
    """Base case with isolated databases, state, and stats."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state = self.root / "state"
        self.opencode_db = self.root / "opencode.db"
        self.metrics_db = self.root / "metrics.db"
        self.stats_file = self.root / "stats.json"
        self.stats_file.write_text(
            json.dumps(
                {
                    "sessions": 4,
                    "prompts": 100,
                    "tools": {"totals": {"calls": 200}},
                }
            ),
            encoding="utf-8",
        )
        self.env = {
            "SESSION_INSIGHTS_STATE_HOME": str(self.state),
            "SESSION_INSIGHTS_OPENCODE_DB": str(self.opencode_db),
            "SESSION_INSIGHTS_METRICS_DB": str(self.metrics_db),
            "SESSION_INSIGHTS_STATS_FILE": str(self.stats_file),
        }

    def analyze(self, **kwargs):
        with patch.dict(os.environ, self.env, clear=False):
            return insights.analyze(**kwargs)


class CanonicalizationTests(unittest.TestCase):
    """Canonical command and path normalization."""

    def test_canonical_command_removes_arguments_and_assignments(self) -> None:
        self.assertEqual(
            insights.canonical_command(
                "GITHUB_TOKEN=ghp_abcdefgh12345678 git push origin feature/secret"
            ),
            "git push",
        )
        self.assertEqual(insights.canonical_command("make test"), "make test")
        self.assertEqual(
            insights.canonical_command("python3 /home/test/script.py"), "python3"
        )
        self.assertEqual(insights.canonical_command("rm -rf /tmp/example"), "rm")

    def test_canonical_command_never_keeps_urls_or_quoted_arguments(self) -> None:
        canonical = insights.canonical_command(
            "curl https://user:pass@example.com/path -H 'Authorization: Bearer abcdefghijklmnop'"
        )
        self.assertEqual(canonical, "curl")
        self.assertNotIn("example.com", canonical)
        self.assertNotIn("Bearer", canonical)

    def test_redact_removes_tokens_keys_and_headers(self) -> None:
        value = (
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz "
            "token=ghp_abcdefgh12345678 "
            "-----BEGIN PRIVATE KEY----- secret -----END PRIVATE KEY-----"
        )
        redacted = insights.redact(value)
        for secret in ("abcdefghijklmnopqrstuvwxyz", "ghp_abcdefgh12345678", "secret"):
            self.assertNotIn(secret, redacted)
        self.assertIn("[REDACTED", redacted)

    def test_path_class_and_extension(self) -> None:
        home_file = str(Path.home() / "project/a.py")
        self.assertEqual(insights.path_class(home_file), ("home", ".py"))
        self.assertEqual(insights.path_class("~/project/a.py"), ("home", ".py"))
        self.assertEqual(insights.path_class("src/a.ts"), ("project", ".ts"))
        self.assertEqual(insights.path_class("/etc/passwd"), ("system", "none"))
        self.assertEqual(insights.path_class("/tmp/x.env"), ("tmp", ".env"))
        self.assertEqual(insights.path_class("/opt/data.json"), ("external", ".json"))

    def test_path_key_distinguishes_files_with_the_same_extension(self) -> None:
        self.assertNotEqual(
            insights.path_key("src/a.py"), insights.path_key("src/b.py")
        )
        self.assertEqual(
            insights.path_key("src/../src/a.py"), insights.path_key("src/a.py")
        )

    def test_model_label_renders_provider_model_and_variant(self) -> None:
        self.assertEqual(
            insights.model_label(
                '{"id":"gpt-6.1-sol","providerID":"complytime","variant":"medium"}'
            ),
            "complytime/gpt-6.1-sol#medium",
        )
        self.assertEqual(insights.model_label("plain-model"), "plain-model")

    def test_distinct_files_are_not_duplicate_reads(self) -> None:
        calls = [
            {
                "session_id": "s1",
                "name": "read",
                "path": "src/a.py",
                "command": None,
                "start": 1,
                "end": 2,
            },
            {
                "session_id": "s1",
                "name": "read",
                "path": "src/b.py",
                "command": None,
                "start": 3,
                "end": 4,
            },
        ]
        result = insights.waste_finding(calls, None, None, "aggregate", False, 30)
        self.assertEqual(result["status"], "no_data")

        calls.append(dict(calls[0]))
        result = insights.waste_finding(calls, None, None, "aggregate", False, 30)
        self.assertEqual(result["evidence"]["duplicate_reads"], 1)


class ScorecardTests(SessionInsightsTestCase):
    """Scorecard aggregation, privacy, and degradation."""

    def test_legacy_schema_produces_five_classes(self) -> None:
        create_legacy_db(self.opencode_db)
        create_metrics_db(self.metrics_db)
        scorecard = self.analyze(days=30)
        classes = {finding["class"] for finding in scorecard["findings"]}
        self.assertEqual(
            classes,
            {
                "permission_friction",
                "confirmation_stalls",
                "latency",
                "waste",
                "permission_policy_drift",
            },
        )
        self.assertFalse(scorecard["clean"])
        self.assertGreaterEqual(scorecard["coverage"]["sessions"], 4)
        self.assertEqual(scorecard["sources"][1]["status"], "ok")

    def test_v2_schema_produces_findings(self) -> None:
        create_v2_db(self.opencode_db)
        create_metrics_db(self.metrics_db)
        scorecard = self.analyze(days=30)
        confirmation = next(
            item
            for item in scorecard["findings"]
            if item["id"] == "confirmation_stalls"
        )
        latency = next(
            item for item in scorecard["findings"] if item["id"] == "latency"
        )
        self.assertGreater(confirmation["events"], 0)
        self.assertGreater(latency["events"], 0)
        self.assertIn("excluded_outliers", latency["evidence"])

    def test_v2_message_content_tool_calls_are_loaded(self) -> None:
        create_v2_message_only_db(self.opencode_db)
        create_metrics_db(self.metrics_db)
        scorecard = self.analyze(days=30)
        confirmation = next(
            item
            for item in scorecard["findings"]
            if item["id"] == "confirmation_stalls"
        )
        latency = next(
            item for item in scorecard["findings"] if item["id"] == "latency"
        )
        self.assertGreaterEqual(confirmation["events"], 12)
        self.assertGreaterEqual(latency["evidence"]["task_calls"], 12)
        self.assertEqual(latency["evidence"]["measured_calls"], 12)

    def test_aggregate_report_contains_no_paths_secrets_or_urls(self) -> None:
        create_legacy_db(self.opencode_db)
        create_metrics_db(self.metrics_db, with_contract=True, events=40)
        scorecard = self.analyze(days=30)
        payload = json.dumps(scorecard)
        for forbidden in (
            "/home/test",
            "ghp_abcdefgh12345678",
            "https://",
            "feature/secret",
        ):
            self.assertNotIn(forbidden, payload)
        self.assertNotIn("patterns", scorecard["findings"][0]["evidence"])

    def test_missing_metrics_source_degrades_gracefully(self) -> None:
        create_legacy_db(self.opencode_db)
        scorecard = self.analyze(days=30)
        metrics_source = next(
            item for item in scorecard["sources"] if item["name"] == "metrics"
        )
        self.assertEqual(metrics_source["status"], "missing")
        friction = next(
            item
            for item in scorecard["findings"]
            if item["id"] == "permission_friction"
        )
        self.assertEqual(friction["confidence"], "low")
        self.assertFalse(friction["proposable"])
        self.assertIn("unavailable", friction["note"])

    def test_capture_absence_reduces_confidence(self) -> None:
        create_legacy_db(self.opencode_db, session_count=4)
        create_metrics_db(
            self.metrics_db,
            session_count=4,
            prompts=400,
            turns=1000,
            with_contract=False,
        )
        scorecard = self.analyze(days=30)
        friction = next(
            item
            for item in scorecard["findings"]
            if item["id"] == "permission_friction"
        )
        self.assertEqual(friction["confidence"], "medium")
        self.assertTrue(friction["proposable"])
        self.assertEqual(friction["evidence"]["source"], "session_metrics")
        self.assertIn("confidence is reduced", friction["note"])

    def test_capture_events_raise_friction_confidence(self) -> None:
        create_legacy_db(self.opencode_db)
        create_metrics_db(self.metrics_db, with_contract=True, events=40, prompts=0)
        scorecard = self.analyze(days=30)
        friction = next(
            item
            for item in scorecard["findings"]
            if item["id"] == "permission_friction"
        )
        self.assertEqual(friction["evidence"]["source"], "permission_events")
        self.assertEqual(friction["confidence"], "high")
        self.assertTrue(friction["proposable"])

    def test_low_confidence_findings_are_not_proposed(self) -> None:
        create_legacy_db(self.opencode_db, session_count=1)
        create_metrics_db(
            self.metrics_db, session_count=1, with_contract=True, events=40
        )
        scorecard = self.analyze(days=30)
        for finding in scorecard["findings"]:
            if finding["confidence"] == "low":
                self.assertFalse(finding["proposable"])
                self.assertIsNone(finding["proposal"])

    def test_patterns_detail_exposes_only_canonical_heads(self) -> None:
        create_legacy_db(self.opencode_db)
        create_metrics_db(self.metrics_db, with_contract=True, events=40)
        scorecard = self.analyze(days=30, detail="patterns")
        payload = json.dumps(scorecard)
        self.assertNotIn("/home/test", payload)
        self.assertNotIn("ghp_abcdefgh12345678", payload)
        friction = scorecard["findings"][0]
        self.assertIn("patterns", friction["evidence"])

    def test_snippets_require_allow_content(self) -> None:
        with self.assertRaises(ValueError):
            self.analyze(days=30, detail="snippets")
        create_legacy_db(self.opencode_db)
        create_metrics_db(self.metrics_db, with_contract=True, events=40)
        scorecard = self.analyze(days=30, detail="snippets", allow_content=True)
        payload = json.dumps(scorecard)
        self.assertNotIn("ghp_abcdefgh12345678", payload)
        self.assertNotIn("/home/test", payload)

    def test_reports_are_private(self) -> None:
        create_legacy_db(self.opencode_db)
        create_metrics_db(self.metrics_db)
        scorecard = self.analyze(days=30, save_report=True)
        report_dir = self.state / "reports"
        self.assertEqual(stat.S_IMODE(report_dir.stat().st_mode), 0o700)
        report_file = report_dir / scorecard["report"]["json"]
        self.assertEqual(stat.S_IMODE(report_file.stat().st_mode), 0o600)
        persisted = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(persisted["detail"], "aggregate")


class VerificationTests(SessionInsightsTestCase):
    """Intervention ledger and baseline comparison."""

    def setUp(self) -> None:
        super().setUp()
        create_legacy_db(self.opencode_db)
        create_metrics_db(
            self.metrics_db,
            session_count=4,
            prompts=50,
            turns=200,
            with_contract=True,
            events=40,
        )

    def record(self, baseline_value: float) -> dict:
        with patch.dict(os.environ, self.env, clear=False):
            return insights.record_intervention(
                {
                    "target": "role",
                    "change_ref": "openspec/changes/example",
                    "hypothesis": "Narrow rules reduce prompts",
                    "metric": "permission_prompts",
                    "baseline": {
                        "start": "2026-10-01T00:00:00Z",
                        "end": "2026-10-31T00:00:00Z",
                        "value": baseline_value,
                        "sessions": 4,
                    },
                    "expected_direction": "decrease",
                    "review_date": "2026-12-01",
                }
            )

    def test_keep_revert_and_extend(self) -> None:
        keep = self.record(100)
        revert = self.record(40)
        extend = self.record(52)
        with patch.dict(os.environ, self.env, clear=False):
            results = insights.verify_interventions(days=30)
        by_id = {result["id"]: result for result in results}
        self.assertEqual(by_id[keep["id"]]["recommendation"], "keep")
        self.assertEqual(by_id[revert["id"]]["recommendation"], "revert")
        self.assertEqual(by_id[extend["id"]]["recommendation"], "extend")

    def test_insufficient_follow_up_data(self) -> None:
        intervention = self.record(100)
        with patch.dict(os.environ, self.env, clear=False):
            results = insights.verify_interventions(
                intervention_id=intervention["id"], project="no-such-project"
            )
        self.assertEqual(results[0]["recommendation"], "insufficient-data")
        self.assertIsNone(results[0]["change_percent"])

    def test_ledger_is_private_and_contains_no_raw_content(self) -> None:
        intervention = self.record(100)
        ledger = self.state / "interventions.json"
        self.assertEqual(stat.S_IMODE(ledger.stat().st_mode), 0o600)
        payload = ledger.read_text(encoding="utf-8")
        self.assertNotIn("/home/test", payload)
        self.assertIn(intervention["id"], payload)


if __name__ == "__main__":
    unittest.main()
