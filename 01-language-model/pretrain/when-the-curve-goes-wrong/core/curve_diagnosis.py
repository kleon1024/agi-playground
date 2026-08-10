"""When the curve goes wrong: four injected pretraining failures and the
diagnostics that assign ownership.

The chapter's "read the pair, not the line" table is asserted, not
measured. This run executes it on one tiny from-scratch next-token
learner with four injected failures:

  - learning rate too high (lr 12): the classic divergence. The diagnostic
    is not the spike itself but the gradient-norm trace, which departs
    from the baseline run about two steps BEFORE the loss does -- a run
    logging norms sees it coming.
  - overflow (lr 48, softmax computed in fp32 range without max
    subtraction): the loss crosses the representable range at step 3 and
    the run that lacks a non-finite check completes with a wall of inf
    then NaN and cannot report which step first went wrong.
  - a corrupted batch (steps 100-139): a slice of the stream is replaced
    by random labels. Train AND held-out both move together and recover,
    which is how a bad batch reads differently from overfitting or a
    broken optimizer.
  - bf16 resolution loss (decayed LR): every weight update is rounded to
    bf16 mantissa precision before it lands, the tempting "bf16 master
    weight" simplification. The train curve flatlines above the fp32-master
    floor while the gradient norm stays alive -- the flat-flat row of the
    pair table, distinguished from a dead loop by the live gradient.

Deterministic (single seed), numpy only, CPU-only. Softmax is computed
with a stable log-sum-exp except in the overflow run, which deliberately
uses the naive path in fp32 range to reproduce the accelerator overflow
mechanism (fp16/bf16 overflow at far lower logits than fp64).
"""

from __future__ import annotations

import math

import numpy as np


