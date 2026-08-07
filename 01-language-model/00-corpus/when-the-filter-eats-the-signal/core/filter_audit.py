"""The quality filter that eats the signal, measured by class.

Stage 00's funnel drops 18.3 percent of raw web text and keeps the rest.
The washing step is a set of gates -- language, diversity, symbol ratio,
length, repetition -- and every gate is a threshold someone tuned. This
script asks what happens when a gate is tuned on the wrong slice of the
corpus: a dev sample that happens to be junk-heavy and code-poor teaches
the filter that symbol-heavy text is spam, and the filter then removes
the code-heavy tail of the signal population at nearly the junk rate.

The population is synthetic but shaped like a crawl: 60 percent templated
boilerplate (low word diversity, low symbol ratio, high repetition) and
40 percent technical long-tail signal split into prose-like docs and a
code-heavy slice -- code repeats keywords, so it has middling diversity
and real repetition, plus a high symbol ratio that a quality filter can
read as spam. The audit runs two weight sets at the same total removal
rate:

1. **Biased weights**, tuned on a junk-heavy, code-poor dev slice -- the
   symbol-ratio gate is overweighted, length is ignored.
2. **Balanced weights**, tuned on a class-stratified gold holdout -- the
   same four signals with balanced weights.

For each weight set it removes the same bottom 55 percent of the corpus
and measures what was removed by gold class, how the survivor
distribution shifted, and a per-gate drop audit that names which gate
eats the signal -- the case-finding step a release gate needs.

Run:
    uv run python core/filter_audit.py
"""

from __future__ import annotations

import random

N_DOCS = 20_000
JUNK_FRACTION = 0.60
CODE_FRACTION_OF_SIGNAL = 0.40
REMOVE_FRACTION = 0.55
SEED = 11


def draw_junk(rng: random.Random) -> dict[str, float]:
    """Templated boilerplate: low diversity, low symbol ratio, repetitive."""
    return {
        "diversity": 0.18 + 0.14 * rng.random(),
        "symbol": 0.01 + 0.04 * rng.random(),
        "length": 0.10 + 0.30 * rng.random(),
        "repetition": 0.55 + 0.30 * rng.random(),
    }


def draw_signal(rng: random.Random) -> dict[str, float]:
    """Technical long-tail: prose docs or code-heavy docs."""
    if rng.random() < CODE_FRACTION_OF_SIGNAL:
        # Code repeats keywords: middling diversity, real repetition.
        return {
            "diversity": 0.35 + 0.20 * rng.random(),
            "symbol": 0.15 + 0.30 * rng.random(),
            "length": 0.20 + 0.80 * rng.random(),
            "repetition": 0.20 + 0.25 * rng.random(),
        }
    else:
        return {
            "diversity": 0.55 + 0.30 * rng.random(),
            "symbol": 0.03 + 0.07 * rng.random(),
            "length": 0.20 + 0.80 * rng.random(),
            "repetition": 0.05 + 0.15 * rng.random(),
        }


def quality_score(
    doc: dict[str, float], w_diversity: float, w_symbol: float,
    w_length: float, w_repetition: float,
) -> float:
    """The funnel's heuristic: higher is cleaner."""
    return (
        w_diversity * doc["diversity"]
        + w_symbol * (1.0 - doc["symbol"])
        + w_length * doc["length"]
        + w_repetition * (1.0 - doc["repetition"])
    )


def audit(
    docs: list[dict[str, float]],
    labels: list[bool],
    weights: tuple[float, float, float, float],
) -> dict[str, object]:
    """Remove the bottom REMOVE_FRACTION by score; measure by class."""
    scores = [quality_score(d, *weights) for d in docs]
    order = sorted(range(len(docs)), key=lambda i: scores[i])
    n_remove = int(REMOVE_FRACTION * len(docs))
    removed = set(order[:n_remove])
    kept = set(order[n_remove:])

    removed_junk = sum(1 for i in removed if not labels[i])
    removed_signal = sum(1 for i in removed if labels[i])
    signal_total = sum(1 for l in labels if l)
    junk_total = len(docs) - signal_total
    removed_code = sum(
        1 for i in removed if labels[i] and docs[i]["symbol"] >= 0.15
    )
    code_total = sum(
        1 for i in range(len(docs)) if labels[i] and docs[i]["symbol"] >= 0.15
    )

    def mean(feature: str, idx: set[int]) -> float:
        return sum(docs[i][feature] for i in idx) / len(idx)

    code_kept = sum(
        1 for i in kept if labels[i] and docs[i]["symbol"] >= 0.15
    )
    # Drop audit: what do the removed signal docs look like versus the kept
    # ones? This is the case-finding step -- it needs the gold class labels.
    removed_signal_docs = [docs[i] for i in removed if labels[i]]
    kept_signal_docs = [docs[i] for i in kept if labels[i]]
    removed_junk_docs = [docs[i] for i in removed if not labels[i]]

    def mean_feat(feature: str, subset: list[dict[str, float]]) -> float:
        return sum(d[feature] for d in subset) / len(subset)

    return {
        "removed_junk": removed_junk,
        "removed_signal": removed_signal,
        "removed_junk_rate": removed_junk / junk_total,
        "removed_signal_rate": removed_signal / signal_total,
        "removed_code_rate": removed_code / code_total,
        "removed_share_signal": removed_signal / n_remove,
        "survivor_diversity": mean("diversity", kept),
        "full_diversity": mean("diversity", set(range(len(docs)))),
        "survivor_length": mean("length", kept),
        "full_length": mean("length", set(range(len(docs)))),
        "survivor_code_share": code_kept / len(kept),
        "full_code_share": code_total / len(docs),
        "signal_kept_share": 1.0 - removed_signal / signal_total,
        "removed_signal_symbol": mean_feat("symbol", removed_signal_docs),
        "kept_signal_symbol": mean_feat("symbol", kept_signal_docs),
        "removed_junk_symbol": mean_feat("symbol", removed_junk_docs),
        "removed_signal_diversity": mean_feat(
            "diversity", removed_signal_docs
        ),
        "kept_signal_diversity": mean_feat("diversity", kept_signal_docs),
    }


