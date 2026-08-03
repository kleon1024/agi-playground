"""Three independent generations per model arm: does any difference clear spread?

A first pass ran one generation per arm and appeared to find a large effect:
Haiku, Sonnet and Opus put markdown scaffolding in roughly a third of their
answers while Fable and the human annotators put almost none in theirs, at
p < 0.005 by Fisher and McNemar. That result did not survive this script.
Fable's scaffolding rate across its own three generations is 2, 8, and 13 of
36 -- a within-arm spread wider than any gap between arms, which a
single-generation design reports as zero because it cannot see it.

So the tests were not miscomputed; the variance model behind them was wrong.
This script exists to make that variance visible, applying the acceptance
rule mission 08's report stage uses: a difference counts only when the margin
between arms exceeds the spread within an arm. Anything that fails that bar
prints as not established, never as a small effect.

The human arm has exactly one generation by construction -- the annotators
wrote each answer once -- so its spread is undefined and it is compared on
margin alone, which is stated wherever it appears.
"""

from __future__ import annotations

import json
import re
import statistics
from math import comb
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "four-authors"
MODEL_ARMS = ["haiku", "sonnet", "opus", "fable"]
GENS = ["", "-g2", "-g3"]

MARKERS = [
    re.compile(r"^\s*[-*+]\s+", re.MULTILINE),
    re.compile(r"\*\*[^*]+\*\*"),
    re.compile(r"^#{1,6}\s+", re.MULTILINE),
    re.compile(r"```"),
]


def scaffolded(text: str) -> bool:
    return any(m.search(text) for m in MARKERS)


def load():
    prompts = json.loads((FIXTURES / "prompts.json").read_text())
    ids = [p["id"] for p in prompts]
    cats = {p["id"]: p["category"] for p in prompts}
    human = {p["id"]: p["human"] for p in prompts}

    runs: dict[str, list[dict[str, str]]] = {}
    for arm in MODEL_ARMS:
        gens = []
        for suffix in GENS:
            path = FIXTURES / f"answers-{arm}{suffix}.jsonl"
            if not path.exists():
                continue
            rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
            if len(rows) == len(ids):
                gens.append({r["id"]: r["answer"] for r in rows})
        runs[arm] = gens
    return ids, cats, human, runs


def sign_test(wins: int, n: int) -> float:
    k = min(wins, n - wins)
    return min(sum(comb(n, i) for i in range(k + 1)) * 2 / 2**n, 1.0)


def main() -> None:
    ids, cats, human, runs = load()
    n_gen = {a: len(runs[a]) for a in MODEL_ARMS}
    print(f"prompts: {len(ids)}   generations per arm: {n_gen}\n")

    print("=== scaffolding rate per generation (answers out of 36) ===")
    print(f"{'arm':8} {'g1':>4} {'g2':>4} {'g3':>4}   {'mean':>6} {'spread':>7}")
    scaf_rates: dict[str, list[int]] = {}
    for arm in MODEL_ARMS:
        rates = [sum(scaffolded(g[i]) for i in ids) for g in runs[arm]]
        scaf_rates[arm] = rates
        cells = "".join(f"{r:>5}" for r in rates) + "     " * (3 - len(rates))
        spread = (max(rates) - min(rates)) if len(rates) > 1 else float("nan")
        print(f"{arm:8}{cells}  {statistics.mean(rates):>6.1f} {spread:>7.1f}")
    h_scaf = sum(scaffolded(human[i]) for i in ids)
    print(f"{'human':8}{h_scaf:>5}                     (one generation by construction)")

    print("\n=== does the scaffolding gap clear run-to-run spread? ===")
    for a in MODEL_ARMS:
        for b in MODEL_ARMS:
            if a >= b:
                continue
            margin = abs(statistics.mean(scaf_rates[a]) - statistics.mean(scaf_rates[b]))
            spread = max(
                (max(scaf_rates[a]) - min(scaf_rates[a])),
                (max(scaf_rates[b]) - min(scaf_rates[b])),
            )
            verdict = "CLEARS" if margin > spread else "does not clear"
            print(f"  {a:7} vs {b:7} margin {margin:>5.1f}  spread {spread:>4.1f}  -> {verdict}")

    print("\n=== median answer length per generation ===")
    print(f"{'arm':8} {'g1':>5} {'g2':>5} {'g3':>5}   {'mean':>7} {'spread':>7}")
    med_len: dict[str, list[float]] = {}
    for arm in MODEL_ARMS:
        meds = [statistics.median(len(g[i].split()) for i in ids) for g in runs[arm]]
        med_len[arm] = meds
        cells = "".join(f"{m:>6.0f}" for m in meds) + "      " * (3 - len(meds))
        spread = (max(meds) - min(meds)) if len(meds) > 1 else float("nan")
        print(f"{arm:8}{cells}  {statistics.mean(meds):>7.1f} {spread:>7.1f}")
    h_med = statistics.median(len(human[i].split()) for i in ids)
    print(f"{'human':8}{h_med:>6.0f}                       (one generation)")

    print("\n=== does any length gap clear spread? ===")
    for a in MODEL_ARMS:
        for b in MODEL_ARMS:
            if a >= b:
                continue
            margin = abs(statistics.mean(med_len[a]) - statistics.mean(med_len[b]))
            spread = max(
                max(med_len[a]) - min(med_len[a]), max(med_len[b]) - min(med_len[b])
            )
            verdict = "CLEARS" if margin > spread else "does not clear"
            print(f"  {a:7} vs {b:7} margin {margin:>6.1f}  spread {spread:>5.1f}  -> {verdict}")

    print("\n=== per-category length range (max/min of category medians) ===")
    cat_names = sorted(set(cats.values()))
    print(f"{'arm':8} {'g1':>7} {'g2':>7} {'g3':>7}   {'spread':>7}")
    for arm in MODEL_ARMS:
        ranges = []
        for g in runs[arm]:
            meds = [
                statistics.median(len(g[i].split()) for i in ids if cats[i] == c)
                for c in cat_names
            ]
            ranges.append(max(meds) / max(min(meds), 1))
        cells = "".join(f"{r:>8.1f}" for r in ranges) + "        " * (3 - len(ranges))
        spread = (max(ranges) - min(ranges)) if len(ranges) > 1 else float("nan")
        print(f"{arm:8}{cells}  {spread:>7.1f}")
    h_meds = [
        statistics.median(len(human[i].split()) for i in ids if cats[i] == c)
        for c in cat_names
    ]
    print(f"{'human':8}{max(h_meds) / max(min(h_meds), 1):>8.1f}                        (one generation)")

    print("\n=== pooled McNemar: fable vs each sibling, all generations pooled ===")
    for other in ["haiku", "sonnet", "opus"]:
        b = c = 0
        for gf in runs["fable"]:
            for go in runs[other]:
                for i in ids:
                    f_s, o_s = scaffolded(gf[i]), scaffolded(go[i])
                    b += f_s and not o_s
                    c += o_s and not f_s
        print(
            f"  fable vs {other:7} discordant {b}/{c}  p={sign_test(b, b + c):.6f}"
            if b + c
            else f"  fable vs {other:7} no discordant pairs"
        )

    out = {
        "scaffolding_rates": scaf_rates,
        "human_scaffolding": h_scaf,
        "median_lengths": med_len,
        "human_median_length": h_med,
    }
    (FIXTURES.parents[1] / "runs" / "seeded-results.json").write_text(json.dumps(out, indent=1))
    print("\nwrote seeded-results.json")


if __name__ == "__main__":
    main()
