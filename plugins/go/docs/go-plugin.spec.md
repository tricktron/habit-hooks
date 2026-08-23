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
