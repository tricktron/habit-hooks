"""Run golangci-lint and print canonical findings.

STUB — scaffolded so the acceptance test compiles and fails on its assertion
rather than on missing files. The real pipeline (split argv -> config check ->
run via tool_spawn -> parse JSON -> map by linter + text -> group by smell) is
built out in the inner TDD loop.
"""

from __future__ import annotations

import sys


def main() -> int:
    # STUB: not yet implemented. Exits 2 (a crash, not a clean run) so the
    # acceptance test fails on its expected output, never on an import error.
    sys.stderr.write("golangci_lint_sensor: not yet implemented\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
