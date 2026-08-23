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
