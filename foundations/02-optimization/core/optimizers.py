"""SGD, momentum, and Adam, implemented from scratch, racing on one
ill-conditioned quadratic bowl.

No torch.optim, no autograd — the gradient of a quadratic is closed-form, so
every update rule below is the actual arithmetic each optimizer performs,
with nothing hidden inside a library call. Runs in well under a second on a
laptop CPU.

See the lesson README for what the numbers mean, and runs/ for a recorded
execution.
"""

import json
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- surface
# L(x, y) = 0.5 * (A * x^2 + B * y^2), A >> B: a bowl 100x steeper along x
# than along y. Condition number = A / B.
A, B = 100.0, 1.0
CONDITION_NUMBER = A / B
START = np.array([1.0, 1.0])
MAX_STEPS = 4000
LOSS_TOL = 1e-6


def loss(p):
    x, y = p
    return 0.5 * (A * x * x + B * y * y)


def grad(p):
    x, y = p
    return np.array([A * x, B * y])


def run_sgd(lr, max_steps=MAX_STEPS):
    p = START.copy()
    history = [p.copy()]
    for step in range(1, max_steps + 1):
        p = p - lr * grad(p)
        history.append(p.copy())
        if loss(p) < LOSS_TOL:
            return np.array(history), step
    return np.array(history), None


def run_momentum(lr, mu, max_steps=MAX_STEPS):
    p = START.copy()
    v = np.zeros_like(p)
    history = [p.copy()]
    for step in range(1, max_steps + 1):
        v = mu * v - lr * grad(p)
        p = p + v
        history.append(p.copy())
        if loss(p) < LOSS_TOL:
            return np.array(history), step
    return np.array(history), None


def run_adam(lr, beta1=0.9, beta2=0.999, eps=1e-8, max_steps=MAX_STEPS):
    p = START.copy()
    m = np.zeros_like(p)
    v = np.zeros_like(p)
    history = [p.copy()]
    for step in range(1, max_steps + 1):
        g = grad(p)
        m = beta1 * m + (1 - beta1) * g
        v = beta2 * v + (1 - beta2) * (g * g)
        m_hat = m / (1 - beta1**step)
        v_hat = v / (1 - beta2**step)
        p = p - lr * m_hat / (np.sqrt(v_hat) + eps)
        history.append(p.copy())
        if loss(p) < LOSS_TOL:
            return np.array(history), step
    return np.array(history), None


def per_axis_progress(history):
    """Sign flips on the steep axis: a direct, countable oscillation measure."""
    x = history[:, 0]
    signs = np.sign(x[1:-1])
    flips = int(np.sum(signs[1:] != signs[:-1]))
    return flips


def main():
    t0 = time.time()

    sgd_lr = 0.019  # just under the divergence threshold 2/A = 0.02
    mom_lr, mom_mu = 0.01, 0.9  # under 2*(1+mu)/A = 0.038 stability bound
    adam_lr = 0.1

    sgd_hist, sgd_steps = run_sgd(sgd_lr)
    mom_hist, mom_steps = run_momentum(mom_lr, mom_mu)
    adam_hist, adam_steps = run_adam(adam_lr)

    wall_clock_s = time.time() - t0

    result = {
        "surface": {"A": A, "B": B, "condition_number": CONDITION_NUMBER, "start": START.tolist()},
        "loss_tolerance": LOSS_TOL,
        "max_steps": MAX_STEPS,
        "wall_clock_s": wall_clock_s,
        "sgd": {
            "lr": sgd_lr,
            "steps_to_converge": sgd_steps,
            "final_loss": float(loss(sgd_hist[-1])),
            "final_point": sgd_hist[-1].tolist(),
            "sign_flips_on_steep_axis": per_axis_progress(sgd_hist),
            "n_history_points": len(sgd_hist),
        },
        "momentum": {
            "lr": mom_lr,
            "mu": mom_mu,
            "steps_to_converge": mom_steps,
            "final_loss": float(loss(mom_hist[-1])),
            "final_point": mom_hist[-1].tolist(),
            "sign_flips_on_steep_axis": per_axis_progress(mom_hist),
            "n_history_points": len(mom_hist),
        },
        "adam": {
            "lr": adam_lr,
            "steps_to_converge": adam_steps,
            "final_loss": float(loss(adam_hist[-1])),
            "final_point": adam_hist[-1].tolist(),
            "sign_flips_on_steep_axis": per_axis_progress(adam_hist),
            "n_history_points": len(adam_hist),
        },
    }

    runs_dir = Path(__file__).resolve().parent.parent / "runs"
    runs_dir.mkdir(exist_ok=True)
    out_path = runs_dir / "optimizer-comparison.json"
    out_path.write_text(json.dumps(result, indent=2))

    for name, hist, steps in [("sgd", sgd_hist, sgd_steps), ("momentum", mom_hist, mom_steps), ("adam", adam_hist, adam_steps)]:
        conv = f"{steps} steps" if steps is not None else f"did not reach tol in {MAX_STEPS}"
        print(f"{name:10s} {conv:28s} final_loss={loss(hist[-1]):.3e}  flips={per_axis_progress(hist)}")

    print(f"\nwall_clock_s={wall_clock_s:.4f}")
    print(f"wrote {out_path}")

    return sgd_hist, mom_hist, adam_hist, result


if __name__ == "__main__":
    main()
