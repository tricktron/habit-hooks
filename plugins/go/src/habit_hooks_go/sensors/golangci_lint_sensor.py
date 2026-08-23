"""Run golangci-lint and print canonical findings, mapped by linter + text.

The pipeline: split argv on ``--`` for the file list -> decide whether the
project has its own config (and only then reach for the bundled fallback) ->
run via ``tool_spawn`` -> parse the v2 JSON wrapper (``{"Issues": [...]}``) ->
map each issue by linter + text to a smell -> group by smell. A missing
golangci-lint answers in one line, not a traceback.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tool_spawn import run_tool

# A project naming no config of its own is linted with ours — the "this project
# has none" fallback, never an override (see "A wrapped tool's own config wins").
PROJECT_CONFIG_NAMES = (".golangci.yml", ".golangci.yaml", "golangci.yml")

# The sensor helper is a loose script, so its own directory is ``sys.path[0]``
# and the bundled config lives one directory above it, off the script's path.
BUNDLED_CONFIG = Path(__file__).resolve().parent.parent / ".golangci.yml"

SMELL_BY_LINTER = {
    "gocyclo": "high-complexity",
    "funlen": "oversized-function",
    "ineffassign": "unused-variable",
}

# golangci-lint's own contract (v2): 0 is clean, 1 is "issues found" — both
# trustworthy. Anything else (3 = flag error in v2, 127 = tool not found,
# -9 = killed) is golangci-lint never having produced a real report, mirroring
# ruff_sensor.TOOL_EXIT_CODES.
TOOL_EXIT_CODES = (0, 1)


def config_arguments() -> list[str]:
    """Ours, only where the project has none of its own.

    The project's config is authoritative; the bundled one is the fallback for
    "this project has none" — the shape every wrapped-tool sensor keeps.
    """
    if any((Path.cwd() / name).exists() for name in PROJECT_CONFIG_NAMES):
        return []
    return ["--config", str(BUNDLED_CONFIG)]


def run_golangci_lint(files: list[str]) -> subprocess.CompletedProcess[str]:
    """What golangci-lint said, or what a shell says about one nobody installed.

    A missing golangci-lint raised a ``FileNotFoundError`` out of here, making
    internals the diagnosis; this wrapper answers the way the shell would
    (``127``, ``golangci-lint: command not found``) so the run names the missing
    tool in one line.
    """
    command = [
        "golangci-lint",
        "run",
        "--output.json.path",
        "stdout",
        # v2 prints its text formatter AND a "N issues." summary to stdout by
        # default, polluting the JSON the sensor parses. The text formatter is
        # useless here, so send it to stderr and drop the summary.
        "--output.text.path",
        "stderr",
        "--show-stats=false",
        *config_arguments(),
        *files,
    ]
    try:
        return run_tool(command)
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            command, 127, "", "golangci-lint: command not found\n"
        )


def golangci_lint_crashed(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode not in TOOL_EXIT_CODES


def violations(result: subprocess.CompletedProcess[str]) -> list[dict]:
    """golangci-lint v2 wraps its issues: ``{"Issues": [...], "Report": {...}}``."""
    text = result.stdout.strip()
    return json.loads(text).get("Issues", []) if text else []


def smell_of(linter: str, text: str) -> str | None:
    if linter in SMELL_BY_LINTER:
        return SMELL_BY_LINTER[linter]
    if linter == "unused":
        return "unused-variable" if text.startswith("var ") else None
    if linter == "typecheck":
        return "unused-import" if "imported and not used" in text else "parse-error"
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
    files = sys.argv[1:]
    if "--" in sys.argv[1:]:
        files = sys.argv[sys.argv.index("--") + 1 :]
    result = run_golangci_lint(files)
    if golangci_lint_crashed(result):
        sys.stderr.write(result.stderr)
        return 2
    print(json.dumps(findings(violations(result))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
