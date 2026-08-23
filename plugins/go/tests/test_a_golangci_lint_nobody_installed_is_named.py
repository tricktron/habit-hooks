"""A detector this plugin does not bring with it must still answer in one line.

``pip install habit-hooks-go`` installs neither golangci-lint nor any other
tool, so a machine that has just enabled the plugin is the ordinary case, not
the edge one. An absent tool is a ``FileNotFoundError`` — twenty lines of
internals would otherwise become the sensor's diagnosis (#114). Mirrors
``test_a_ruff_nobody_installed_is_named.py``.

The sensor short-circuits to an empty findings list when no files are passed
(no scope = no work), so the test passes ``-- main.go`` to reach the spawn
where the missing tool is caught and named.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SENSOR = (
    Path(__file__).resolve().parents[1]
    / "src/habit_hooks_go" / "sensors" / "golangci_lint_sensor.py"
)


def test_a_golangci_lint_nobody_installed_answers_the_way_a_shell_does(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [sys.executable, str(SENSOR), "--", "main.go"],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env={"PATH": "/nonexistent"},
    )

    assert result.returncode == 2
    assert result.stdout.strip() == ""
    assert result.stderr.strip() == "golangci-lint: command not found"
