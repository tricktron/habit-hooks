"""``[sensors.golangci-lint] args`` must reach golangci-lint, not be dropped.

Before this fix ``main()`` threw away everything before the ``--`` — the half
the core's ``${args}`` placeholder expands out of ``[sensors.golangci-lint]``
``args`` into the argv — so a project naming its own config through
``--config custom.yml`` lost it to the bundled fallback. The sensor's command
now spells ``${args} -- ${files}`` and the wrapper splits on the last ``--``:
everything before it goes to golangci-lint verbatim, everything after becomes a
file. A ``--config`` a project put in its args is that project's own
config — the bundled fallback must not be passed beside it (golangci-lint would
name the later one) — and findings anchor to that config's directory, exactly
as they do for the bundled fallback.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SENSOR = (
    Path(__file__).resolve().parents[1]
    / "src/habit_hooks_go" / "sensors" / "golangci_lint_sensor.py"
)

GO_MOD = "module demo\n\ngo 1.26\n"

UNUSED_IMPORT = """package main

import "fmt"

func main() {}
"""

# 30 ``if`` statements — cyclomatic complexity 31, over gocyclo's >30 default,
# so the bundled fallback flags it. ``main`` calls ``f`` so ``unused`` never does.
HIGH_COMPLEXITY = """package main

func f(n int) int {
\tx := 0
\tif n > 0 { x++ }
\tif n > 1 { x++ }
\tif n > 2 { x++ }
\tif n > 3 { x++ }
\tif n > 4 { x++ }
\tif n > 5 { x++ }
\tif n > 6 { x++ }
\tif n > 7 { x++ }
\tif n > 8 { x++ }
\tif n > 9 { x++ }
\tif n > 10 { x++ }
\tif n > 11 { x++ }
\tif n > 12 { x++ }
\tif n > 13 { x++ }
\tif n > 14 { x++ }
\tif n > 15 { x++ }
\tif n > 16 { x++ }
\tif n > 17 { x++ }
\tif n > 18 { x++ }
\tif n > 19 { x++ }
\tif n > 20 { x++ }
\tif n > 21 { x++ }
\tif n > 22 { x++ }
\tif n > 23 { x++ }
\tif n > 24 { x++ }
\tif n > 25 { x++ }
\tif n > 26 { x++ }
\tif n > 27 { x++ }
\tif n > 28 { x++ }
\tif n > 29 { x++ }
\treturn x
}

func main() {
\t_ = f(0)
}
"""

NOTHING_ENABLED = 'version: "2"\nlinters:\n  enable: []\n'


def _run(cwd: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SENSOR), *arguments],
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def test_a_config_named_in_args_wins_over_the_bundled_fallback(tmp_path: Path) -> None:
    """Without a ``--config`` arg the bundled fallback applies and the 30-``if``
    function is flagged ``high-complexity``; with ``--config`` naming a project
    config whose linters are disabled, the fallback is not added beside it and
    the same function is clean — proof the arg reached golangci-lint's own
    config selection rather than being dropped before the spawn."""
    (tmp_path / "go.mod").write_text(GO_MOD, encoding="utf-8")
    (tmp_path / "main.go").write_text(HIGH_COMPLEXITY, encoding="utf-8")
    (tmp_path / "custom").mkdir()
    (tmp_path / "custom" / "loose.yml").write_text(NOTHING_ENABLED, encoding="utf-8")

    without_the_config = _run(tmp_path, ["--", "main.go"])
    with_the_config = _run(tmp_path, ["--config", "custom/loose.yml", "--", "main.go"])

    assert without_the_config.returncode == 0, without_the_config.stderr
    assert [
        finding["smell"] for finding in json.loads(without_the_config.stdout)
    ] == ["high-complexity"]

    assert with_the_config.returncode == 0, with_the_config.stderr
    assert json.loads(with_the_config.stdout) == []


def test_findings_anchor_to_the_dir_of_the_config_named_in_args(
    tmp_path: Path,
) -> None:
    """golangci-lint resolves an issue's filename against the config file it
    used, so a project config in a subdirectory makes paths come back relative
    to that subdirectory — the sensor must re-join them against it, exactly as
    it does for the bundled fallback, or the runner's anchoring is fed a path
    that points nowhere. Uses the ``--config=path`` spelling; typecheck is
    always on, so the unused import is reported whatever the config enables."""
    (tmp_path / "go.mod").write_text(GO_MOD, encoding="utf-8")
    (tmp_path / "main.go").write_text(UNUSED_IMPORT, encoding="utf-8")
    (tmp_path / "cfg").mkdir()
    (tmp_path / "cfg" / "any.yml").write_text(NOTHING_ENABLED, encoding="utf-8")

    result = _run(tmp_path, ["--config=cfg/any.yml", "--", "main.go"])

    assert result.returncode == 0, result.stderr
    findings = json.loads(result.stdout)
    assert [finding["smell"] for finding in findings] == ["unused-import"]
    assert Path(findings[0]["issues"][0]["key"]) == (tmp_path / "main.go").resolve()
