"""Map golangci-lint v2 issues to canonical findings, grouped by smell.

The pipeline: split argv on the last ``--`` for the project's args and the file
list -> thread the config that wins (a project's own, named in ``args`` or on
disk, before the bundled fallback) through the run -> run via
``golangci_lint_runner`` -> parse the v2 JSON wrapper -> map each issue by
linter + text to a smell -> group by smell. A missing golangci-lint answers in
one line, not a traceback.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from golangci_lint_runner import (
    config_in_force,
    golangci_lint_crashed,
    issues,
    run_golangci_lint,
)

SMELL_BY_LINTER = {
    "gocyclo": "high-complexity",
    "funlen": "oversized-function",
    "ineffassign": "unused-variable",
}

def split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    """``argv``, split on the last literal ``--``: the project's args before it,
    the files to analyse after.

    The template spells ``${args} -- ${files}``, so the separator sits after
    everything ``args`` can contribute and before every file: the *last* ``--``
    is always ours, whatever a project wrote into its args.
    """
    if "--" not in argv:
        return argv, []
    index = len(argv) - 1 - argv[::-1].index("--")
    return argv[:index], argv[index + 1 :]


def smell_of(linter: str, text: str) -> str | None:
    if linter in SMELL_BY_LINTER:
        return SMELL_BY_LINTER[linter]
    if linter == "unused":
        return "unused-variable" if text.startswith("var ") else linter
    if linter == "typecheck":
        return "unused-import" if "imported and not used" in text else "parse-error"
    # Any linter a project enabled that this plugin has no catalogue smell for
    # is forwarded under the linter's own name, surfacing through
    # ``uncoached.md`` (suggested severity). The message is specific and
    # self-coaching, so no guide is needed. A project escalates with
    # ``uncoached = "enforce"`` or ``[smells.<linter>] severity = "enforced"``.
    return linter


def issue(entry: dict, base: Path) -> dict:
    # A path golangci-lint anchored at ``base`` is re-joined against it, so the
    # runner's anchoring (see "Finding paths are anchored at the sensor
    # boundary") is fed a path that actually points into the project.
    filename = os.path.normpath(str(base / entry["Pos"]["Filename"]))
    line, column = entry["Pos"]["Line"], entry["Pos"]["Column"]
    # golangci-lint v2 reports a package-level typecheck
    # error as a synthetic issue whose ``Pos`` collapses to line 1, column 0
    # (offset 0), with the real position embedded at the start of its ``Text``
    # as ``file:line:col: message``. Recover it, or every such finding would
    # coach the file's first line instead of the broken one.
    if entry["Pos"]["Line"] == 1 and entry["Pos"]["Column"] == 0:
        match = re.search(r"(\d+):(\d+): ", entry["Text"])
        if match:
            line, column = int(match.group(1)), int(match.group(2))
    # ``content`` carries the source line and the linter's message so the
    # shared listing shows both: the offending code and what is wrong with it.
    # ``content`` is what ``line_level_issues.md`` renders after ``file:line``,
    # and no shipped sensor sets it — so without this, the listing is bare.
    source_lines = entry.get("SourceLines")
    source_line = source_lines[0].strip() if source_lines else ""
    content = f"{source_line}: {entry['Text']}" if source_line else entry["Text"]
    return {
        "key": filename,
        "details": {
            "file": filename,
            "line": line,
            "column": column,
            "message": entry["Text"],
            "source": "golangci-lint:" + entry["FromLinter"],
            "content": content,
        },
    }


def findings(entries: list[dict], base: Path) -> list[dict]:
    """v2 ``Issue`` entries to canonical findings, grouped by smell (sorted)."""
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
            "issues": [issue(entry, base) for entry in by_smell[smell]],
        }
        for smell in sorted(by_smell)
    ]


def main() -> int:
    project_args, files = split_argv(sys.argv[1:])
    if not files:
        print("[]")
        return 0
    config_args, base = config_in_force(project_args)
    result = run_golangci_lint(files, project_args, config_args)
    if golangci_lint_crashed(result):
        sys.stderr.write(result.stderr)
        return 2
    print(json.dumps(findings(issues(result), base)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
