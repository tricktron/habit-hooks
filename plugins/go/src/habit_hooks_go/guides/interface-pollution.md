A large interface is a tax on every consumer. Go's implicit satisfaction
means anyone using your interface must implement all of it — stubbing the
methods they don't need, often with `panic("not implemented")`. The
standard library gives you `io.Reader` (one method), `fmt.Stringer` (one
method). The Go proverb: *the bigger the interface, the weaker the
abstraction.*

Break the interface into single-method or few-method pieces, or expose a
concrete struct and let consumers declare their own interface over the
subset they need. A consumer's interface is defined at the point of use,
not the point of production — and a one-method interface extracted at the
call site is always small enough.

{% include "includes/line_level_issues.md" %}
