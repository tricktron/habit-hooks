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

## An unused func is forwarded as uncoached

The `unused` linter reports an unused function as `func unused is unused` —
`"func "`, not `"var "`, so it has no catalogue smell. Rather than dropping it,
the sensor forwards it under the `unused` smell key, surfacing through
`uncoached.md` (suggested severity) — the same treatment every unmapped linter
gets. `main` is always considered used, so the fixture's one unused function is
`unused`, kept small and straight-line (so neither `funlen` nor `gocyclo`
fires) and the lone finding.

📄main.go
```go
package main

func unused() int {
	return 1
}

func main() {}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️
```json
{
  "smell": "unused",
  "language": "go",
  "key": "main.go",
  "line": 3,
  "source": "golangci-lint:unused"
}
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

## An unchecked error is flagged

The bundled `.golangci.yml` enables `errcheck`, which reports a call whose error
return is discarded. Calling `os.Open("nonexistent")` as a bare statement throws
away **both** return values — the unchecked `error` is what the linter flags, and
only a bare statement triggers it (`_ = os.Open(...)` is an explicit discard and
would stay silent). The file otherwise compiles (so `typecheck` never speaks),
`main` is used by the runtime (so `unused` never sees it), and the straight-line
five-line body stays under `funlen`'s and `gocyclo`'s defaults — the discarded
error is the one smell this file carries.

The sensor maps `errcheck` → `unchecked-error` (`smell_of`), stamping
`source: "golangci-lint:errcheck"` on the issue.

📄main.go
```go
package main

import "os"

func main() {
	os.Open("nonexistent")
}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "unchecked-error",
  "language": "go",
  "key": "main.go",
  "line": 6,
  "source": "golangci-lint:errcheck"
}
```

## A copied lock is flagged

The bundled `.golangci.yml` enables `govet`, whose `copylocks` analyzer reports a
`sync.Mutex` that got carried off in a value — `sync.Mutex` documents "must not
be copied after first use", and copying a struct that holds one silently splits
the lock in two. This fixture builds a `Counter` and copies it into `d`; govet
reports `assignment copies lock value to d: demo.Counter contains sync.Mutex`,
and the fix the guide coaches is a pointer: pass `*Counter`, not `Counter`.

`govet` runs many analyzers, so it needs text routing like `unused` / `typecheck`
rather than a wholesale mapping: a govet message containing `copies lock value`
maps to `copied-lock` (`smell_of`), stamping `source: "golangci-lint:govet"` on
the issue.

The fixture stays a single smell: `c.mu.Lock()` / `c.mu.Unlock()` in place marks
the field used (so `unused` never sees it), `_ = d` is an explicit use of the
copy (so it is not left unused), and the straight-line body stays under
`funlen`'s and `gocyclo`'s defaults — the copied lock is the one thing this file
carries.

📄main.go
```go
package main

import "sync"

type Counter struct {
	mu sync.Mutex
}

func main() {
	c := Counter{}
	c.mu.Lock()
	d := c
	c.mu.Unlock()
	_ = d
}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "copied-lock",
  "language": "go",
  "key": "main.go",
  "line": 12,
  "source": "golangci-lint:govet"
}
```

## Interface pollution is flagged

The bundled `.golangci.yml` enables `interfacebloat`, which reports an interface
with more than 10 methods (its default threshold, reported when *greater than*
10). An interface with **11** methods — a `Worker` whose contract is a wish
list — trips it. The fixture's empty method bodies are the interface's own
definition (each compiles to its required signature), so the file parses
(`typecheck` never speaks), `main` is used by the runtime (so `unused` never
sees the package-scope `Worker`), and there is no function body to blow
`funlen`'s or `gocyclo`'s defaults — the oversized contract is the one smell
this file carries.

`interfacebloat` is a standalone linter with an unambiguous `FromLinter`, so it
gets a direct mapping rather than text routing: the sensor maps
`interfacebloat` → `interface-pollution` (`smell_of`), stamping
`source: "golangci-lint:interfacebloat"` on the issue. It is a design smell, not
a runtime hazard — the code works, it is just harder to test and maintain — so
it coaches but does not fail the run (suggested severity).

📄main.go
```go
package main

type Worker interface {
	Method1()
	Method2()
	Method3()
	Method4()
	Method5()
	Method6()
	Method7()
	Method8()
	Method9()
	Method10()
	Method11()
}

func main() {}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️
```json
{
  "smell": "interface-pollution",
  "language": "go",
  "key": "main.go",
  "line": 3,
  "source": "golangci-lint:interfacebloat"
}
```

## Missing context propagation is flagged

The bundled `.golangci.yml` enables `contextcheck`, which reports a function
that creates a fresh `context.Background()` / `context.TODO()` where the
`context.Context` parameter it was handed should have been flowed through.
`f` takes `ctx context.Context` but hands its callee `work` a brand-new
`context.Background()` — a call that could just as well have taken `ctx` —
severing the cancellation tree. `main` calls `f(context.Background())` from a
function with no context parameter, so there is nothing there to propagate and
`contextcheck` stays silent on it. The file otherwise compiles (so `typecheck`
never speaks), `work` and `f` are both called (so `unused` never sees them),
and the straight-line bodies stay under `funlen`'s and `gocyclo`'s defaults —
the severed context is the one smell this file carries.

`contextcheck` is a standalone linter with an unambiguous `FromLinter`, so it
gets a direct mapping rather than text routing: the sensor maps `contextcheck`
→ `missing-context-propagation` (`smell_of`), stamping
`source: "golangci-lint:contextcheck"` on the issue. It is a runtime hazard,
not a design smell — a broken cancellation tree lets goroutines outlive the
request — so it fails the run (enforced severity), like `unchecked-error` and
`copied-lock`.

📄main.go
```go
package main

import "context"

func work(ctx context.Context) {}

func f(ctx context.Context) {
	work(context.Background())
}

func main() {
	f(context.Background())
}
```

```bash
habit-sensors --all | jq '.[] | {smell, language, key: (.issues[0].key | sub(".*/"; "")), line: .issues[0].details.line, source: .issues[0].details.source}'
```

🖥️ ✅
```json
{
  "smell": "missing-context-propagation",
  "language": "go",
  "key": "main.go",
  "line": 8,
  "source": "golangci-lint:contextcheck"
}
```
