An error you didn't check is a failure you didn't notice. Go returns
errors as values — the compiler won't force you to read them, so the
discipline is yours. Assign the error, check it, and decide what to do
with it.

Work through it in order:

1. **Check before you use the result.** A function returning `(T, error)`
   expects you to test `err` before touching `T`. The unchecked path is the
   one where `T` is zero-valued, nil, or stale — using it silently is the
   bug, and it surfaces at the worst moment: a nil dereference in
   production, an empty config loaded without complaint, a file that
   "wrote" to a closed handle.
2. **Handle it, don't just pass it on.** Bare `return err` propagates the
   error but loses where it happened. Add context at each layer with
   `fmt.Errorf("doing X: %w", err)` — the `%w` verb preserves the chain so
   `errors.Is` and `errors.As` still work upstream. A caller six frames up
   should read "could not read config: open failed: no such file or
   directory", not just "no such file or directory".
3. **Handle it once.** Logging the error *and* returning it is handling it
   twice — the log fills with duplicate lines and the top-level caller gets
   a stripped error. Either wrap it and return it, or log it and stop. Not
   both.
4. **Prefer opaque errors.** Return the error with added context rather
   than inspecting its type or value. If a caller needs to distinguish
   error kinds, assert behaviour — an interface like `Temporary() bool` —
   not a sentinel value (`== ErrFoo`) or a type assertion
   (`err.(*MyError)`). Comparing `err.Error()` to a string is a code
   smell: the message is for humans, not for program logic, and a
   reworded message silently breaks the check.

Suppressing the warning with `_ =` or a blank assignment hides the
question instead of answering it. If the error genuinely cannot occur, a
comment saying so is cheaper than a silent discard that masks the one
time it does.

{% include "includes/line_level_issues.md" %}
