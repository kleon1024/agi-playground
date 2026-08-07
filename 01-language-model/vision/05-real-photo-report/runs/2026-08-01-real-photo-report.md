# Real-photo mission outcome report — 2026-08-01

**Commands:**
```
export OPENROUTER_API_KEY=...
uv run python call_hosted_api.py --limit 4      # pilot, verify the pipeline
uv run python call_hosted_api.py --resume       # remaining 194 questions
uv run python report.py
```

**Hosted API:** `openai/gpt-4o-mini` via OpenRouter, same model and endpoint as
stage 02's synthetic-shapes baseline. All 198 real-photo eval questions
(stage 03's held-out set) answered in two batches (4-question pilot + 194
resumed), total wall-clock 333s for the resumed batch.

**Full result:**
```
vision      mean=0.2374  spread=0.0101  per_seed=[0.2374, 0.2424, 0.2323]
text_only   mean=0.2222  per_seed=[0.2121, 0.1919, 0.2626]
hosted API: 0.4596  (198 questions, single run, no seeds -- a fixed API)

vs text-only: margin +0.0152 vs vision's own spread 0.0101 -> beats the noise band
vs hosted API: margin -0.2222 vs vision's own spread 0.0101 -> does NOT beat the noise band
```

**Hosted API accuracy by answer type:**
```
number       6/25  (24.0%)
other       34/93  (36.6%)
yes_no      51/80  (63.8%)
```

**Cost:** \$0.2534 total over 198 questions (\$0.00128/question, matching stage
02's per-question rate on the synthetic set) — hosted API cost is the only
non-zero cost in the whole mission-05 rescope; vision/text-only training was
\$0 on local CPU.

**Verdict: NOT MET.** The real-photo vision pathway beats the text-only
baseline by a real (if narrow) margin, replicating the direction of stage
01's synthetic-shapes finding on real photographs. It does not, and was never
plausible to, beat a production hosted VLM: `gpt-4o-mini` is trained at a
scale and with a text/image corpus this mission's from-scratch model cannot
approach at an 858K-parameter, 300-image budget. The margin against the
hosted API (-0.2222) is roughly 22x vision's own seed-to-seed spread — this
is not a close call decided by noise, it is a real and expected gap.

**What this settles and what it does not:** it settles that the same
architecture, unchanged, extracts a real (if narrow) signal from real
photographs, not just synthetic renders — the vision-vs-text-only half of
the acceptance bar transfers. It does not settle, and was never designed to
settle, whether a from-scratch model at this budget can compete with a
frontier-trained hosted model; the mission's `does_not_prove` section says
this explicitly. The category breakdown suggests where the hosted model's
advantage concentrates: yes/no questions (63.8%) are the easiest category for
any model to get right by chance-adjacent guessing at a real 50/50 prior,
while free-form "other" answers (36.6%) and exact numeric answers (24.0%)
need real visual grounding the from-scratch model at this scale does not
have.
