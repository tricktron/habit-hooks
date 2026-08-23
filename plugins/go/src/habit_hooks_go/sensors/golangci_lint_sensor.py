"""Run golangci-lint and print canonical findings.

STUB — scaffolded so the acceptance test compiles and fails on its assertion
rather than on missing files. The real pipeline (split argv -> config check ->
run via tool_spawn -> parse JSON -> map by linter + text -> group by smell) is
built out in the inner TDD loop.
"""

from __future__ import annotations

import sys

SMELL_BY_LINTER = {
    "gocyclo": "high-complexity",
    "funlen": "oversized-function",
    "ineffassign": "unused-variable",
}


def smell_of(linter: str, text: str) -> str | None:
    if linter in SMELL_BY_LINTER:
        return SMELL_BY_LINTER[linter]
    if linter == "unused" and text.startswith("var "):
        return "unused-variable"
    if linter == "typecheck":
        if "imported and not used" in text:
            return "unused-import"
        return "parse-error"
    return None


def issue(entry: dict) -> dict:
    return {
        "key": entry["Pos"]["Filename"],
        "details": {
            "file": entry["Pos"]["Filename"],
            "line": entry["Pos"]["Line"],
            "column": entry["Pos"]["Column"],
            "message": entry["Text"],
            "source": "golangci-lint:" + entry["FromLinter"],
        },
    }


def findings(entries: list[dict]) -> list[dict]:
    by_smell: dict[str, list[dict]] = {}
    for entry in entries:
        smell = smell_of(entry["FromLinter"], entry["Text"])
        if smell is None:
            continue
        by_smell.setdefault(smell, []).append(entry)
    return [
        {
            "smell": smell,
            "details": {},
            "issues": [issue(entry) for entry in by_smell[smell]],
        }
        for smell in sorted(by_smell)
    ]


def main() -> int:
    # STUB: not yet implemented. Exits 2 (a crash, not a clean run) so the
    # acceptance test fails on its expected output, never on an import error.
    sys.stderr.write("golangci_lint_sensor: not yet implemented\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
