"""``findings()`` maps each golangci-lint v2 ``Issue`` to a canonical finding:
map by linter + text to a smell, group by smell, and shape each group into the
canonical finding — the walking skeleton, built up in the inner TDD loop.

These exercise the pure mapping logic with synthetic golangci-lint-JSON-shaped
entries (v2 field names: ``FromLinter``, ``Text``, ``Pos.Filename``,
``Pos.Line``, ``Pos.Column``) rather than spawning the real tool, which the
acceptance spec does instead.
"""

from __future__ import annotations

import pytest

from golangci_lint_sensor import SMELL_BY_LINTER, findings


def _entry(linter: str = "gocyclo", filename: str = "main.go", line: int = 1) -> dict:
    return {
        "FromLinter": linter,
        "Text": "m",
        "SourceLines": ["func f() {"],
        "Pos": {
            "Filename": filename,
            "Offset": 28,
            "Line": line,
            "Column": 1,
        },
        "ExpectNoLint": False,
        "ExpectedNoLintLinter": "",
    }


def test_zero_issues_is_no_findings() -> None:
    assert findings([]) == []


@pytest.mark.parametrize("linter", sorted(SMELL_BY_LINTER))
def test_every_mapped_linter_reaches_its_own_smell(linter: str) -> None:
    result = findings([_entry(linter)])

    assert [finding["smell"] for finding in result] == [SMELL_BY_LINTER[linter]]
    assert result[0]["issues"][0]["details"]["source"] == f"golangci-lint:{linter}"


def test_unused_with_var_prefix_is_unused_variable() -> None:
    entry = _entry("unused")
    entry["Text"] = "var x is unused"

    result = findings([entry])

    assert [finding["smell"] for finding in result] == ["unused-variable"]
    assert result[0]["issues"][0]["details"]["source"] == "golangci-lint:unused"


def test_unused_with_func_prefix_is_dropped() -> None:
    entry = _entry("unused")
    entry["Text"] = "func foo is unused"

    assert findings([entry]) == []