def main() -> None:
    rng = random.Random(SEED)
    docs: list[dict[str, float]] = []
    labels: list[bool] = []
    for _ in range(N_DOCS):
        is_signal = rng.random() >= JUNK_FRACTION
        docs.append(draw_signal(rng) if is_signal else draw_junk(rng))
        labels.append(is_signal)

    biased = (0.35, 0.45, 0.05, 0.15)  # symbol overweighted, length ignored
    balanced = (0.40, 0.20, 0.20, 0.20)
    results = {name: audit(docs, labels, w) for name, w in (
        ("biased", biased),
        ("balanced", balanced),
    )}

    print(
        f"population: {N_DOCS} docs, "
        f"{100*(1-JUNK_FRACTION):.0f}% signal (of which "
        f"{100*CODE_FRACTION_OF_SIGNAL:.0f}% code-heavy), "
        f"removal rate {100*REMOVE_FRACTION:.0f}%"
    )
    for name in ("biased", "balanced"):
        r = results[name]
        print()
        if name == "biased":
            print("biased weights (symbol 0.45, length 0.05) -- tuned on a")
            print("junk-heavy, code-poor dev slice:")
        else:
            print("balanced weights (symbol 0.20, length 0.20) -- tuned on a")
            print("class-stratified gold holdout:")
        print(
            f"  removed {r['removed_junk'] + r['removed_signal']} docs = "
            f"{r['removed_junk']} junk ({100*r['removed_junk_rate']:.1f}%) + "
            f"{r['removed_signal']} signal ({100*r['removed_signal_rate']:.1f}%)"
        )
        print(
            f"  removed set is {100*r['removed_share_signal']:.1f}% signal; "
            f"signal kept {100*r['signal_kept_share']:.1f}% "
            f"({100*r['removed_code_rate']:.1f}% of code-heavy signal removed)"
        )
        print(
            f"  survivor shift: diversity {r['full_diversity']:.2f} -> "
            f"{r['survivor_diversity']:.2f}, length {r['full_length']:.2f} -> "
            f"{r['survivor_length']:.2f}, code share "
            f"{100*r['full_code_share']:.0f}% -> {100*r['survivor_code_share']:.0f}%"
        )
        print(
            "  drop audit of removed signal docs: mean symbol ratio "
            f"{r['removed_signal_symbol']:.2f} (kept signal "
            f"{r['kept_signal_symbol']:.2f}, removed junk "
            f"{r['removed_junk_symbol']:.2f}), mean diversity "
            f"{r['removed_signal_diversity']:.2f} (kept "
            f"{r['kept_signal_diversity']:.2f})"
        )

    r_b = results["biased"]
    r_c = results["balanced"]
    print()
    print(f"verdict: at the same {100*REMOVE_FRACTION:.0f}% removal rate the "
          "biased filter")
    print(f"removes {100*r_b['removed_signal_rate']:.1f}% of the signal "
          f"population vs {100*r_c['removed_signal_rate']:.1f}% for the "
          f"balanced one -- {100*r_b['removed_code_rate']:.1f}% of the "
          "code-heavy slice against")
    print(f"{100*r_c['removed_code_rate']:.1f}%.")
    print("The drop audit shows what the removed signal docs are: mean")
    print(f"symbol ratio {r_b['removed_signal_symbol']:.2f} against "
          f"{r_b['kept_signal_symbol']:.2f} for kept signal -- the filter")
    print("removed the code-heavy slice, whose high symbol ratio the biased")
    print("weights scored as spam. A wash that looks clean by total count is")
    print("a wash that removed the code tail; the class-stratified audit is")
    print("the only thing that sees it.")


if __name__ == "__main__":
    main()
