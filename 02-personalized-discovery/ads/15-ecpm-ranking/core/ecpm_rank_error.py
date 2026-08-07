"""Rank-error revenue audit for eCPM ranking.

The ranking consumes estimated pCTR; revenue realizes from true pCTR.
This audit perturbs one ad's pCTR at a time, re-ranks by estimated
eCPM (ties broken by bid), and measures realized revenue per impression
against the optimal ranking's 150.00.

Run:
    uv run python core/ecpm_rank_error.py
"""

from __future__ import annotations


def ecpm(bid: float, pctr: float) -> float:
    return bid * pctr * 1000


def main() -> None:
    # (name, bid, true pCTR). True eCPMs: Ad A 100, Ad B 150, Ad C 120.
    ads = [("Ad A", 2.00, 0.05), ("Ad B", 0.50, 0.30), ("Ad C", 1.00, 0.12)]
    errors = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
    true_ecpm = {name: ecpm(bid, pctr) for name, bid, pctr in ads}
    optimal = max(true_ecpm.values())

    def rank(estimated: dict[str, float]) -> list[tuple[str, float, float]]:
        # Descending eCPM; ties broken by bid (higher bid wins), then name.
        ordered = sorted(
            ads,
            key=lambda a: (-estimated[a[0]], -a[1], a[0]),
        )
        return [(name, estimated[name], true_ecpm[name]) for name, _, _ in ordered]

    print("rank-error audit: estimates = true pCTR; optimal revenue per")
    print(f"impression = {optimal:.2f} (Ad B). Perturb one ad's pCTR at a")
    print("time; re-rank by estimated eCPM, ties broken by bid; realized")
    print("revenue uses the winner's true eCPM.\n")
    print(f"  {'perturbed':>9} {'error':>6} {'winner':>7} "
          f"{'realized':>9} {'loss':>6}")
    flips = 0
    total_loss = 0.0
    cells = 0
    for target in ads:
        for mult in errors:
            estimated = {}
            for name, bid, pctr in ads:
                p = pctr * (mult if name == target[0] else 1.0)
                estimated[name] = ecpm(bid, p)
            order = rank(estimated)
            winner = order[0][0]
            realized = order[0][2]
            loss = optimal - realized
            if winner != "Ad B":
                flips += 1
            total_loss += loss
            cells += 1
            if mult in (0.5, 1.25, 1.5, 2.0):
                print(f"  {target[0]:>9} {mult:>6.2f} {winner:>7} "
                      f"{realized:>9.2f} {loss:>6.2f}")

    print(f"\ngrid: {cells} perturbations; winner flips in {flips} "
          f"({flips / cells:.1%})")
    print(f"mean realized revenue {optimal - total_loss / cells:.2f} "
          f"vs optimal {optimal:.2f} (mean loss {total_loss / cells:.2f})")
    print("\nreading: half-measure errors that keep Ad B on top cost nothing;")
    print("errors that flip the winner cost 30-50 per impression. The ranking")
    print("is only as good as the estimate, and the audit's realized column is")
    print("the online check that catches the flip before revenue reports it.")


if __name__ == "__main__":
    main()
