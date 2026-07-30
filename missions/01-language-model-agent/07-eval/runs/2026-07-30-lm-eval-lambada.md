# lm-eval-harness report — 2026-07-30

checkpoint       stage02/ckpt/ckpt.pt  (sha256 ffd32ce920c4..., same checkpoint the perplexity report used)
tokenizer        stage01/tokenizer_hf.json  (sha256 8e0feb8cce7b...)
harness          lm-evaluation-harness 0.4.12, installed into an opt-in `lm-eval` uv dependency group
task             lambada_openai, limit 200 of 5153, num_fewshot 0, device cpu
perplexity       138.316 +/- 30.977
accuracy         0.205 +/- 0.0286 (exact-match on the held-out final word)

Environment: this repo's local machine, CPU only (macOS arm64), `uv run --group lm-eval --group torch`.
The checkpoint and tokenizer were copied down from the remote box
(`/home/ding/agi-playground/stage02/ckpt/ckpt.pt`,
`/home/ding/agi-playground/stage01/tokenizer_hf.json`) to a local scratch path
for this run, since the repo's own git checkout does not track model
binaries. Wall clock: 46.5s total including harness startup and dataset
download from the HF Hub.

Two real bugs in `prod/lm_eval.py` blocked this run before this session and
were fixed to make it runnable at all, not to change what it measures:

1. **Self-import shadowing.** The file is named `lm_eval.py`, the same as the
   third-party package it imports. Python inserts a script's own directory
   at the front of `sys.path`, so `import lm_eval` resolved to this file
   itself rather than the installed package, and the module's own
   `except ImportError` handler caught the resulting failure and reported
   "lm-evaluation-harness is not installed" even with the package present.
   Fixed by stripping the script's own directory from `sys.path` before the
   import.
2. **Read-only `device` property.** `SpeedrunLM.__init__` set `self.device =
   device`, but the installed lm-eval-harness (0.4.12) exposes `device` as a
   property on the base `LM` class backed by `self._device`, with no setter.
   Fixed by assigning `self._device` directly.

does not prove:
  - This is a single static benchmark at a 200-example cap on an 88M
    from-scratch model with no instruction tuning for this task type;
    138 perplexity / 20.5% accuracy is not comparable to any frontier-model
    leaderboard entry, only to another run of this exact checkpoint under
    an identical task/limit/fewshot configuration.
  - Nothing here tests the agent-eval half of this stage's argument
    (`core/evaluate.py agent-report`, already measured separately) — this
    harness has no concept of a multi-turn trajectory.
