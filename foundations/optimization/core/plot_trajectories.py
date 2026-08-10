"""Render the loss surface and the three optimizers' real trajectories.

Re-runs core/optimizers.py so the plot always matches the numbers in
runs/optimizer-comparison.json, then saves runs/trajectories.png.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from optimizers import A, B, loss, main


def render(sgd_hist, mom_hist, adam_hist, out_path):
    xs = np.linspace(-1.2, 1.2, 240)
    ys = np.linspace(-1.2, 1.2, 240)
    xx, yy = np.meshgrid(xs, ys)
    zz = 0.5 * (A * xx**2 + B * yy**2)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))

    ax = axes[0]
    ax.contour(xx, yy, zz, levels=np.geomspace(0.05, zz.max(), 14), cmap="Greys", linewidths=0.6)
    for hist, label, color in [
        (sgd_hist, "SGD", "tab:red"),
        (mom_hist, "SGD + momentum", "tab:orange"),
        (adam_hist, "Adam", "tab:blue"),
    ]:
        n = min(len(hist), 120)  # first 120 steps: enough to show the shape
        ax.plot(hist[:n, 0], hist[:n, 1], color=color, linewidth=1.1, marker=".", markersize=2, label=label)
    ax.scatter([0], [0], color="black", marker="*", s=80, zorder=5, label="minimum")
    ax.set_xlabel("x (steep axis, curvature A=100)")
    ax.set_ylabel("y (shallow axis, curvature B=1)")
    ax.set_title("Trajectories on an ill-conditioned bowl (first 120 steps)")
    ax.legend(fontsize=8, loc="upper right")

    ax = axes[1]
    for hist, label, color in [
        (sgd_hist, "SGD", "tab:red"),
        (mom_hist, "SGD + momentum", "tab:orange"),
        (adam_hist, "Adam", "tab:blue"),
    ]:
        losses = [loss(p) for p in hist]
        ax.semilogy(losses, color=color, linewidth=1.2, label=label)
    ax.set_xlabel("step")
    ax.set_ylabel("loss (log scale)")
    ax.set_title("Loss vs. step, all three optimizers, same start point")
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    sgd_hist, mom_hist, adam_hist, _ = main()
    out = Path(__file__).resolve().parent.parent / "runs" / "trajectories.png"
    render(sgd_hist, mom_hist, adam_hist, out)
