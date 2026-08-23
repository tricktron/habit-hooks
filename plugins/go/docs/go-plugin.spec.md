# The go plugin — acceptance

The go plugin runs its sensor through the real `habit-sensors` pipeline. These
cases run the **actual** tool (`golangci-lint`, from the system `PATH`) against
a fixture with a known shape and assert the canonical finding comes out, mapped
to the smell keys in [smell-vocabulary.md](smell-vocabulary.md).

`habit-sensors` is the installed CLI; `golangci-lint` is on the system `PATH`.
The sensor runs `golangci-lint` with `--output.json.path stdout`, groups the
flat JSON issues by smell, and emits one finding per smell. Every case needs a
valid `go.mod` — golangci-lint refuses to run without one — so it lives in the
preamble and every case inherits it.

📄.habit-hooks/config.toml
```toml
plugins = ["go"]
```

📄go.mod
```go
module demo

go 1.26
```

## A clean Go file produces no findings

The walking skeleton: a well-formed Go program that imports only the standard
library has nothing for golangci-lint to report, so the sensor emits an empty
findings list — the thinnest possible end-to-end path from an installed plugin
to a clean run. Nothing to coach is as much an answer as a finding.

📄main.go
```go
package main

import "fmt"

func main() {
	fmt.Println("hello")
}
```

```bash
habit-sensors --all
```

🖥️ ✅
```json
[]
```

## A high-complexity function is flagged

A function whose cyclomatic complexity exceeds the `gocyclo` threshold is the
tangle a hook exists to stop, so it is the second end-to-end path: a real
complexity report, mapped to the `high-complexity` smell. The bundled
`.golangci.yml` enables `gocyclo` at golangci-lint's own default (min
complexity 30, reported when *greater than* 30), so a function with **30**
`if` statements — complexity 31 — trips it. The fixture stays under `funlen`'s
defaults (40 statements, 60 lines) so complexity is the one smell it carries,
and `main` calls `f` so the `unused` linter never sees it.

The sensor maps `gocyclo` → `high-complexity` (`smell_of`), stamping
`source: "golangci-lint:gocyclo"` on each issue. The issue's `key` is the
file's path anchored to the project, so only its final component is asserted
here (`sub(".*/"; "")`), along with the deterministic line and column.

📄main.go
```go
package main

func f(n int) int {
	x := 0
	if n > 0 { x++ }
	if n > 1 { x++ }
	if n > 2 { x++ }
	if n > 3 { x++ }
	if n > 4 { x++ }
	if n > 5 { x++ }
	if n > 6 { x++ }
	if n > 7 { x++ }
	if n > 8 { x++ }
	if n > 9 { x++ }
	if n > 10 { x++ }
	if n > 11 { x++ }
	if n > 12 { x++ }
	if n > 13 { x++ }
	if n > 14 { x++ }
	if n > 15 { x++ }
	if n > 16 { x++ }
	if n > 17 { x++ }
	if n > 18 { x++ }
	if n > 19 { x++ }
	if n > 20 { x++ }
	if n > 21 { x++ }
	if n > 22 { x++ }
	if n > 23 { x++ }
	if n > 24 { x++ }
	if n > 25 { x++ }
	if n > 26 { x++ }
	if n > 27 { x++ }
	if n > 28 { x++ }
	if n > 29 { x++ }
	return x
}

func main() {
	_ = f(0)
}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "high-complexity",
  "language": "go",
  "key": "main.go",
  "line": 3,
  "source": "golangci-lint:gocyclo"
}
```

## An oversized function is flagged

The bundled `.golangci.yml` enables `funlen`, which reports a function with more
than `statements: 40` statements (its default, reported when *greater than* 40).
A straight-line function of 41 statements trips it, while its absence of
conditionals keeps cyclomatic complexity at 1 so `gocyclo` never fires, and the
function's 43 lines stay under `funlen`'s 60-line default — statement count is
the one thing this fixture carries. `main` calls `f`, so the `unused` linter
never sees it.

The sensor maps `funlen` → `oversized-function` (`smell_of`), stamping
`source: "golangci-lint:funlen"` on each issue.

📄main.go
```go
package main

func f() int {
	a := 0
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	a++
	return a
}

func main() {
	_ = f()
}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "oversized-function",
  "language": "go",
  "key": "main.go",
  "line": 3,
  "source": "golangci-lint:funlen"
}
```

## An unused variable is flagged

A package-level `var x = 1` that nothing ever reads is reported by the `unused`
linter as `var x is unused` — the `"var "` text prefix in the routing table maps
it to `unused-variable`. The fixture stays at package scope on purpose: a
*local* `x := 1` never read is a Go compiler error (`declared and not used`
from `typecheck`), which would map to `parse-error` instead — the two cases are
only separable because `unused` talks about the package-scope spelling.

