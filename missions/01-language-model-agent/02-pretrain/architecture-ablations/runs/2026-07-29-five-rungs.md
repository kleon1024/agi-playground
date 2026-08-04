# The remaining five rungs — norm, position, activation, GQA, depth/width

The [MoE rung](2026-07-28-moe-rung.md) ran first and alone. This record covers
the other five, trained back to back on the same card overnight: 14 arms, three
seeds each, 42 runs, 9.55 GPU-hours. With the MoE rung the full ladder is 17
arms, 51 runs, 12.97 GPU-hours, \$0 on the local lane.

## Command

```bash
cd missions/01-language-model-agent/02-pretrain/architecture-ablations/core
for rung in norm activation gqa depth-width position; do
  python ablate.py --rung $rung --data ~/agi-playground/data/tokens \
      --seeds 3 --tokens 2e8 --budget "<declared per rung>" \
      --out ~/ablation-$rung.json
done
```

Control, hardware, schedule, and data are identical to the MoE rung: 8 layers,
`d_model` 512, `d_ff` 1368, 512-token sequences, 16,512-token vocabulary,
3e-4 peak with 2% warmup and cosine decay, 199,999,488 tokens per run, RTX 4090
under WSL2, torch 2.13.0+cu130, bf16 autocast. Arms within a rung share a
seed's batch sequence exactly; seeds differ from each other.

## The ladder handed itself a control

The control configuration appears in every rung — `rmsnorm`, `rope`, `swiglu`,
`kv8`, `L8-d512`, and `dense` are the same model, and they were run with the
same three seeds on the same batches. Six independent replications of one
configuration:

| Rung it appeared in | Arm name | 3-seed mean |
|---|---|---:|
| norm | `rmsnorm` | 3.8597 |
| position | `rope` | 3.8593 |
| activation | `swiglu` | 3.8604 |
| gqa | `kv8` | 3.8611 |
| depth-width | `L8-d512` | 3.8602 |
| moe | `dense` | 3.8608 |

**Range 0.0018, standard deviation of the mean 0.00066 — with the seeds, the
data, the order, and the configuration all held identical.** That residue is
GPU nondeterminism: non-deterministic reductions in the backward pass,
autotuned kernel selection, and bf16 accumulation order. Nothing was
misconfigured; this is what "same run twice" costs on this hardware.

It is worth more than it cost, because it is an assumption-free floor. Any
claim in this ladder resting on less than about 0.002 is resting on the
allocator.

## Results, as paired per-seed differences

Arms within a rung see identical batches in identical order, so the statistic
this design supports is the **per-seed difference**, not the gap between two
independently-noisy means. Negative means the arm beat the control.

| Rung | Arm vs control | seed 0 | seed 1 | seed 2 | mean |
|---|---|---:|---:|---:|---:|
| position | `learned` vs `rope` | +0.0762 | +0.0884 | +0.0813 | +0.0820 |
| position | `none` vs `rope` | +0.0981 | +0.1087 | +0.1084 | +0.1051 |
| depth-width | `L16-d320` vs `L8-d512` | +0.0618 | +0.0636 | +0.0699 | +0.0651 |
| depth-width | `L4-d752` vs `L8-d512` | −0.0121 | −0.0087 | −0.0024 | −0.0077 |
| gqa | `kv1` vs `kv8` | +0.0307 | +0.0421 | +0.0617 | +0.0448 |
| gqa | `kv2` vs `kv8` | +0.0152 | +0.0183 | +0.0408 | +0.0248 |
| gqa | `kv4` vs `kv8` | +0.0096 | +0.0004 | +0.0177 | +0.0092 |
| norm | `layernorm` vs `rmsnorm` | −0.0023 | +0.0052 | +0.0091 | +0.0040 |
| activation | `gelu` vs `swiglu` | +0.0001 | −0.0115 | −0.0031 | −0.0048 |

Three tiers fall out, and the tiers are the finding.

**Unambiguous — every seed agrees, by 10x the floor or more.** Position
encoding is the largest effect on the ladder: RoPE beats learned absolute
positions by 0.0820 and beats no positional information at all by 0.1051, on
every seed. Depth against width at matched parameters is nearly as stark in
one direction: 16 layers at `d_model` 320 is 0.0651 worse than 8 layers at 512,
on every seed. Both are far outside anything nondeterminism could produce.

**Consistent but underpowered — every seed agrees, but the margin is small.**
The GQA rung degrades monotonically as KV heads are removed, and every arm is
worse than `kv8` on every seed. The full range, `kv8` to `kv1`, is 0.0448. But
the adjacent step `kv8` to `kv4` is only 0.0092 with a per-seed spread from
0.0004 to 0.0177 — the direction is consistent, the magnitude is not resolved.
Wide-and-shallow beating the control by 0.0077 is the same shape of claim.

**No result — the sign flips between seeds.** `layernorm` is *better* than
`rmsnorm` on seed 0 and worse on seeds 1 and 2. `gelu` is worse than `swiglu`
on seed 0 and better on seeds 1 and 2. Neither rung ranks its arms at this
scale. That is a reportable outcome, not a failed experiment, and it is the
one this chapter most needed to be able to say.

Note the direction of that last one. The nominal 3-seed means put GELU ahead of
SwiGLU by 0.0048 — the opposite of the usual published ordering. Reporting that
as "GELU wins" would be precisely the error the ladder exists to prevent: it is
one seed's worth of noise wearing a result's clothes.

## Method limitations worth fixing before the next ladder

Three, recorded because they constrain what any reader can do with the numbers
above and because two of them are mistakes rather than tradeoffs.

**The metric is in-distribution fit, and only that.** Every loss is measured on
`val.bin`, a held-out slice of the same FineWeb-Edu shards `train.bin` was
built from. So the ladder ranks architectures by how well they predict
educational web text. It does not rank them by capability, and a rung that won
here could plausibly win because it suits this distribution rather than because
it is better. The box holds 1.7GB of raw Common Crawl WARC that no arm has ever
seen; scoring every arm on it as a second column would separate those two
readings, and was not done.

**`ablate.py` saves no checkpoints.** `train_one` trains, evaluates, returns a
number, and lets the model fall out of scope. That makes every additional
metric — top-1 accuracy, out-of-distribution loss, a benchmark suite —
cost a full 13-hour retrain instead of a re-scoring pass over saved weights.
It is a design mistake, not a constraint, and it is the reason this record
reports one number per run.

**No downstream task was scored.** A 33M-parameter model trained on 200M tokens
is not expected to separate from chance on the standard suites, so those scores
would be noise rather than evidence — but that expectation was not tested here,
and stating it is not the same as having measured it.

## What these runs do not establish

- **That RMSNorm and SwiGLU do not help.** They establish that 33M parameters
  over 200M tokens with three seeds cannot tell. Both are widely reported to
  help at larger scale, and nothing here contradicts that.
- **Any significance claim.** Three seeds cannot support one. What is reported
  is sign consistency and magnitude against a measured nondeterminism floor,
  which is weaker than a hypothesis test and is what the data can carry.
- **That the rankings survive scale.** The standing caution applies to every
  rung: a winner at 33M can lose at 7B.
- **Anything about wall-clock.** Every rung above is an equal-token comparison.
  `layernorm` finished a run in 720s against `rmsnorm`'s 841s, and `L16-d320`
  took 1,010s against `L8-d512`'s 839s, but no arm was given equal wall-clock.
