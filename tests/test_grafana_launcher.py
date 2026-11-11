# SPDX-License-Identifier: Apache-2.0
"""Exercise the rendered Grafana launcher without starting containers."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
MOCK_PODMAN = """#!/bin/bash
case "$1" in
    ps) echo "${MOCK_RUNNING:-}" ;;
    run) printf '%s\\n' "$@" > "${MOCK_ARGS}" ;;
    rm) exit 0 ;;
    *) exit 1 ;;
esac
"""


class GrafanaLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.data = self.directory / "metrics with spaces"
        self.data.mkdir()
        self.arguments = self.directory / "arguments"
        podman = self.directory / "podman"
        podman.write_text(MOCK_PODMAN)
        podman.chmod(0o755)
        template = Environment(
            undefined=StrictUndefined, keep_trailing_newline=True
        ).from_string((ROOT / "templates/opencode_grafana.sh.j2").read_text())
        self.launcher = self.directory / "opencode-grafana"
        self.launcher.write_text(
            template.render(
                ai_grafana_metrics_container_name="opencode-grafana",
                ai_grafana_metrics_port=3033,
                ai_opencode_metrics_data_dir=str(self.data),
                ai_grafana_metrics_provisioning_dir=str(
                    self.directory / "provisioning"
                ),
                ai_grafana_metrics_image="grafana:test",
                ai_grafana_metrics_sqlite_plugin="frser-sqlite-datasource",
                ai_grafana_metrics_sqlite_plugin_version="4.0.6",
            )
        )
        self.environment = {
            **os.environ,
            "PATH": f"{self.directory}:{os.environ['PATH']}",
            "MOCK_ARGS": str(self.arguments),
            "MOCK_RUNNING": "",
        }

    def start(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(self.launcher), "start"],
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def test_start_maps_host_user_and_migrates_only_named_volume(self) -> None:
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = self.arguments.read_text().splitlines()
        self.assertIn("--userns=keep-id:uid=472,gid=0", arguments)
        self.assertIn("opencode-grafana-data:/var/lib/grafana:U", arguments)
        self.assertIn(f"{self.data}:/data/metrics:rw,Z", arguments)
        mounts = [
            arguments[index + 1] for index, arg in enumerate(arguments) if arg == "-v"
        ]
        for mount in mounts:
            if mount.startswith(str(self.directory)):
                self.assertNotIn("U", mount.rsplit(":", 1)[-1].split(","))

    def test_missing_metrics_directory_does_not_start_container(self) -> None:
        self.data.rmdir()
        result = self.start()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Metrics data directory not found", result.stdout)
        self.assertFalse(self.arguments.exists())

    def test_running_container_is_not_recreated(self) -> None:
        self.environment["MOCK_RUNNING"] = "opencode-grafana"
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already running", result.stdout)
        self.assertFalse(self.arguments.exists())


if __name__ == "__main__":
    unittest.main()
