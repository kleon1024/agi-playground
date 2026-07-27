# Run — first training loop, Tiny Shakespeare

**Date:** 2026-07-26
**Hardware:** NVIDIA GeForce RTX 4090 (24GB, driver 591.86), WSL2 Ubuntu,
kernel 6.6.87.2-microsoft-standard-WSL2, reached over Tailscale SSH.
**Software:** Python 3.12, torch 2.13.0+cu130, uv-managed venv.
**Cost:** \$0 (local lane). 34.2 seconds of GPU time.

## Command

```bash
python core/train_gpt.py
```

No arguments — the configuration is constants at the top of the file
(`BLOCK=256`, `BATCH=64`, `N_LAYER=6`, `N_HEAD=6`, `N_EMB=384`, `LR=1e-3`,
`ITERS=2000`, seed 1337). The Tiny Shakespeare corpus (1.1MB) is downloaded on
first run.

## Output

```
vocab=65  params=10.75M  device=NVIDIA GeForce RTX 4090
iter     0  train 4.3266  val 4.3272     0.6s      0.0k tok/s
iter   250  train 2.5375  val 2.5448     5.1s    810.9k tok/s
iter   500  train 2.0374  val 2.0952     9.2s    889.7k tok/s
iter   750  train 1.6536  val 1.8108    13.4s    920.0k tok/s
iter  1000  train 1.4815  val 1.6638    17.5s    935.8k tok/s
iter  1250  train 1.3846  val 1.6047    21.7s    945.2k tok/s
iter  1500  train 1.3269  val 1.5698    25.8s    951.5k tok/s
iter  1750  train 1.2844  val 1.5447    30.0s    956.1k tok/s
iter  2000  train 1.2753  val 1.5383    34.2s    959.5k tok/s

peak VRAM: 1.65 GB
```

Chart: [`loss.png`](loss.png).

## Sample (temperature 0.8, 400 tokens, from an empty context)

```
ANGELO:
Any coward, is the time: and bubzed in my reason
That answer'd thee use as they come.

Harery:
We must follow'd on my tongue to the chamber:
Though with is the neck; ladiest drop the deed?
I never bewing well in you hear some dead:
The princess of young to see the earth death:
I will make all already her evils, where dost
As we had no blood of his business noble to
Is no prisoner to thy f
```

## Throughput sanity check

The headline 959.5k tokens/s is characters, not BPE tokens, and the corpus is
seen roughly 30 times over — so it is not 33M tokens of fresh data. The
implied hardware utilization is the number worth keeping:

- Training FLOPs ≈ `6 × params` per token = 6 × 10.75M ≈ 64.5 MFLOP, plus
  ~7 MFLOP for attention at this context length → ~71 MFLOP/token
- 959.5k tok/s × 71 MFLOP ≈ **68 TFLOP/s**

Against 138.8 TFLOP/s measured for raw bf16 matmul on this card (see
[`infra/local-4090.md`](../../../infra/local-4090.md)), that is **~49%
utilization** — a believable figure for a model this small, where kernel launch
overhead and undersized matmuls prevent saturation. A substantially higher
number would indicate a measurement bug rather than a fast model.

Derived totals: 64 sequences × 256 tokens × 2000 iterations = 32.8M tokens in
34.2s.

## Notes

- Step-0 loss of 4.3266 sits just above `ln(65) = 4.174`, the uniform-random
  baseline over the 65-character vocabulary — the initialization sanity check
  described in the lesson.
- Train/validation divergence (1.2753 vs 1.5383 at the end, from parity at step
  0) is memorization of a 1.1MB corpus, not an architecture defect.
- Peak allocation of 1.65 GB is 7% of the card. This run is not
  hardware-limited in any respect.
