# SPDX-License-Identifier: Apache-2.0
"""Offline workflow tests: no GitHub mutation, credentials, or project framework."""

import copy
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "files/scripts/pr_workflow.py"
SPEC = importlib.util.spec_from_file_location("pr_workflow", HELPER)
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)
HEAD = "a" * 40
BASE = "b" * 40
PATCH = "@@ -1,2 +1,3 @@\n unchanged\n-old\n+new\n+extra\n"


def metadata() -> dict:
    return {
        "number": 42,
        "html_url": "https://github.com/example/project/pull/42",
        "base": {"ref": "main", "sha": BASE},
        "head": {
            "ref": "feature",
            "sha": HEAD,
            "repo": {"full_name": "example/project"},
        },
        "changed_files": 1,
        "updated_at": "2026-11-10T00:00:00Z",
        "user": {"login": "author"},
        "title": "Fix",
        "body": "Fixes #1",
    }


def thread() -> dict:
    return {
        "id": "thread-1",
        "isResolved": False,
        "isOutdated": False,
        "path": "main.py",
        "line": 2,
        "originalLine": 2,
        "comments": [
            {
                "id": "comment-1",
                "databaseId": 123,
                "body": "Check this",
                "updatedAt": "today",
                "author": {"login": "reviewer"},
            }
        ],
    }


