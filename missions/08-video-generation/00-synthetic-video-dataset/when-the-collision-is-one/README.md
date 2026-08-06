---
status: verified
level: applied
base: scratch
label: When the collision is one
verified: 2026-08-06
---

# The state space that multiplied the collisions away

**Question:** [stage 00's synthetic video dataset](../) extends mission
05's image generator along a time axis. This chapter reads the recorded
run and asks why the collision problem nearly vanished.

**Before this:** [stage 00's synthetic video dataset](../) and its recorded
generation.

## The story, read

The run ([record](runs/2026-08-06-collision-one.md)) reads the recorded
numbers:

| fact | value |
|---|---|
| eval candidates rejected | 1 |
| mission 05's first-attempt collisions (contrast) | 116 |
| per-clip state space | 3 shapes x 4 colors x 3 half-sizes x 8 directions x positions |

## Two readings

**The time axis multiplies the state space, and collisions follow the
space.** Mission 05's static images lived in a 48-state space (4 cells x 3
shapes x 4 colors), small enough that ~700 draws collided constantly. This
generator's per-clip space adds direction and start position, then
requires two clips to match at every one of 8 frames — roughly two orders
of magnitude larger. The recorded result: one rejected eval candidate
instead of hundreds.

**The headroom is a property of the space, not the code.** The generator
did not get better at avoiding collisions; the space got large enough that
collisions became rare. That is the same lesson as mission 05's fix
(widening the space) applied by construction rather than by repair — and
it is why the run records the collision count rather than assuming it.

## Evidence boundary

The recorded dataset run (800/150 split, one generator, one seed set). It
reads that artifact; it does not re-generate and the one-rejection count
characterizes this generator's space.

## Check your mental model

Answer each before opening it.

**1. Why did the same style of generator stop colliding?**

<details>
<summary>Answer</summary>

Because the collision probability scales with the state space's size.
Mission 05's static images had ~48 states, so hundreds of draws revisited
the same image. This generator's per-clip space — shape x color x
half-size x direction x start position, matched across 8 frames — is
orders of magnitude larger, so two clips matching entirely becomes rare.
The generator's code is no different; the space is.

</details>

**2. What would the one rejection have been if the space had not grown?**

<details>
<summary>Answer</summary>

Hundreds — the mission 05 pattern. The rejection count is the direct
measure of how much collision headroom the space has: at 48 states it was
116 on the first attempt, at this larger space it is 1. The recorded
number is evidence about the space's size, which is why the run reports
it instead of asserting "no leakage."

</details>

## Next

Back to [stage 00](../), or to
[the seed is the answer key](../when-the-seed-is-the-answer/) which reads
the same stage's fixture contract.
