---
status: verified
level: applied
base: scratch
label: When the long tail is invisible
verified: 2026-08-06
---

# The zero that is structural, not a tuning miss

**Question:** [stage 03's pre-rank](../) compares cheap proxies against
popularity-only ranking. This chapter reads the recorded surface-rate runs
and asks why popularity-only's long-tail number is zero on every seed.

**Before this:** [stage 03's pre-rank](../) and its recorded runs.

## The numbers, read

The run ([record](runs/2026-08-06-longtail-read.md)) reads the recorded
surface rates:

| seed | popularity overall | popularity long-tail |
|---:|---:|---:|
| 1 | 0.100 | 0.000 |
| 7 | 0.400 | 0.000 |
| 42 | 0.400 | 0.000 |
| 99 | 0.100 | 0.000 |
| funnel scale (2,000 items) | 0.100 | 0.000 |

## Two readings

**A cold item's popularity is noise, so it can never rank above a head item
on that signal alone.** Long-tail items have zero or near-zero observed
popularity by definition, so a popularity-only proxy ranks them below every
head item every time. The 0.000 is not a threshold miss or a seed artifact
— it holds across four seeds and a funnel-realistic scale because it is
true by construction.

**The zero is the point of the comparison, not an embarrassment.** The cheap
proxy (content + popularity) surfaces long-tail items (0.111-0.200 at demo
scale) because content is not popularity. The recorded contrast is what
makes pre-rank honest: a proxy that cannot see the tail would pass the
overall surface-rate check while quietly emptying the long tail, and the
long-tail column exists to catch exactly that.

## The fix and its trade

The fix is to stratify the surface-rate read: report the long-tail column
next to the overall number, and let the long-tail column be the one that
decides. The executed table prices why: popularity-only scores 0.100-0.400
overall while its long-tail surface is 0.000 on all four seeds and at funnel
scale (2,000 items) — an aggregate read would certify a proxy that is
silently empty exactly where discovery happens.

The trade, named: a stratified read needs enough tail items per run to be
stable, and it forces the team to decide what "tail" means before the run.
The cheap proxy's 0.111-0.200 long-tail surface at demo scale shows the
repair is real cold-item signal (content), not a bigger cut — and at the
funnel's actual cut ratio both proxies collapse to 0.000, so the long-tail
column is also the number that stops the team from promising a capability
the funnel's cut ratio does not deliver.

## Who owns the loop

- **The evaluation team** owns the stratified read — the long-tail column is
  a per-run report, not a one-time analysis.
- **The product team** owns the tail promise the column is measured against:
  which items count as the tail is a product definition.
- **The pre-rank team** owns the proxy's cold-item signal: content or
  embedding similarity, not popularity, is what makes the column nonzero.

## Evidence boundary

The recorded surface-rate runs (600 and 2,000-item synthetic catalogues,
four seeds). It reads those artifacts; it does not re-run the proxies and
the numbers characterize synthetic data, not production catalogues.

## Check your mental model

Answer each before opening it.

**1. Why is the long-tail zero structural rather than a tuning problem?**

<details>
<summary>Answer</summary>

Because the signal itself is zero for cold items. Popularity is a count of
observed engagements, and a long-tail item has none — so its popularity
score is noise, and no threshold or scaling makes noise rank above a head
item's real count. The cheap proxy escapes the zero because it adds a
content signal that does not depend on engagement.

</details>

**2. What would an overall-only metric have hidden?**

<details>
<summary>Answer</summary>

The tail's disappearance. Popularity-only's overall surface rate (0.100-
0.400) looks acceptable, but its long-tail rate is 0.000 — every cold item
is cut before the fine-ranker ever sees it. An overall-only check would
pass while the pre-rank stage silently destroyed cold-start reach, which is
exactly why the stage reports the long-tail slice.

</details>

## Next

Back to [stage 03](../), or to
[when the cheap cut fails](../when-the-cheap-cut-fails/) which reads the same
stage's cut-agreement story.