class FakeGitHub:
    host = "github.com"
    repository = "example/project"
    prefix = "repos/example/project"

    def __init__(self) -> None:
        self.before = metadata()
        self.after = metadata()
        self.metadata_calls = 0
        self.fail = None
        self.files = [
            {"filename": "main.py", "additions": 2, "deletions": 1, "patch": PATCH}
        ]

    def metadata(self, number: int) -> dict:
        self.metadata_calls += 1
        return self.before if self.metadata_calls == 1 else self.after

    def api(self, endpoint: str, **kwargs: object) -> object:
        if endpoint == self.prefix:
            return {"id": 100}
        if endpoint == "user":
            return {"login": "viewer"}
        if kwargs.get("raw"):
            return PATCH
        raise AssertionError(endpoint)

    def listing(self, endpoint: str, key: str | None = None) -> list:
        if self.fail and self.fail in endpoint:
            raise ValueError("API failure: 403 forbidden")
        if "/files?" in endpoint:
            return self.files
        return []

    def threads(self, number: int) -> list[dict]:
        return [thread()]


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        environment = patch.dict(
            os.environ, {"XDG_STATE_HOME": str(self.root / "state")}
        )
        environment.start()
        self.addCleanup(environment.stop)
        self.github = FakeGitHub()

    def snapshot(self) -> dict:
        result = workflow.capture(self.github, 42)
        return workflow.load_snapshot(result["snapshot_path"])

    def test_complete_snapshot_private_files_and_immutable_inputs(self) -> None:
        snapshot = self.snapshot()
        self.assertEqual(snapshot["context"]["head_sha"], HEAD)
        self.assertEqual(snapshot["files"][0]["additions"], 2)
        self.assertTrue(snapshot["threads"][0]["comments"])
        first_path = snapshot["snapshot_path"]
        for path in (Path(first_path), Path(snapshot["diff_path"])):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        for directory in [
            Path(first_path).parent,
            *list(Path(first_path).parents)[1:4],
        ]:
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        self.github.metadata_calls = 0
        second = self.snapshot()
        self.assertNotEqual(first_path, second["snapshot_path"])
        self.assertEqual(workflow.load_snapshot(first_path), snapshot)

    def test_capture_rejects_incomplete_data_without_snapshot(self) -> None:
        for failure in ("files", "reviews", "comments", "check-runs", "statuses"):
            with self.subTest(failure=failure):
                self.github = FakeGitHub()
                self.github.fail = failure
                with self.assertRaisesRegex(ValueError, "API failure"):
                    workflow.capture(self.github, 42)
        self.assertFalse(list(self.root.rglob("snapshot-*.json")))

    def test_capture_rejects_moving_head_base_and_inventory_limit(self) -> None:
        for field in ("head", "base"):
            with self.subTest(field=field):
                self.github = FakeGitHub()
                self.github.after[field]["sha"] = "c" * 40
                with self.assertRaisesRegex(ValueError, "context changed"):
                    workflow.capture(self.github, 42)
        self.github = FakeGitHub()
        self.github.before["changed_files"] = 3001
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            workflow.capture(self.github, 42)
        self.assertFalse(list(self.root.rglob("snapshot-*.json")))

    def test_capture_rejects_bad_sha_and_updated_pr(self) -> None:
        self.github.before["head"]["sha"] = "main"
        with self.assertRaisesRegex(ValueError, "immutable"):
            workflow.capture(self.github, 42)
        self.github = FakeGitHub()
        self.github.after["updated_at"] = "tomorrow"
        with self.assertRaisesRegex(ValueError, "changed during ingestion"):
            workflow.capture(self.github, 42)

    def test_diff_tampering_is_detected(self) -> None:
        snapshot = self.snapshot()
        Path(snapshot["diff_path"]).write_text("changed")
        with self.assertRaisesRegex(ValueError, "Saved diff changed"):
            workflow.load_snapshot(snapshot["snapshot_path"])

    def test_state_revision_conflicts_and_stale_context(self) -> None:
        snapshot = self.snapshot()
        incoming = {
            "snapshot_path": snapshot["snapshot_path"],
            "revision": 0,
            "items": [{"decision": "accept"}],
            "actions": [{"id": 1}],
        }
        result = workflow.save_journal(snapshot, "address_feedback", incoming)
        saved = workflow.read_json(result["journal_path"])
        self.assertEqual(saved["revision"], 1)
        self.assertEqual(saved["actions"], [{"id": 1}])
        with self.assertRaisesRegex(ValueError, "revision changed"):
            workflow.save_journal(snapshot, "address_feedback", incoming)
        self.github = FakeGitHub()
        self.github.before["head"]["sha"] = "c" * 40
        self.github.after["head"]["sha"] = "c" * 40
        newer = self.snapshot()
        output = self.cli(
            "state-show",
            "--snapshot",
            newer["snapshot_path"],
            "--command",
            "address_feedback",
        )
        self.assertFalse(json.loads(output.stdout)["context_matches"])

    def test_invalid_journal_and_cached_consent_rejected(self) -> None:
        snapshot = self.snapshot()
        for extra in (
            {"confirmed": True},
            {"items": [{"decision": "defer"}]},
            {"items": ["invalid"]},
            {"snapshot_path": "other"},
        ):
            with self.subTest(extra=extra):
                incoming = {
                    "snapshot_path": snapshot["snapshot_path"],
                    "revision": 0,
                    **extra,
                }
                with self.assertRaises(ValueError):
                    workflow.save_journal(snapshot, "address_feedback", incoming)

    def test_reply_endpoint_literal_text_and_crash_reconciliation(self) -> None:
        snapshot = self.snapshot()
        body = "Literal $(touch /bad); 'quoted'\n```suggestion\nnew\n```"
        reply = workflow.prepare_reply(snapshot, body, "thread-1")
        self.assertTrue(reply["endpoint"].endswith("/pulls/42/comments/123/replies"))
        self.assertIn(body, reply["payload"]["body"])
        self.assertFalse(reply["already_posted"])
        snapshot["threads"][0]["comments"].append(
            {
                "body": reply["payload"]["body"],
                "author": {"login": "viewer"},
                "id": "posted",
            }
        )
        recovered = workflow.prepare_reply(snapshot, body, "thread-1")
        self.assertTrue(recovered["already_posted"])
        self.assertEqual(recovered["receipts"][0]["id"], "posted")
        self.assertEqual(recovered["payload"], reply["payload"])
        self.assertFalse(
            workflow.prepare_reply(snapshot, "different", "thread-1")["already_posted"]
        )

    def test_general_reply_and_invalid_thread(self) -> None:
        snapshot = self.snapshot()
        self.assertTrue(
            workflow.prepare_reply(snapshot, "why?", None)["endpoint"].endswith(
                "/issues/42/comments"
            )
        )
        for target in ("unknown", "thread-1"):
            snapshot["threads"][0]["isResolved"] = True
            with self.assertRaises(ValueError):
                workflow.prepare_reply(snapshot, "why?", target)
        with self.assertRaises(ValueError):
            workflow.prepare_reply(snapshot, "  ", None)

    def test_body_limits_and_inline_count(self) -> None:
        snapshot = self.snapshot()
        self.assertIsNone(workflow.validate_body("A" * workflow.MAX_BODY_BYTES))
        for body in ("é" * workflow.MAX_BODY_BYTES, None, " "):
            with self.subTest(body_type=type(body)), self.assertRaises(ValueError):
                workflow.validate_body(body)
        with self.assertRaises(ValueError):
            workflow.prepare_reply(snapshot, "A" * (workflow.MAX_BODY_BYTES + 1), None)
        with self.assertRaises(ValueError):
            workflow.prepare_review(
                snapshot,
                {
                    "event": "COMMENT",
                    "body": "ok",
                    "comments": [{}] * 16,
                },
            )

    def test_check_head_cli_accepts_only_exact_context(self) -> None:
        snapshot = self.snapshot()
        arguments = [
            "pr_workflow.py",
            "check-head",
            "--snapshot",
            snapshot["snapshot_path"],
        ]
        with (
            patch.object(sys, "argv", arguments),
            patch.object(workflow, "GitHub", return_value=self.github),
            patch("builtins.print") as output,
        ):
            workflow.main()
        self.assertTrue(json.loads(output.call_args.args[0])["unchanged"])
        self.github.after["head"]["sha"] = "c" * 40
        with (
            patch.object(sys, "argv", arguments),
            patch.object(workflow, "GitHub", return_value=self.github),
        ):
            with self.assertRaisesRegex(ValueError, "context changed"):
                workflow.main()

    def test_review_payload_binds_head_and_reconciles(self) -> None:
        snapshot = self.snapshot()
        incoming = {
            "event": "REQUEST_CHANGES",
            "body": "Fix error handling",
            "comments": [
                {
                    "path": "main.py",
                    "line": 2,
                    "side": "RIGHT",
                    "body": "Check the error",
                },
            ],
        }
        review = workflow.prepare_review(snapshot, incoming)
        self.assertEqual(review["payload"]["commit_id"], HEAD)
        self.assertEqual(review["payload"]["event"], "REQUEST_CHANGES")
        self.assertFalse(review["already_posted"])
        snapshot["reviews"].append(
            {"body": review["payload"]["body"], "user": {"login": "viewer"}, "id": 9}
        )
        self.assertTrue(workflow.prepare_review(snapshot, incoming)["already_posted"])

    def test_review_rejects_invalid_event_location_and_self_approval(self) -> None:
        snapshot = self.snapshot()
        bad = [
            {"event": "MERGE", "body": "bad"},
            {"event": "APPROVE", "body": " "},
            {
                "event": "COMMENT",
                "body": "ok",
                "comments": [
                    {"path": "outside.py", "line": 2, "side": "RIGHT", "body": "bad"}
                ],
            },
            {
                "event": "COMMENT",
                "body": "ok",
                "comments": [
                    {"path": "main.py", "line": 1, "side": "RIGHT", "body": "context"}
                ],
            },
            {"event": "COMMENT", "body": "ok", "comments": [None]},
            {
                "event": "COMMENT",
                "body": "ok",
                "comments": [
                    {"path": "main.py", "line": 2, "side": "LEFT", "body": "bad"}
                ],
            },
        ]
        for incoming in bad:
            with self.subTest(incoming=incoming), self.assertRaises(ValueError):
                workflow.prepare_review(snapshot, incoming)
        snapshot["viewer"] = snapshot["author"]
        with self.assertRaisesRegex(ValueError, "Authors cannot"):
            workflow.prepare_review(snapshot, {"event": "APPROVE", "body": "ok"})
        self.assertEqual(
            workflow.prepare_review(snapshot, {"event": "COMMENT", "body": "ok"})[
                "payload"
            ]["event"],
            "COMMENT",
        )

    def test_symlink_and_relative_state_refused(self) -> None:
        target = self.root / "actual"
        target.mkdir()
        link = self.root / "link"
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            workflow.atomic_write(link / "nested/result.json", "{}")
        with patch.dict(os.environ, {"XDG_STATE_HOME": "relative"}):
            with self.assertRaisesRegex(ValueError, "absolute"):
                workflow.capture(self.github, 42)

    def cli(self, *arguments: str) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [sys.executable, str(HELPER), *arguments],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_cli_prepares_private_json_without_executing_body(self) -> None:
        snapshot = self.snapshot()
        body = self.root / "body.txt"
        marker = self.root / "must-not-exist"
        body.write_text(f"$(touch {marker})")
        output = self.root / "reply.json"
        result = self.cli(
            "reply",
            "--snapshot",
            snapshot["snapshot_path"],
            "--thread",
            "thread-1",
            "--input",
            str(body),
            "--output",
            str(output),
        )
        self.assertFalse(json.loads(result.stdout)["already_posted"])
        self.assertIn(body.read_text(), workflow.read_json(output)["body"])
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
        self.assertFalse(marker.exists())


