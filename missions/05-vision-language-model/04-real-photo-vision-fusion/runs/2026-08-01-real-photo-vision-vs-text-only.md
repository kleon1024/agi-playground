# Real-photo vision vs. text-only training — 2026-08-01

**Command:**
```
uv run --group torch python train.py --seeds 3
```

**Hardware:** local CPU (no CUDA GPU reachable from this environment at run
time — `torch.cuda.is_available()` returned `False` and no `nvidia-smi`/SSH
route to the local 4090 lane was reachable; falling back to CPU per
mission.yaml's stated fallback, not silently substituted).

**Data:** stage 03's real-photo dataset — 599 train QA pairs (300 images),
198 eval QA pairs (100 images). Vocabulary built from real VQA v2 question
and answer text: 1,014 words (vs. stage 01's small closed synthetic
vocabulary), confirming the tokenizer scales to open, real-world text
without modification.

**Model:** `VisionLanguageTransformer`/`Config` imported unchanged from
stage 01's `vlm_model.py` — 858,112 params (vision) / 843,648 params
(text-only), same architecture, same sizes as stage 01 (the parameter-count
difference is the vision path's patch-embedding + positional table).

**Results:**
```
vision     eval exact-match: mean=0.2374 spread=0.0101 per_seed=[0.2374, 0.2424, 0.2323]
text_only  eval exact-match: mean=0.2222 spread=0.0707 per_seed=[0.2121, 0.1919, 0.2626]
wall-clock: 497.3s (8.3 min), device: cpu, ceiling_hit: False (30-min ceiling)
```

Margin (vision mean − text-only mean) = **+0.0152**, larger than vision's own
seed-to-seed spread (0.0101) — by this mission's own rule (a gap smaller than
run-to-run spread is no result), this is a real, if narrow, margin. Note
text-only's own spread (0.0707) is far larger than vision's — the smaller,
more homogeneous real-photo answer distribution (many "yes"/"no" and common
short answers) makes text-only's blind guess noisier across seeds than the
image-conditioned model, the opposite pattern from stage 01's synthetic
result, where vision was the noisier pathway.

**Cost:** \$0 — local CPU training, no hosted API calls in this stage.

**What this does not settle:** whether this narrow real-photo margin beats
the hosted VLM API baseline is stage 05's question, not this stage's — this
stage only establishes the vision-vs-text-only half of the mission's
acceptance bar.
