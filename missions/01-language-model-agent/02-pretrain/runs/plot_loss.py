"""Draw the stage-02 loss curve from the checkpoint's history.json.

Standard library only, and it emits SVG rather than a raster, for two reasons
that both matter more than they sound: the chart stays sharp at any zoom on the
docs site, and a text format means a future change to the curve shows up as a
readable diff instead of a new binary blob.

Colours are chosen to be legible on both the light and dark site themes, since
an `<img>` cannot inherit the page's colour.

    python plot_loss.py history.json loss.svg
"""

import json
import math
import sys
from pathlib import Path

W, H = 720, 380
PAD_L, PAD_R, PAD_T, PAD_B = 62, 18, 22, 46

AXIS = "#8a8a8a"
CURVE = "#4f8ef7"
REFERENCE = "#c2703f"
BEST = "#3fa06a"

VOCAB_SIZE = 16512


def scale(value: float, lo: float, hi: float, out_lo: float, out_hi: float) -> float:
    return out_lo + (value - lo) / (hi - lo) * (out_hi - out_lo)


def main() -> None:
    history = json.loads(Path(sys.argv[1]).read_text())
    points = [(h["step"], h["val_loss"]) for h in history if h.get("val_loss") is not None]
    uniform = math.log(VOCAB_SIZE)

    x_max = max(step for step, _ in points)
    y_lo, y_hi = 3.0, 10.0
    def px(step: float) -> float:
        return scale(step, 0, x_max, PAD_L, W - PAD_R)

    def py(loss: float) -> float:
        return scale(loss, y_hi, y_lo, PAD_T, H - PAD_B)

    best_step, best_loss = min(points, key=lambda p: p[1])
    final_step, final_loss = points[-1]

    out = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}" font-family="system-ui, sans-serif" font-size="12">'
        ),
        f'<title>Stage 02 validation loss over {x_max:,} steps</title>',
    ]

    for loss in range(3, 11):
        y = py(loss)
        out.append(
            f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" '
            f'stroke="{AXIS}" stroke-opacity="0.18"/>'
        )
        out.append(f'<text x="{PAD_L - 10}" y="{y + 4:.1f}" fill="{AXIS}" text-anchor="end">{loss}</text>')

    for step in range(0, x_max + 1, 5000):
        x = px(step)
        out.append(
            f'<line x1="{x:.1f}" y1="{PAD_T}" x2="{x:.1f}" y2="{H - PAD_B}" '
            f'stroke="{AXIS}" stroke-opacity="0.12"/>'
        )
        out.append(
            f'<text x="{x:.1f}" y="{H - PAD_B + 18}" fill="{AXIS}" text-anchor="middle">'
            f'{step // 1000}k</text>'
        )

    # The uniform-distribution loss: where an untrained model must start.
    y_uniform = py(uniform)
    out.append(
        f'<line x1="{PAD_L}" y1="{y_uniform:.1f}" x2="{W - PAD_R}" y2="{y_uniform:.1f}" '
        f'stroke="{REFERENCE}" stroke-width="1.5" stroke-dasharray="6 4"/>'
    )
    out.append(
        f'<text x="{W - PAD_R - 6}" y="{y_uniform - 7:.1f}" fill="{REFERENCE}" text-anchor="end">'
        f'ln({VOCAB_SIZE:,}) = {uniform:.3f} — uniform guess</text>'
    )

    path = " ".join(
        f"{'M' if i == 0 else 'L'}{px(step):.1f},{py(loss):.1f}"
        for i, (step, loss) in enumerate(points)
    )
    out.append(f'<path d="{path}" fill="none" stroke="{CURVE}" stroke-width="2.2"/>')

    out.append(
        f'<circle cx="{px(best_step):.1f}" cy="{py(best_loss):.1f}" r="4" fill="{BEST}"/>'
    )
    # The tail is flat and sits just above the x-axis labels, so both
    # annotations go in a legend rather than beside the points they describe.
    # The gap between them is the reason for the legend: the run did not end at
    # its best checkpoint, and a chart that hides that is doing the rounding
    # this repository forbids in prose.
    out.append(
        f'<text x="{PAD_L + 8}" y="{PAD_T + 40}" fill="{BEST}">'
        f'best {best_loss:.4f} at step {best_step:,}</text>'
    )
    out.append(
        f'<text x="{PAD_L + 8}" y="{PAD_T + 58}" fill="{AXIS}">'
        f'final {final_loss:.4f} at step {final_step:,}</text>'
    )

    out.append(
        f'<text x="{PAD_L}" y="{H - 8}" fill="{AXIS}">optimizer step</text>'
    )
    out.append(
        f'<text transform="translate(16,{H / 2:.0f}) rotate(-90)" fill="{AXIS}" '
        f'text-anchor="middle">validation loss (nats/token)</text>'
    )
    out.append("</svg>")

    Path(sys.argv[2]).write_text("\n".join(out) + "\n")
    print(f"wrote {sys.argv[2]}: {len(points)} points, best {best_loss:.4f} @ {best_step:,}")


if __name__ == "__main__":
    main()