class GitHubPaginationTests(unittest.TestCase):
    def test_rest_pagination_and_no_shell(self) -> None:
        responses = [
            json.dumps(
                {
                    "nameWithOwner": "example/project",
                    "url": "https://github.example.com/example/project",
                }
            ),
            json.dumps([[{"id": 1}], [{"id": 2}]]),
        ]
        with patch.object(workflow, "run", side_effect=responses) as runner:
            github = workflow.GitHub()
            self.assertEqual(
                github.listing("repos/example/project/reviews"), [{"id": 1}, {"id": 2}]
            )
        self.assertIn("--paginate", runner.call_args.args[0])
        self.assertIn("--slurp", runner.call_args.args[0])
        self.assertIn("github.example.com", runner.call_args.args[0])

    def test_thread_and_nested_comment_pagination(self) -> None:
        def connection(nodes: list, more: bool) -> dict:
            return {
                "nodes": nodes,
                "pageInfo": {"hasNextPage": more, "endCursor": "next"},
            }

        first = thread()
        first["comments"] = connection([{"id": "1", "body": "initial"}], True)
        second = copy.deepcopy(first)
        second["id"] = "thread-2"
        second["comments"] = connection([], False)
        responses = [
            {
                "repository": {
                    "pullRequest": {"reviewThreads": connection([first], True)}
                }
            },
            {"node": {"comments": connection([{"id": "2", "body": "reply"}], False)}},
            {
                "repository": {
                    "pullRequest": {"reviewThreads": connection([second], False)}
                }
            },
        ]
        github = object.__new__(workflow.GitHub)
        github.repository = "example/project"
        with patch.object(github, "graphql", side_effect=responses) as query:
            threads = github.threads(42)
        self.assertEqual(len(threads), 2)
        self.assertEqual([c["id"] for c in threads[0]["comments"]], ["1", "2"])
        self.assertEqual(query.call_count, 3)
        changed = copy.deepcopy(threads[0])
        fingerprint = changed.pop("fingerprint")
        self.assertEqual(workflow.digest(changed), fingerprint)
        changed["comments"][0]["body"] = "edited"
        self.assertNotEqual(workflow.digest(changed), fingerprint)

    def test_graphql_errors_and_subprocess_failures(self) -> None:
        github = object.__new__(workflow.GitHub)
        github.host = "github.com"
        with patch.object(
            workflow, "run", return_value='{"errors":[{"message":"denied"}]}'
        ):
            with self.assertRaisesRegex(ValueError, "GraphQL failed"):
                github.graphql("query {}", {})
        result = subprocess.CompletedProcess(["gh"], 1, "", "403 forbidden")
        with patch.object(workflow.subprocess, "run", return_value=result) as runner:
            with self.assertRaisesRegex(ValueError, "403 forbidden"):
                workflow.run(["gh", "api", "user"])
        self.assertNotIn("shell", runner.call_args.kwargs)
        self.assertEqual(runner.call_args.kwargs["timeout"], workflow.TIMEOUT_SECONDS)

    def test_explicit_pr_does_not_detect_branch(self) -> None:
        with (
            patch.object(sys, "argv", ["pr_workflow.py", "snapshot", "--pr", "42"]),
            patch.object(workflow, "GitHub") as github,
            patch.object(workflow, "capture", return_value={"ok": True}) as capture,
            patch.object(
                workflow, "run", side_effect=AssertionError("branch detection")
            ),
            patch("builtins.print"),
        ):
            workflow.main()
        capture.assert_called_once_with(github.return_value, 42)


class CommandContractTests(unittest.TestCase):
    def test_commands_are_standalone_with_explicit_gates(self) -> None:
        for name in ("review_pr", "address_feedback"):
            text = (ROOT / f"files/commands/{name}.md").read_text()
            self.assertIn("$ARGUMENTS", text)
            self.assertIn("pr_workflow.py", text)
            self.assertIn("--input", text)
            self.assertIn("check-head", text)
            self.assertIn("mandatory", text)
            self.assertNotRegex(
                text, r"(?i)\buf\b|unbound.force|divisor|replicator|dewey"
            )
            self.assertIn("No project", text)
        feedback = (ROOT / "files/commands/address_feedback.md").read_text()
        self.assertIn("Stop only at the boundary", feedback)
        self.assertIn("separate confirmation", feedback)


if __name__ == "__main__":
    unittest.main()
