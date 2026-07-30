# Run — stage 03 pre-rank, cheap-proxy vs popularity-only long-tail surface rate

**Date:** 2026-07-30
**Hardware:** Apple Silicon (arm64), macOS (Darwin 24.6.0). CPU-only, stdlib
only (`random`, `argparse`, `dataclasses`) — no GPU involved.
**Cost:** \$0 (local lane).

## Command

```bash
python core/pre_rank.py                                    # default: 600 -> 60, k=10, seed=42
python core/pre_rank.py --seed 1
python core/pre_rank.py --seed 7
python core/pre_rank.py --seed 99
python core/pre_rank.py --catalogue-size 2000 --keep 150 --k 20   # funnel-realistic scale, seed=42
```

## Output, default scale (600 items, cut to 60, true top-10), across four seeds

```
seed  true-top10 long-tail  cheap-proxy surface (overall / long-tail)  popularity-only (overall / long-tail)
1     9                      0.200 / 0.111                              0.100 / 0.000
7     5                      0.600 / 0.200                              0.400 / 0.000
42    5                      0.600 / 0.200                              0.400 / 0.000
99    7                      0.300 / 0.143                              0.100 / 0.000
```

Rank agreement (rho, among kept), same seeds, for reference: cheap proxy
0.413/0.289/0.436/0.161, popularity-only 0.079/0.277/0.310/0.158 — noisy in
both directions and not the number that matters here.

## Output, funnel-realistic scale (2000 items, cut to 150, true top-20, seed=42)

```
true top-20 contains 17 long-tail items
cheap proxy (content + popularity):   surface rate overall 0.150, long-tail 0.000
popularity-only proxy:                surface rate overall 0.100, long-tail 0.000
```

## Verdict

At the chapter's default demo scale, the pattern the README claims is exact
and holds on every seed tried: **popularity-only's long-tail surface rate is
0.000 in all four runs** — by construction, a cold item's popularity is
noise, so it can never rank above a head item on that signal alone. The
cheap proxy's long-tail surface rate is never zero (0.111-0.200) because
`content_sim` gives it real, if imperfect, signal on cold items too.

At the wider funnel-realistic cut (2000/150/20), both proxies hit 0.000 on
long-tail surface at seed 42 — the cheap proxy's structural advantage did not
survive this particular ratio of catalogue size to keep count on this seed.
This is a real, unflattering data point, not cherry-picked away: the
chapter's mechanism claim ("cannot distinguish a gem from noise" vs. "can,
imperfectly") is about *capability*, not a guarantee that every cut size and
seed exhibits it — that qualifier was previously implicit in the README and
is now stated explicitly there.

`prod/lgbm_pre_rank.py` was not run: it imports `lightgbm`, which is not a
dependency of this repository's `pyproject.toml` and was not installed for
this run.
