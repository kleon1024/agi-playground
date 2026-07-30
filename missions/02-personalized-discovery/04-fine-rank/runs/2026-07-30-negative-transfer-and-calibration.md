# Run — stage 04 fine-rank, negative transfer and calibration

**Date:** 2026-07-30
**Hardware:** Apple Silicon (arm64), macOS (Darwin 24.6.0). CPU-only; no GPU
involved anywhere in this stage.
**Software:** Python 3, PyTorch 2.10.0, scikit-learn 1.8.0 (for the `prod/`
isotonic-regression path only; `core/` is stdlib-only).
**Cost:** \$0 (local lane).

## Command 1 — default trunk

```bash
python core/fine_rank.py
```

## Output 1

```
trunk hidden=8, epochs=25, lr=0.05

negative transfer: naive equal weighting vs. scale-normalized weighting
task               naive    balanced
click              0.807       0.825
completion         0.750       0.784
satisfaction       0.651       0.706
dwell              0.658       0.803

(binary tasks: pairwise ranking accuracy, 0.5 = chance, 1.0 = perfect.
 dwell: Pearson correlation between predicted and true seconds.)

calibration (click head, 400 held-out examples):
  ECE before Platt scaling   0.0722
  ECE after  Platt scaling   0.0552  (a=0.707, b=-0.158)
```

## Command 2 — wider trunk, trained longer

```bash
python core/fine_rank.py --hidden 16 --epochs 60
```

## Output 2

```
trunk hidden=16, epochs=60, lr=0.05

negative transfer: naive equal weighting vs. scale-normalized weighting
task               naive    balanced
click              0.773       0.828
completion         0.721       0.785
satisfaction       0.644       0.664
dwell             -0.080       0.809

(binary tasks: pairwise ranking accuracy, 0.5 = chance, 1.0 = perfect.
 dwell: Pearson correlation between predicted and true seconds.)

calibration (click head, 400 held-out examples):
  ECE before Platt scaling   0.0956
  ECE after  Platt scaling   0.0555  (a=0.699, b=0.143)
```

At the wider trunk, naive dwell correlation goes negative (-0.080): more
capacity and more training gives the raw-seconds gradient more room to pull
the shared trunk away from what the binary heads need, before normalization
fixes it back to 0.809.

## Command 3 — production lane

```bash
PYTHONPATH=core python prod/torch_fine_rank.py
```

## Output 3

```
trunk hidden=8, epochs=25, lr=0.01 (PyTorch, Adam)

calibration (click head, 400 held-out examples):
  ECE before calibration            0.1068
  ECE after isotonic regression      0.0000
```

Isotonic regression on this held-out set fits the calibration curve exactly
(ECE 0.0000) — expected for a nonparametric fit on the same 400-example set
it is evaluated against, unlike Platt scaling's two-parameter logistic
curve, which cannot chase every miscalibration shape and leaves 0.0552-0.0555
residual ECE in the `core/` runs above.

## Verdict

Every number the README's mechanism sections predict shows up in synthetic
data: balancing the loss raises `satisfaction`'s pairwise accuracy by 0.055
(default trunk) to 0.020 (wider trunk) over naive equal weighting, dwell's
correlation swings from 0.658/-0.080 (naive) to 0.803/0.809 (balanced) —
negative transfer gets worse, not better, with more model capacity — and a
two-parameter Platt fit closes roughly a quarter to half of the click head's
calibration error without touching ranking, while isotonic regression
overfits the same held-out set it is scored against.
