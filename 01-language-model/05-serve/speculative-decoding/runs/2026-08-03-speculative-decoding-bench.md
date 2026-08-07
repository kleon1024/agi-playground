# Run — greedy speculative decoding, from-scratch draft and target

## Command

```bash
cd 01-language-model/05-serve/speculative-decoding/core
python speculative.py
```

## Hardware and software

| | |
|---|---|
| CPU | Apple M1 Pro (local lane) |
| GPU | none — `torch.cuda.is_available()` is `False` in this environment, confirmed before this chapter was built |
| OS | macOS 15.6.1, Darwin 24.6.0 |
| torch | 2.10.0 |
| Data | tinyshakespeare (`karpathy/char-rnn`), same corpus and download path `foundations/01-first-training-loop` uses, character-level tokenizer, 65 symbols |
| Total wall-clock | 187.6s for the whole script (train both models, verify, benchmark) |
| Cost | \$0 (local CPU lane) |

## Models trained from scratch for this run

```
target: 4 layers, d_model=256, n_head=4, n_kv_head=2   ->  2,903,552 params (2.9M)
draft:  2 layers, d_model=96,  n_head=2, n_kv_head=2    ->    227,904 params (0.2M)
```

`draft-good` and `draft-poor` share this exact draft architecture and differ only in training
steps (600 vs. 40) — isolating draft *quality* as the one variable under test, not draft *size*.

```
target train:      600 steps, final loss 1.4756, wall-clock 138.42s
draft-good train:  600 steps, final loss 1.8840, wall-clock  34.28s
draft-poor train:   40 steps, final loss 3.2372, wall-clock   2.29s
```

## Result 1: correctness — exact match against plain target-only greedy decoding

```
baseline = generate_naive(target, prompt, 200)          # target alone, full recompute per step
spec_good = speculative_decode(target, draft_good, ...)  # draft proposes, target verifies
spec_poor = speculative_decode(target, draft_poor, ...)

exact match, draft-good: True
exact match, draft-poor: True
```

Both regimes produce token sequences identical to the target model's own plain greedy decoding,
regardless of draft quality — the guarantee this chapter's scope depends on (see README "What
this does not establish" for the boundary: this is the deterministic/greedy special case, not the
full stochastic rejection-sampling algorithm).

## Result 2: bench — 200 generated tokens, k=4, prompt "ROMEO:"

```
      config   wall_s  vs_baseline  accept_rate  accepted/round  rounds
    baseline    1.623         1.00           --              --     200
  draft-good    1.028         1.58        0.379            1.51      80
  draft-poor    1.735         0.94        0.159            0.63     123
```

`draft-good` (600 training steps) accepts 37.9% of its proposals, averaging 1.51 tokens per
verification round, and reaches 1.58x wall-clock over plain target-only decoding. `draft-poor`
(40 training steps, otherwise identical architecture) accepts only 15.9% of its proposals,
averaging 0.63 tokens per round, and is measurably *slower* than the baseline it was meant to
speed up (0.94x) — the extra draft forward passes and the wider verification batch on every low-
acceptance round cost more than the few tokens they occasionally save.

## Verdict

A cheap draft model's guesses are worth the target's verification check only when the draft is
good enough at the shared distribution to land a majority of its guesses — confirmed here as a
measured crossover, not asserted: the identical architecture flips from a 1.58x speedup to a 0.94x
slowdown purely as a function of how many training steps the draft received, with the target and
prompt held fixed. Both regimes are guaranteed byte-identical to plain greedy decoding regardless
of which side of that crossover the draft lands on.
