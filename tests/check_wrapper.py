"""Exercise rendered launchers with dummy keys and a fake OpenCode executable."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main() -> None:
    default_wrapper, configured_wrapper, key_file = map(Path, sys.argv[1:])
    with tempfile.TemporaryDirectory(prefix="opencode-wrapper-test-") as directory:
        mock_dir = Path(directory)
        marker = mock_dir / "started"
        mock = mock_dir / "opencode"
        mock.write_text(
            f"#!{sys.executable}\n"
            "import os, pathlib, sys\n"
            "pathlib.Path(os.environ['TEST_MARKER']).touch()\n"
            "assert os.environ.get('ENMAAS_KEY') == os.environ['TEST_EXPECTED_KEY']\n"
            "assert sys.argv[1:] == ['--standalone', 'project with spaces']\n"
        )
        mock.chmod(0o700)

        def launch(wrapper: Path, expected: str, succeeds: bool = True) -> None:
            marker.unlink(missing_ok=True)
            environment = {
                **os.environ,
                "PATH": f"{mock_dir}{os.pathsep}{os.environ['PATH']}",
                "ENMAAS_KEY": "inherited-test-key",
                "TEST_EXPECTED_KEY": expected,
                "TEST_MARKER": str(marker),
            }
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

    print("Wrapper checks passed: inherited key, runtime loading, rotation, arguments, empty/missing file.")


if __name__ == "__main__":
    main()