The sensor maps `unused` + `"var "` → `unused-variable` (`smell_of`), stamping
`source: "golangci-lint:unused"` on the issue.

📄main.go
```go
package main

var x = 1

func main() {}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "unused-variable",
  "language": "go",
  "key": "main.go",
  "line": 3,
  "source": "golangci-lint:unused"
}
```

## An unused import is flagged

`import "fmt"` that is never referenced is a Go compiler error — the always-on
`typecheck` linter reports `"fmt" imported and not used`, and the
`"imported and not used"` text prefix in the routing table maps it to
`unused-import`. This is the compiler's own voice, so the fixture needs no
`fmt` call and nothing else in the file: a single unused import is the whole
smell.

The sensor maps `typecheck` + `"imported and not used"` → `unused-import`
(`smell_of`), stamping `source: "golangci-lint:typecheck"` on the issue.

📄main.go
```go
package main

import "fmt"

func main() {}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "unused-import",
  "language": "go",
  "key": "main.go",
  "line": 3,
  "source": "golangci-lint:typecheck"
}
```

## A parse error is flagged

A file Go cannot parse is coached, not silently mislabelled: `func broken( {`
makes `typecheck` report two parse errors (`expected ')', found '{'` and
`missing ',' in parameter list`), neither containing `imported and not used`,
so the routing table maps every non-import `typecheck` issue to `parse-error`
and the two group into one finding. `.issues[0]` is the first report, at the
`func` line.

The sensor maps `typecheck` + other text → `parse-error` (`smell_of`),
stamping `source: "golangci-lint:typecheck"` on each issue.

📄main.go
```go
package main

func broken( {
}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "parse-error",
  "language": "go",
  "key": "main.go",
  "line": 3,
  "source": "golangci-lint:typecheck"
}
```

## An unused func is not forwarded

The `unused` linter reports an unused function as `func unused is unused` —
`"func "`, not `"var "`, so the routing table's unused row has no smell for it
and the issue is **dropped**, the same "a sensor emits vocabulary smells only"
rule ruff and knip follow. `main` is always considered used, so the fixture's
one unused function is `unused`, kept small and straight-line (so neither
`funlen` nor `gocyclo` fires) and the lone candidate for forwarding. With
nothing else in the file, a clean run is the whole assertion.

📄main.go
```go
package main

func unused() int {
	return 1
}

func main() {}
```

```bash
habit-sensors --all
```

🖥️ ✅
```json
[]
```

## A project's own config wins

The bundled `.golangci.yml` answers "this project has none"; it never overrides
a project that has thought about its own (["A wrapped tool's own config
wins"](../../../CLAUDE.md)). The sensor looks for `.golangci.yml` /
`.golangci.yaml` / `golangci.yml` in the project root, and when it finds one it
passes no `--config` and lets golangci-lint discover it — the project's own
config is authoritative for thresholds and linters alike.

So this project's `.golangci.yml` (`linters.enable: []`, keeping golangci-lint's
default set but adding nothing) is what runs, and the 30-`if` function from the
earlier high-complexity case — complexity 31, red under the bundled config — is
now clean. If the sensor had passed `--config <bundled>`, `gocyclo` would have
fired; an empty result is proof it stood aside.

The case is its own git repository, as a real project is, so the sensor's run
cannot be answered by anything outside the case directory.

✏️GIT_CEILING_DIRECTORIES
```text
$PWD/..
```

```bash
git init -q
```

📄.golangci.yml
```yaml
version: "2"
linters:
  enable: []
```

📄main.go
```go
package main

func f(n int) int {
	x := 0
	if n > 0 { x++ }
	if n > 1 { x++ }
	if n > 2 { x++ }
	if n > 3 { x++ }
	if n > 4 { x++ }
	if n > 5 { x++ }
	if n > 6 { x++ }
	if n > 7 { x++ }
	if n > 8 { x++ }
	if n > 9 { x++ }
	if n > 10 { x++ }
	if n > 11 { x++ }
	if n > 12 { x++ }
	if n > 13 { x++ }
	if n > 14 { x++ }
	if n > 15 { x++ }
	if n > 16 { x++ }
	if n > 17 { x++ }
	if n > 18 { x++ }
	if n > 19 { x++ }
	if n > 20 { x++ }
	if n > 21 { x++ }
	if n > 22 { x++ }
	if n > 23 { x++ }
	if n > 24 { x++ }
	if n > 25 { x++ }
	if n > 26 { x++ }
	if n > 27 { x++ }
	if n > 28 { x++ }
	if n > 29 { x++ }
	return x
}

func main() {
	_ = f(0)
}
```

```bash
habit-sensors --all
```

🖥️ ✅
```json
[]
```
