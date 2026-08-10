"""When the order exceeds the click: a head reports p(order) = 0.2 on
a sample whose p(click) = 0.1 — a contradiction that reaches the
blending stage as nonsense arithmetic.

Run:
    uv run python core/order_exceeds_click.py
"""

from __future__ import annotations


def main() -> None:
    rows = [
        ("strong-intent item", 0.12, 0.15, 0.31),
        ("cold lead", 0.02, 0.04, 0.07),
        ("normal item", 0.30, 0.08, 0.02),
    ]
    print("when the order exceeds the click, read (head outputs):")
    print(f"  {'sample':<18}{'p(click)':>9}{'p(order)':>9}{'p(pay)':>9}  contradiction")
    for name, pc, po, pp in rows:
        bad = "order>click" if po > pc else ("pay>order" if pp > po else "ok")
        print(f"  {name:<18}{pc:>9.2f}{po:>9.2f}{pp:>9.2f}  {bad}")
    print()
    print("reading: these heads were trained on different labels and nothing")
    print("ties them together, so their outputs can violate the funnel. the")
    print("next stage multiplies these numbers into a value estimate, and a")
    print("p(order) above p(click) is not a model nuance, it is a probability")
    print("that cannot exist; monitoring this violation rate is the cheapest")
    print("funnel-consistency check a team can run.")


if __name__ == "__main__":
    main()
