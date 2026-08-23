"""Resolve which golangci-lint config wins, run the tool, and parse its output.

The config-precedence shape every wrapped-tool sensor keeps: the project's own
config is authoritative, the bundled one is the fallback for "this project has
none". A project can name its config on disk (a standard filename in the root)
or through ``args`` (a ``--config`` of its own) — both stand.

golangci-lint v2 resolves an issue's ``Pos.Filename`` against the config file
it used, not the cwd: the base returned by ``config_in_force`` is the directory
of the config in force, and the sensor re-joins each reported path against it
before the runner re-expresses them.

golangci-lint v2 cannot typecheck individual files from different directories
(Go's type checker needs full package context), so the unique parent
directories of the file list are passed instead — only packages with changed
files are linted, preserving the scoping habit-hooks narrows to.

golangci-lint's cache keys on content, not paths: a cache hit from a different
project returns ``Pos.Filename`` values pointing there. ``GOLANGCI_LINT_CACHE``
is scoped to a per-project directory (keyed by cwd) so the cache stays warm
within a project while isolating it from every other.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from tool_spawn import run_tool

# A project naming no config of its own is linted with ours — the "this project
# has none" fallback, never an override (see "A wrapped tool's own config wins").
# The dot-prefixed names golangci-lint v2 discovers itself (verified against
# 2.12.2): .yml, .yaml, .toml, .json. A bare ``golangci.yml`` is NOT discovered
# — listing it here would make the sensor stand aside thinking the project's
# config was in force, while golangci-lint silently ran with defaults.
PROJECT_CONFIG_NAMES = (
    ".golangci.yml",
    ".golangci.yaml",
    ".golangci.toml",
    ".golangci.json",
)

# The sensor helper is a loose script, so its own directory is ``sys.path[0]``
# and the bundled config lives one directory above it, off the script's path.
BUNDLED_CONFIG = Path(__file__).resolve().parent.parent / ".golangci.yml"

# golangci-lint's own contract (v2): 0 is clean, 1 is "issues found" — both
# trustworthy. Anything else (3 = flag error in v2, 127 = tool not found,
# -9 = killed) is golangci-lint never having produced a real report, mirroring
# ruff_sensor.TOOL_EXIT_CODES.
TOOL_EXIT_CODES = (0, 1)


def _cache_dir() -> str:
    """A cache dir scoped to this project, so cross-project cache hits cannot
    return paths from another checkout.

    golangci-lint's cache keys on content + relative path, not absolute paths,
    so identical files at the same relative path in different projects share a
    cache entry — and the cached ``Pos.Filename`` points to whichever project
    was analysed first. A per-project cache dir (keyed by cwd hash) keeps the
    cache warm within a project (same relative paths → valid hits) while
    isolating it from every other project's checkout.
    """
    digest = hashlib.sha256(str(Path.cwd().resolve()).encode()).hexdigest()[:16]
    cache = Path.home() / ".cache" / "golangci-lint" / digest
    cache.mkdir(parents=True, exist_ok=True)
    return str(cache)


def _named_config(project_args: list[str]) -> Path | None:
    """The config a project named itself in ``args``, if it named one.

    Both pflag spellings golangci-lint accepts: ``--config path`` and
    ``--config=path``.
    """
    for i, token in enumerate(project_args):
        if token == "--config":
            if i + 1 < len(project_args):
                return Path(project_args[i + 1])
        elif token.startswith("--config="):
            return Path(token.partition("=")[2])
    return None


def config_in_force(project_args: list[str]) -> tuple[list[str], Path]:
    """The config that wins, and the dir golangci-lint anchors paths to.

    The shape every wrapped-tool sensor keeps: the project's own config is
    authoritative, the bundled one is the fallback for "this project has none".
    A project can name its config on disk (a standard filename in the root) or
    through ``args`` (a ``--config`` of its own) — both stand.

    golangci-lint v2 resolves an issue's ``Pos.Filename`` against the config
    file it used, not the cwd: the base is therefore the directory of the config
    in force — the named config's parent, the root when one was discovered, or
    the bundled config's own directory when the fallback runs. The sensor
    re-joins each reported path against it before the runner re-expresses them.
    """
    named = _named_config(project_args)
    if named is not None:
        return [], named.resolve().parent
    if any((Path.cwd() / name).exists() for name in PROJECT_CONFIG_NAMES):
        return [], Path.cwd()
    return ["--config", str(BUNDLED_CONFIG)], BUNDLED_CONFIG.parent


def run_golangci_lint(
    files: list[str], project_args: list[str], config_args: list[str]
) -> subprocess.CompletedProcess[str]:
    """What golangci-lint said, or what a shell says about one nobody installed.

    A missing golangci-lint raised a ``FileNotFoundError`` out of here, making
    internals the diagnosis; this wrapper answers the way the shell would
    (``127``, ``golangci-lint: command not found``) so the run names the missing
    tool in one line.

    golangci-lint v2 cannot accept individual ``.go`` files from different
    directories — Go's type checker needs full package context, and "named
    files must all be in one directory" is its own error. The unique parent
    directories of ``files`` are passed instead, so only packages with changed
    files are linted (the scoping habit-hooks narrows to), and golangci-lint
    typechecks each package independently.

    golangci-lint's cache keys on content + relative path, not absolute paths:
    identical files at the same relative path in different projects share a
    cache entry, and the cached ``Pos.Filename`` points to the wrong project.
    ``GOLANGCI_LINT_CACHE`` is scoped to a per-project directory (keyed by
    cwd hash) so the cache stays warm within a project while isolating it
    from every other — the default shared cache is the source of the
    stale-path false-clean.
    """
    dirs = sorted({str(Path(f).parent) for f in files})
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
        *project_args,
        *config_args,
        # Parent directories, not individual files: golangci-lint v2 cannot
        # typecheck files from different directories together, but it accepts
        # multiple directory paths and typechecks each package independently.
        *dirs,
    ]
    os.environ["GOLANGCI_LINT_CACHE"] = _cache_dir()
    try:
        return run_tool(command)
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            command, 127, "", "golangci-lint: command not found\n"
        )


def golangci_lint_crashed(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode not in TOOL_EXIT_CODES


def issues(result: subprocess.CompletedProcess[str]) -> list[dict]:
    """golangci-lint v2 wraps its issues: ``{"Issues": [...], "Report": {...}}``."""
    text = result.stdout.strip()
    return json.loads(text).get("Issues", []) if text else []
