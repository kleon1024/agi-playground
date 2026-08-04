# Run: instrumented training step-time distribution

**Command:**
```bash
cd infra/04-observability/core
python instrumented_train.py --steps 200 --out ../runs
```

**Hardware:** local dev box (CPU only).

**Software:** Python 3.11, PyTorch 2.10.0. Model: mission 01's `Config`/
`Transformer` (unmodified), 2 layers, d_model=128, vocab_size=512,
batch_size=8, seq_len=64.

**Wall-clock:** ~3.7s for 200 measured steps plus 5 warmup steps.

**Cost:** \$0 (local lane, CPU only).

**Metrics** (full per-step samples and histogram in
`instrumented-train-result.json` in this directory):

```
steps=200 tokens=102,400 final_loss=6.2450
step time p50=18.45ms p95=21.14ms mean=18.79ms min=16.43ms max=28.68ms
```

**Notes:** final_loss of 6.245 after 200 steps on random (untokenized,
uniformly sampled) input is expected and not a claim of learning — this
chapter's model never sees real text, only random token ids, since the
point is the timing instrumentation, not convergence. The step-time tail
(a handful of steps at 23-28ms against a 16-20ms typical range) persisted
across the 5-step warmup, meaning it is not purely first-call lazy-init
cost; it is consistent with normal GC/OS-scheduling jitter at this scale
and is named as such in the README, not investigated further here.
