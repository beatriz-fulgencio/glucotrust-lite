import json
import os
from pathlib import Path
import subprocess


def test_devcontainer_setup_stops_on_installation_failure(tmp_path):
    # No network or actual package installation: a failing Python executable
    # stands in for pip's first failed install.
    executable = tmp_path / "python"
    executable.write_text('#!/bin/sh\nprintf "invoked\\n" >> "$SETUP_TEST_LOG"\nexit 23\n')
    executable.chmod(0o700)
    log = tmp_path / "calls"
    environment = {**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
                   "SETUP_TEST_LOG": str(log)}
    configuration = json.loads(Path(".devcontainer/devcontainer.json").read_text())
    result = subprocess.run(configuration["updateContentCommand"].split(), env=environment,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 23
    assert log.read_text().splitlines() == ["invoked"]
