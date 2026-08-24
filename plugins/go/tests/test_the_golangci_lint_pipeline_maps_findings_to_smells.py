"""``findings()`` maps each golangci-lint v2 ``Issue`` to a canonical finding:
map by linter + text to a smell, group by smell, and shape each group into the
canonical finding — the walking skeleton, built up in the inner TDD loop.

``base`` is the directory golangci-lint anchored each ``Pos.Filename`` to (the
directory of the config that ran); the pure tests never assert on ``key`` or
``file``, so ``Path(".")`` is enough for them.

These exercise the pure mapping logic with synthetic golangci-lint-JSON-shaped
entries (v2 field names: ``FromLinter``, ``Text``, ``Pos.Filename``,
``Pos.Line``, ``Pos.Column``) rather than spawning the real tool, which the
acceptance spec does instead.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from golangci_lint_sensor import SMELL_BY_LINTER, findings

_BASE = Path(".")


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
    assert findings([], _BASE) == []


def test_many_entries_group_by_smell_sorted_alphabetically() -> None:
    """Insertion order is deliberately the reverse of the alphabetical group
    order, so a test that merely preserved input order would still pass unless
    the sort is checked."""
    unused_variable = _entry("ineffassign", filename="b.go")
    high_complexity = _entry("gocyclo", filename="a.go")

    result = findings([unused_variable, high_complexity], _BASE)

    assert [finding["smell"] for finding in result] == [
        "high-complexity",
        "unused-variable",
    ]


def test_two_issues_for_the_same_smell_share_one_finding() -> None:
    first = _entry("gocyclo", filename="a.go", line=1)
    second = _entry("gocyclo", filename="a.go", line=2)

    result = findings([first, second], _BASE)

    assert len(result) == 1
    assert [issue["details"]["line"] for issue in result[0]["issues"]] == [1, 2]


@pytest.mark.parametrize("linter", sorted(SMELL_BY_LINTER))
def test_every_mapped_linter_reaches_its_own_smell(linter: str) -> None:
    result = findings([_entry(linter)], _BASE)

    assert [finding["smell"] for finding in result] == [SMELL_BY_LINTER[linter]]
    assert result[0]["issues"][0]["details"]["source"] == f"golangci-lint:{linter}"


def test_errcheck_is_unchecked_error() -> None:
    """errcheck reports a call whose error return is discarded, and every one of
    its findings is an unchecked return — no text ambiguity — so it maps straight
    from the linter table to ``unchecked-error``. Hardcoded rather than relying on
    the ``SMELL_BY_LINTER`` parametrization, so adding the table entry is what
    turns it green."""
    result = findings([_entry("errcheck")], _BASE)

    assert [finding["smell"] for finding in result] == ["unchecked-error"]
    assert result[0]["issues"][0]["details"]["source"] == "golangci-lint:errcheck"


def test_unused_with_var_prefix_is_unused_variable() -> None:
    entry = _entry("unused")
    entry["Text"] = "var x is unused"

    result = findings([entry], _BASE)

    assert [finding["smell"] for finding in result] == ["unused-variable"]
    assert result[0]["issues"][0]["details"]["source"] == "golangci-lint:unused"


def test_unused_with_func_prefix_is_forwarded_as_uncoached() -> None:
    entry = _entry("unused")
    entry["Text"] = "func foo is unused"

    result = findings([entry], _BASE)

    assert [finding["smell"] for finding in result] == ["unused"]
    assert result[0]["issues"][0]["details"]["source"] == "golangci-lint:unused"


def test_typecheck_with_imported_and_not_used_is_unused_import() -> None:
    entry = _entry("typecheck")
    entry["Text"] = 'main.go:5:2: imported and not used: "fmt"'

    result = findings([entry], _BASE)

    assert [finding["smell"] for finding in result] == ["unused-import"]
    assert result[0]["issues"][0]["details"]["source"] == "golangci-lint:typecheck"


def test_typecheck_with_other_text_is_parse_error() -> None:
    entry = _entry("typecheck")
    entry["Text"] = "main.go:3:1: expected declaration, found '}'"

    result = findings([entry], _BASE)

    assert [finding["smell"] for finding in result] == ["parse-error"]
    assert result[0]["issues"][0]["details"]["source"] == "golangci-lint:typecheck"
