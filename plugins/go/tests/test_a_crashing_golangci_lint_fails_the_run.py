"""A broken ``golangci-lint`` must not read as clean — it must fail the sensor.

``golangci_lint_crashed`` trusts exactly golangci-lint's own contract (0 clean,
1 issues found); every other exit code — a flag error (2), tool not found
(127), or a killed process (-9) — is a crash, mirroring
``test_a_crashing_ruff_fails_the_run``.
"""

from __future__ import annotations

import subprocess

import pytest
from golangci_lint_sensor import golangci_lint_crashed


def _result(returncode: int) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr="")


@pytest.mark.parametrize("returncode", [0, 1])
def test_golangci_lint_s_own_exit_codes_are_trusted(returncode: int) -> None:
    assert golangci_lint_crashed(_result(returncode)) is False


@pytest.mark.parametrize("returncode", [2, 127, -9])
def test_any_other_exit_code_is_a_crash(returncode: int) -> None:
    assert golangci_lint_crashed(_result(returncode)) is True
