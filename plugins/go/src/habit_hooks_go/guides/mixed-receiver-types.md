A value receiver means the method operates on a copy — mutate the
receiver and the original is unchanged, silently. Mixing value and pointer
receivers on the same type is inconsistent: some methods modify the
original, others don't, and a reader has to check each one to know which
is which.

Pick one and use it consistently. If any method mutates the receiver, use
a pointer receiver for all methods on that type — not because `Balance`
needs a pointer, but because consistency lets the reader assume one rule
instead of checking every method. A struct with no mutation can use value
receivers throughout; a struct with one mutating method should use pointer
receivers throughout.

{% include "includes/line_level_issues.md" %}
