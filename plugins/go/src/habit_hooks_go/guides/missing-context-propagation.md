A context you didn't propagate is a cancellation you didn't honour. When
a function receives a `context.Context` and creates `context.Background()`
or `context.TODO()` instead of deriving from the parent, the cancellation
tree is broken — goroutines outlive the request, deadlines are lost, and a
client who disconnected is still being served.

Pass `ctx` as the first argument to every function on the call path
between incoming and outgoing requests. Derive (never replace) when you
need a narrower scope: `ctx, cancel := context.WithTimeout(parentCtx,
timeout)`. The parent's cancellation flows downward through the tree; a
fresh `context.Background()` in the middle severs it.

{% include "includes/line_level_issues.md" %}