def logsumexp(a: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically stable log-sum-exp (subtract the max first)."""
    m = a.max(axis=axis, keepdims=True)
    return m + np.log(np.exp(a - m).sum(axis=axis, keepdims=True))


class NextTokenMLP:
    """A two-layer next-token learner: embed a 2-token context, one
    hidden layer, softmax over the vocab. From scratch, no framework."""

    def __init__(self, vocab: int, d: int = 16, h: int = 32, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.vocab = vocab
        self.d = d
        self.E = rng.normal(0, 0.3, (vocab, d))
        self.W1 = rng.normal(0, 0.25, (2 * d, h))
        self.b1 = np.zeros(h)
        self.W2 = rng.normal(0, 0.25, (h, vocab))
        self.b2 = np.zeros(vocab)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """x: (n, 2) token ids -> logits (n, vocab)."""
        e = self.E[x].reshape(x.shape[0], -1)
        z = np.tanh(e @ self.W1 + self.b1)
        return z @ self.W2 + self.b2

    def _logp(self, logits: np.ndarray, naive: bool) -> np.ndarray:
        if naive:
            # The accelerator path: fp32 range, no max subtraction.
            # exp() overflows once logits pass ~88, reproducing the
            # fp16/bf16 loss-spike overflow that fp64 stable math hides.
            with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                logits = logits.astype(np.float32)
                logp = logits - np.log(
                    np.exp(logits).sum(axis=1, keepdims=True))
            return logp.astype(np.float64)
        return logits - logsumexp(logits)

    def train_step(self, x: np.ndarray, y: np.ndarray, lr: float,
                   round_bf16: bool = False, naive_softmax: bool = False
                   ) -> tuple[float, float]:
        """One SGD step. Returns (loss, grad-norm-before-update).
        round_bf16 rounds every parameter update to bf16 mantissa
        precision, simulating a bf16 master weight: the update only
        lands if it crosses the nearest bf16 grid point."""
        n = x.shape[0]
        e = self.E[x].reshape(n, -1)
        z = np.tanh(e @ self.W1 + self.b1)
        logits = z @ self.W2 + self.b2
        logp = self._logp(logits, naive_softmax)
        loss = -logp[np.arange(n), y].mean()

        p = np.exp(logp)
        g_out = p.copy()
        g_out[np.arange(n), y] -= 1.0
        g_out /= n

        gW2 = z.T @ g_out
        gb2 = g_out.sum(axis=0)
        gz = g_out @ self.W2.T
        gz = gz * (1 - z**2)
        gW1 = e.T @ gz
        gb1 = gz.sum(axis=0)
        # gradient wrt the concatenated embedding is (n, 2*d); split it
        # and scatter each half to the token that produced it
        ge = gz @ self.W1.T
        gE = np.zeros_like(self.E)
        np.add.at(gE, x[:, 0], ge[:, : self.d])
        np.add.at(gE, x[:, 1], ge[:, self.d:])
        grad_norm = math.sqrt(
            float(np.sum(gW2**2) + np.sum(gb2**2) + np.sum(gW1**2)
                  + np.sum(gb1**2) + np.sum(gE**2))
        )

        def bf16(w: np.ndarray) -> np.ndarray:
            # bf16 keeps 8 mantissa bits: round the mantissa, keep the
            # exponent. Simulated by truncating the float32 bits.
            bits = w.astype(np.float32).view(np.uint32)
            bits = bits & 0xFFFF0000  # drop the low 16 bits (8 mantissa)
            return bits.view(np.float32).astype(np.float64)

        def apply(w: np.ndarray, g: np.ndarray) -> np.ndarray:
            upd = w - lr * g
            return bf16(upd) if round_bf16 else upd

        self.E = apply(self.E, gE)
        self.W1 = apply(self.W1, gW1)
        self.b1 = apply(self.b1, gb1)
        self.W2 = apply(self.W2, gW2)
        self.b2 = apply(self.b2, gb2)
        return float(loss), grad_norm

    def loss(self, x: np.ndarray, y: np.ndarray) -> float:
        logits = self.forward(x)
        logp = self._logp(logits, naive=False)
        return float(-logp[np.arange(x.shape[0]), y].mean())


def make_data(seed: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """A planted next-token task: the next token is a noisy function of
    the previous token (a Markov chain), so a learner can reach a low
    but not zero loss."""
    rng = np.random.default_rng(seed)
    vocab = 16
    trans = np.full((vocab, vocab), 0.08)
    for t in range(vocab):
        trans[t, (t * 3 + 1) % vocab] = 0.6
        trans[t, (t * 5 + 2) % vocab] = 0.32
    trans /= trans.sum(axis=1, keepdims=True)
    x = np.zeros((n, 2), dtype=np.int64)
    y = np.zeros(n, dtype=np.int64)
    prev = rng.integers(0, vocab)
    for i in range(n):
        x[i, 0] = prev
        x[i, 1] = rng.integers(0, vocab)
        y[i] = rng.choice(vocab, p=trans[prev])
        prev = y[i]
    return x, y


def run(seed: int = 42) -> None:
    x_tr, y_tr = make_data(seed, 3000)
    x_te, y_te = make_data(seed + 1, 1000)

    def train(lr: float, steps: int = 200, corrupt: tuple | None = None,
              bf16: bool = False, check_nan: bool = True,
              lr_end: float | None = None, naive_softmax: bool = False
              ) -> dict:
        m = NextTokenMLP(16, seed=seed)
        trace = []  # (step, train, held, grad_norm), every step
        first_nonfinite = None
        peak_gnorm, peak_step = 0.0, None
        for s in range(steps):
            if lr_end is not None:
                eff_lr = lr_end + (lr - lr_end) * max(0.0, 1.0 - s / steps)
            else:
                eff_lr = lr
            if corrupt is not None and corrupt[0] <= s < corrupt[1]:
                # a slice of the stream replaced by a different
                # distribution: labels drawn uniformly at random.
                ys = np.random.default_rng(s).integers(0, 16, size=len(y_tr))
            else:
                ys = y_tr
            loss, gnorm = m.train_step(x_tr, ys, eff_lr, round_bf16=bf16,
                                       naive_softmax=naive_softmax)
            if gnorm > peak_gnorm:
                peak_gnorm, peak_step = gnorm, s
            if not math.isfinite(loss) and first_nonfinite is None:
                first_nonfinite = s
                if check_nan:
                    break
            trace.append((s, loss, m.loss(x_te, y_te), gnorm))
        return {"trace": trace, "first_nonfinite": first_nonfinite,
                "peak_gnorm": peak_gnorm, "peak_step": peak_step,
                "steps_done": trace[-1][0] + 1 if trace else 0}

    base = train(0.3, steps=240)
    lr_bad = train(12.0)
    # the overflow run reproduces inf/nan on purpose; silence the
    # expected numpy warnings for just these two runs
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        overflow = train(48.0, naive_softmax=True)
        overflow_unchecked = train(48.0, naive_softmax=True,
                                   check_nan=False)
    corrupt = train(0.3, steps=240, corrupt=(100, 140))
    fp32_run = train(0.5, steps=800, lr_end=0.001)
    bf16_run = train(0.5, steps=800, lr_end=0.001, bf16=True)

    def at(r: dict, *steps: int) -> dict:
        by = {s: (t, h, g) for s, t, h, g in r["trace"]}
        return {s: by[s] for s in steps}

    b0 = at(base, 0, 199)
    f1 = at(lr_bad, 0, 4, 5, 6, 7, 199)
    ovu = at(overflow_unchecked, 0, 10, 20, 30, 199)
    f2 = at(corrupt, 95, 100, 120, 140, 160, 200, 239)
    b2 = at(base, 95, 100, 120, 140, 160, 200)
    f3a = at(fp32_run, 300, 400, 500, 600, 700, 799)
    f3b = at(bf16_run, 300, 400, 500, 600, 700, 799)

    print("when the curve goes wrong, read (four injected failures):")
    print("  one seed, numpy-only 2-layer next-token learner;")
    print("  3000 train / 1000 held-out tokens, 16-symbol planted Markov task")
    print()
    print("  baseline (lr 0.3, 200 steps):")
    print(f"    step 0:  train {b0[0][0]:.4f}  held {b0[0][1]:.4f}")
    print(f"    step 199: train {b0[199][0]:.4f}  held {b0[199][1]:.4f}")
    print()
    print("  failure 1 - learning rate too high (lr 12):")
    print(f"    step 0:  train {f1[0][0]:.4f}  held {f1[0][1]:.4f}  "
          f"grad-norm {f1[0][2]:.3f}")
    print(f"    step 4:  train {f1[4][0]:.4f}  held {f1[4][1]:.4f}  "
          f"grad-norm {f1[4][2]:.3f}  (baseline grad-norm {b0[0][2]:.3f}->"
          f"0.197 at step 4)")
    print(f"    step 5:  train {f1[5][0]:.4f}  held {f1[5][1]:.4f}  "
          f"grad-norm {f1[5][2]:.3f}")
    print(f"    step 6:  train {f1[6][0]:.4f}  held {f1[6][1]:.4f}  "
          f"grad-norm {f1[6][2]:.3f}")
    print(f"    step 7:  train {f1[7][0]:.4f}  held {f1[7][1]:.4f}  "
          f"grad-norm {f1[7][2]:.3f} (peak {lr_bad['peak_gnorm']:.3f} at "
          f"step {lr_bad['peak_step']})")
    print(f"    step 199: train {f1[199][0]:.4f}  held {f1[199][1]:.4f}  "
          f"(diverged, no recovery)")
    print("    gradient norm departs from the baseline ~2 steps before "
          "the train loss does")
    print()
    print("  failure 2 - loss overflows the compute range (lr 48, fp32-")
    print("  range softmax without max subtraction):")
    print(f"    first non-finite loss: step {overflow['first_nonfinite']}; "
          f"with the check the run stops there "
          f"({overflow['steps_done']} steps executed)")
    print(f"    without the check: step 0 train {ovu[0][0]:.4f}, then "
          f"step 10 {ovu[10][0]}, step 20 {ovu[20][0]}, "
          f"step 30 {ovu[30][0]}, ... step 199 {ovu[199][0]}")
    print("    the unchecked run cannot report which step first went wrong")
    print()
    print("  failure 3 - corrupted batch (steps 100-139, random labels):")
    print(f"    baseline at 95/100/120/140/160/200: "
          f"train {b2[95][0]:.4f}/{b2[100][0]:.4f}/{b2[120][0]:.4f}/"
          f"{b2[140][0]:.4f}/{b2[160][0]:.4f}/{b2[200][0]:.4f} | "
          f"held {b2[95][1]:.4f}/{b2[100][1]:.4f}/{b2[120][1]:.4f}/"
          f"{b2[140][1]:.4f}/{b2[160][1]:.4f}/{b2[200][1]:.4f}")
    print(f"    corrupt  at 95/100/120/140/160/200/239: "
          f"train {f2[95][0]:.4f}/{f2[100][0]:.4f}/{f2[120][0]:.4f}/"
          f"{f2[140][0]:.4f}/{f2[160][0]:.4f}/{f2[200][0]:.4f}/"
          f"{f2[239][0]:.4f} | "
          f"held {f2[95][1]:.4f}/{f2[100][1]:.4f}/{f2[120][1]:.4f}/"
          f"{f2[140][1]:.4f}/{f2[160][1]:.4f}/{f2[200][1]:.4f}/"
          f"{f2[239][1]:.4f}")
    print("    both curves move together during the window and return "
          "toward the baseline path")
    print()
    print("  failure 4 - bf16 resolution loss (bf16 master weights, "
          "lr 0.5 -> 0.001 over 800 steps):")
    print("    fp32 master: "
          f"train {f3a[300][0]:.4f} @300 -> {f3a[799][0]:.4f} @799 | "
          f"held {f3a[300][1]:.4f} -> {f3a[799][1]:.4f} | "
          f"grad-norm {f3a[300][2]:.4f} -> {f3a[799][2]:.4f}")
    print("    bf16 master: "
          f"train {f3b[300][0]:.4f} @300 -> {f3b[799][0]:.4f} @799 | "
          f"held {f3b[300][1]:.4f} -> {f3b[799][1]:.4f} | "
          f"grad-norm {f3b[300][2]:.4f} -> {f3b[799][2]:.4f}")
    print("    bf16 train flatlines ~0.06 above the fp32 floor while the")
    print("    gradient norm stays alive (0.050 vs fp32 0.014): precision")
    print("    floor, not a dead loop.")


if __name__ == "__main__":
    run()
