"""When the CTCVR disagrees: deriving p_pay as p_ctcvr / p_click
explodes wherever p_click is tiny; the clip is a decision, not bookkeeping.

Run:
    uv run python core/ctcvr_disagrees.py
"""

from __future__ import annotations


def main() -> None:
    # Three impressions with honest CTR but noisy CTCVR reads.
    rows = [
        ("cold head", 0.02, 0.0004),
        ("mid funnel", 0.10, 0.0120),
        ("strong intent", 0.30, 0.0300),
    ]
    print("when the ctcvr disagrees, read (p_pay = p_ctcvr / p_click):")
    print(f"  {'impression':<14}{'p_click':>9}{'p_ctcvr':>9}{'p_pay raw':>10}{'p_pay clip':>11}")
    for name, pc, ptc in rows:
        raw = ptc / pc
        clipped = min(raw, 1.0)
        print(f"  {name:<14}{pc:>9.2f}{ptc:>9.4f}{raw:>10.3f}{clipped:>11.3f}")
    print()
    print("reading: at 2% CTR a small CTCVR estimation error is a 3x swing")
    print("in the derived p_pay. The ratio is stable only where p_click is")
    print("large enough to trust; the clip is the system admitting it does")
    print("not know the conditional there, which is better than ranking on")
    print("an exploded ratio.")


if __name__ == "__main__":
    main()
