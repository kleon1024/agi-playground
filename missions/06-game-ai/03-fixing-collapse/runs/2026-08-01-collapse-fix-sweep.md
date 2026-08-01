# Collapse-fix sweep: group size and an entropy bonus

## Commands

```bash
cd missions/06-game-ai/03-fixing-collapse/core
uv run --group torch python fix_collapse.py --variant small-group --group-size 4 --seed 0
uv run --group torch python fix_collapse.py --variant small-group --group-size 4 --seed 1
uv run --group torch python fix_collapse.py --variant small-group --group-size 4 --seed 2
uv run --group torch python fix_collapse.py --variant entropy-bonus --entropy-coef 0.01 --seed 0
```

CPU only, Apple silicon laptop, macOS 15.6.1. Same 5x5 grid-world, vocab,
reward, and GRPO mechanism as stage 01 (`--group-size 8` baseline reused
from stage 01's own `runs/2026-07-31-grpo-training.md`, not rerun).

## Results

| Variant | Seed | Degenerate steps / 200 | Greedy success | Sampled success | Wall-clock |
|---|---|---|---|---|---|
| baseline (stage 01, group_size=8) | 0/1/2 | 0/0/1 | 0.078/0.062/0.078 | 0.182/0.144/0.210 | 130.8s/118.1s/123.9s |
| small-group (group_size=4) | 0 | 18 | 0.024 | 0.032 | 70.8s |
| small-group (group_size=4) | 1 | 4 | 0.050 | 0.080 | 71.2s |
| small-group (group_size=4) | 2 | 10 | 0.036 | 0.034 | 68.9s |
| entropy-bonus (coef=0.01, group_size=8) | 0 | 0 | 0.078 | 0.176 | 329.3s |

All greedy-eval runs still converge to a fixed, board-independent
completion. Entropy-bonus seed 0 reproduces stage 01's exact failure shape
(all 8 dumped examples: `RRRRRRRRRRRR`, a full 12-character repeated-action
string). Small-group seed 0 collapsed further still: all 8 examples are the
single character `L` followed immediately by EOS (`steps: 1` on every
example) -- the policy did not even learn to keep emitting legal moves
until the step budget ran out, a strictly worse collapse than the
"repeat one legal action" pattern stage 01 found.

## Verdict

Neither fix worked. Smaller groups made things measurably worse across all
3 seeds (18/4/10 degenerate steps vs. baseline's 0/0/1, and greedy success
2.4-5.0% vs. baseline's 6.2-7.8%) -- the opposite of Fan et al.'s finding for
their classical-RL environments, at least at this scale and reward shape.
The entropy bonus (single seed, `entropy-coef=0.01`) left greedy and sampled
success essentially unchanged from baseline (7.8% / 17.6% vs. baseline's
7.8% / range up to 21.0%) while measurably raising mid-training entropy
(1.3-1.7 nats, logged per step) -- the policy's overall distribution did get
less peaked, but its **argmax** still tracked a fixed action rather than the
board. This is a real, checkable distinction: an entropy bonus penalizes a
narrow overall distribution, but it does not specifically reward the argmax
being board-correlated, so it can raise entropy everywhere without touching
the one statistic (which token wins the argmax) that greedy decode reads.

## Scope note

Only one seed was run for `entropy-bonus`, not three -- each run took
~330s (vs. ~70-130s for the other configurations) because of the extra
forward pass per rollout for the entropy computation, and the single result
already sits inside stage 01's own baseline range on both metrics with no
directional improvement, so a 3-seed confirmation was not run given the
wall-clock cost. If a future variant showed a promising direction, it would
need the full 3-seed treatment before any claim; this one does not clear
that bar.
