A mutex copied is a lock broken. Go copies values on every assignment
and function call, and `sync.Mutex` documents "must not be copied after
first use" — the copy's lock state is undefined, and the original's
protection is silently gone. Two goroutines can enter the critical section
through what they think is the same lock but are actually two.

The fix is a pointer. Pass `*Counter`, not `Counter`. If the struct lives
in a receiver, use a pointer receiver. If callers construct the value,
give them a constructor (`NewCounter()`) so they receive a pointer from
the start and never have the chance to copy by value.

`go vet` catches this — do not silence it. A `go vet` pass on a struct
containing a mutex is not a suggestion, it is a bug report.

{% include "includes/line_level_issues.md" %}
