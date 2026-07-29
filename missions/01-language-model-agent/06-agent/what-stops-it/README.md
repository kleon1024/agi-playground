---
status: draft
level: applied
base: none
label: What stops it
---

# The agent can act. What stops it?

[The previous chapter](../) built a loop that reads files, lists directories,
and runs commands, with a grounding rule that keeps the model from inventing
its own observations. Every one of those capabilities is also a way to do
damage, and the grounding rule does nothing about that — it makes the agent
*honest*, not *safe*.

This chapter is the containment half: what the harness refuses, how it refuses
it, and which of those refusals actually hold. You need the loop and the tool
schemas from the previous chapter; you leave with a permission model and a
jail, plus a clear statement of the gap neither of them closes.

## Path joining is a trap, and it is not the one you expect

`resolve_in_jail` in `tools.py` exists because of one `pathlib` behavior:

```python
Path("/root") / "/etc/passwd"     # -> Path("/etc/passwd")
```

Joining with an absolute path *replaces* the left side rather than extending
it. A jail that joins and then checks the result for `..` would miss this
entirely — there is no `..` anywhere, and the path is fully outside the jail.

So `resolve_in_jail` rejects absolute inputs outright *before* joining, then
resolves the path (following symlinks) and checks ancestry. Those three steps
close three different escapes: the absolute-path escape, the `..`-walk escape,
and the symlink escape. The ordering matters — resolving before rejecting
absolutes would let the first one through.

## An allowlist, and why a denylist could not work

`run_command` adds a fourth control on top of the jail: an **allowlist**
checked against the parsed first token.

A denylist is a losing game. "No `rm -rf`" has no bound on the ways to spell
"delete everything" — different flags, a different binary, a shell expansion, a
script that does it indirectly. Every entry you add is a response to an attack
you already thought of. An allowlist inverts the burden: the command runs only
if it names something already decided to be safe, and the unknown case fails.

This only works because the harness never passes `shell=True`. With a shell,
`"echo hi; rm -rf /"` is one command as far as the operating system is
concerned, and checking `argv[0]` against an allowlist would only ever see
`echo`. Shell metacharacters are rejected outright as well, so that command
fails fast with a clear message rather than quietly doing something the
allowlist never anticipated. A timeout bounds a hung process; output truncation
keeps a giant file from flooding the model's context.

**One gap is left open rather than hidden.** Only `argv[0]` is allowlisted, so
`cat /etc/passwd` runs `cat` — an allowed name — while reading a path outside
the jail, because arguments are never checked against `resolve_in_jail`. The
jail protects `read_file`; it does not protect what an allowlisted binary
chooses to read. Closing that is exercise 2, and it is worth doing by hand,
because the shape of the fix is the general lesson: a control that validates
the *caller* does not automatically validate what the caller invokes.

## Three tiers, and a default that says no

Every `Tool` in `tools.py` carries a `RiskTier`:

| Tier | Meaning | Example |
|---|---|---|
| `AUTO` | read-only, always allowed | `read_file`, `list_dir` |
| `CONFIRM` | changes state, needs sign-off | `run_command` |
| `DENY` | refused unconditionally | anything you never want reachable |

`check_permission` in `harness.py` enforces it, and the harness's default
`confirm` function **denies every `CONFIRM`-tier call**.

That default is the point. A non-interactive run — a test, a scheduled job,
this file's own demo — must fail closed rather than silently execute something
nobody approved *merely because nobody was present to say no*. The absence of a
human is not consent. Swapping in a real `confirm` (a CLI prompt, a policy
check) is what makes `run_command` reachable at all.

**The tier lives on the tool, not on the call**, and that is a simplification
worth naming. `run_command` running `cat` and `run_command` running a
repo-mutating build are the same tier under this model, which is obviously too
coarse; a real harness eventually wants tier-by-argument distinctions. That is
exercise 1, and doing it will show you why it is harder than it sounds: you are
writing a classifier for "does this change state", and the cost of being wrong
is asymmetric.

## Fewer tools is a containment decision

Three tools, not thirty. The usual argument is about accuracy — tool count adds
selection complexity and ambiguous overlaps faster than it adds capability, and
a well-scoped three-tool loop reliably beats a much larger one on tasks within
its scope. mini-swe-agent's small toolset, and this stage's, are design choices
rather than limitations awaiting more tools.

The containment argument is separate and stronger: **every tool is a surface
you have to reason about the failure of.** Each new one needs its own tier, its
own jail interaction, and its own answer to "what does this do when the model
is confused?" `run_command`'s description leans on this directly — it names
`grep` as reachable *through* the allowlist rather than adding a fourth tool for
search, because one well-designed escape hatch composes better than a growing
enumeration of narrow tools, and it is one thing to audit instead of four.

## What none of this establishes

The jail, the allowlist, and the permission ladder are real controls, and they
are not a security boundary. They stop an agent that is confused, looping, or
following a bad instruction. They do not stop an adversary who controls the
model's input, because everything here runs in the same process with the same
credentials, and `cat` reading outside the jail is a demonstration that the
composition has holes. A harness that must resist an adversary needs process
isolation, a filesystem namespace, and dropped privileges — controls the
operating system enforces rather than controls a Python function requests.

This stage has no `runs/` entry, so nothing here is a claim about how often any
of it triggers in practice.

## Exercises

1. **Tier by argument.** `run_command` is uniformly `CONFIRM`. Extend
   `check_permission` (or add a policy hook) so a read-only `cat` or `grep`
   auto-allows while a repo-mutating command still confirms. Argue where the
   line sits, and what closes the gap when your classifier is wrong.
2. **Harden the honest gap.** Extend `run_command` to validate any argument
   that looks like a path against `resolve_in_jail`. First write a command that
   escapes the jail today through an allowlisted binary, then confirm your fix
   closes it.
3. **Add a fourth tool, on purpose.** Add a dedicated `grep` tool instead of
   routing search through `run_command`, give it its own risk tier, and argue
   in a comment whether it earns its place against the containment argument
   above.

## Check your mental model

1. `resolve_in_jail` rejects absolute paths before joining rather than after.
   What escapes if you reverse those two steps?
2. Why does the allowlist depend on never passing `shell=True`, and what
   exactly does an allowlist check see when a shell is involved?
3. The default `confirm` denies everything. What breaks if it allowed instead,
   in a run where no human is watching?
4. `cat /etc/passwd` passes the allowlist. Is that a bug in the allowlist, in
   the jail, or in neither?
5. You are asked to add ten more tools. Give one accuracy argument and one
   containment argument against it, and say which you would lead with.

## Next

Return to [stage 06](../) for the production mapping — how mini-swe-agent,
OpenHands, and Claude Code's published harness write-ups handle these same
decisions at scale. Then [stage 07](../../07-eval/) measures the agent built
here, under a harness disclosure that includes every control on this page,
because a score produced with `run_command` denied is not the same score.
