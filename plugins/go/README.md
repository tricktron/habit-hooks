# habit-hooks-go

The Go Habit Hooks plugin: wraps [`golangci-lint`](https://golangci-lint.run/)
for structural code-smell detection.

## Install

```sh
pip install "habit-hooks[go]"
```

## Enable

```toml
# .habit-hooks/config.toml
plugins = ["go", "generic"]
```

Installing a plugin does not switch it on — it has to be named in
`plugins` before habit-hooks runs it.

## Detectors

- [`golangci-lint`](https://golangci-lint.run/) — `go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest`

Part of [habit-hooks](https://github.com/habit-hooks/habit-hooks).
