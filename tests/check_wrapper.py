"""Exercise rendered launchers with dummy keys and a fake OpenCode executable."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main() -> None:
    default_wrapper, configured_wrapper, key_file, vertex_wrapper, vertex_creds = map(Path, sys.argv[1:])
    with tempfile.TemporaryDirectory(prefix="opencode-wrapper-test-") as directory:
        mock_dir = Path(directory)
        marker = mock_dir / "started"
        mock = mock_dir / "opencode"
        mock.write_text(
            f"#!{sys.executable}\n"
            "import os, pathlib, sys\n"
            "pathlib.Path(os.environ['TEST_MARKER']).touch()\n"
            "assert os.environ.get('ENMAAS_KEY') == os.environ['TEST_EXPECTED_KEY']\n"
            "assert os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') == os.environ.get('TEST_EXPECTED_VERTEX_CREDS')\n"
            "assert sys.argv[1:] == ['--standalone', 'project with spaces']\n"
        )
        mock.chmod(0o700)

        def launch(wrapper: Path, expected: str, succeeds: bool = True, expected_creds: str | None = None) -> None:
            marker.unlink(missing_ok=True)
            environment = {
                **os.environ,
                "PATH": f"{mock_dir}{os.pathsep}{os.environ['PATH']}",
                "ENMAAS_KEY": "inherited-test-key",
                "TEST_EXPECTED_KEY": expected,
                "TEST_MARKER": str(marker),
            }
            environment.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            if expected_creds is not None:
                environment["TEST_EXPECTED_VERTEX_CREDS"] = expected_creds
            result = subprocess.run(
                [str(wrapper), "--standalone", "project with spaces"],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            assert (result.returncode == 0) == succeeds, result.stderr
            assert marker.exists() == succeeds, "Unexpected OpenCode launch state"
            assert result.stdout == "", "Launcher unexpectedly wrote to stdout"

        launch(default_wrapper, "inherited-test-key")
        # Shell metacharacters are literal key content, never sourced/evaluated.
        for key in ["dummy-$key-$(exit 99)-'quoted'", "rotated-dummy-key"]:
            key_file.write_text(key + "\n")
            key_file.chmod(0o600)
            launch(configured_wrapper, key)
            assert key not in configured_wrapper.read_text(), "Key embedded in launcher"

        key_file.write_text("")
        launch(configured_wrapper, "", succeeds=False)
        key_file.unlink()
        launch(configured_wrapper, "", succeeds=False)

        # The vertex launcher exports only the expanded credentials path; the
        # other launchers must not export it at all. The path contains an
        # apostrophe, so the export is shell-quoted; the launch round-trip
        # below proves the quoting reproduces the exact path in the environment.
        for wrapper in (default_wrapper, configured_wrapper):
            assert "GOOGLE_APPLICATION_CREDENTIALS" not in wrapper.read_text(), "Unexpected credentials export"
        vertex_text = vertex_wrapper.read_text()
        assert "export GOOGLE_APPLICATION_CREDENTIALS=" in vertex_text, "Missing credentials export"
        assert "~/" not in vertex_text, "Credentials path not expanded"
        launch(vertex_wrapper, "inherited-test-key", expected_creds=str(vertex_creds))

    print("Wrapper checks passed: inherited key, runtime loading, rotation, arguments, empty/missing file, vertex credentials path.")


if __name__ == "__main__":
    main()
