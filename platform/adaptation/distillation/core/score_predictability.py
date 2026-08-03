"""Predictability under a fixed base scorer, across three generations per arm.

The single-generation pass found no significant difference between any model
arm and the human arm on this axis. Three generations per arm turn that from
"no difference detected in one draw" into a spread the margins can be checked
against, the same way the length and scaffolding statistics are checked.

The scorer is a base model, not an instruct model, so it is not aligned to
any arm's chat style, and it is identical across every arm and generation.
Lower mean NLL means more predictable, not better.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "four-authors"
MODEL_ARMS = ["haiku", "sonnet", "opus", "fable"]
GENS = ["", "-g2", "-g3"]
SCORER = "Qwen/Qwen2.5-0.5B"


@torch.no_grad()
def nll(model, tok, text: str, device: str) -> float | None:
    ids = tok(text, return_tensors="pt", truncation=True, max_length=1024).input_ids.to(device)
    if ids.shape[1] < 2:
        return None
    return float(model(ids, labels=ids).loss)


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(SCORER)
    model = AutoModelForCausalLM.from_pretrained(
        SCORER, dtype=torch.bfloat16 if device == "cuda" else torch.float32
    ).to(device)
    model.eval()

    prompts = json.loads((FIXTURES / "prompts.json").read_text())
    ids = [p["id"] for p in prompts]
    human = {p["id"]: p["human"] for p in prompts}

    print(f"scorer: {SCORER}  device: {device}\n")

    h_vals = [v for i in ids if (v := nll(model, tok, human[i], device)) is not None]
    print(f"{'arm':8} {'g1':>8} {'g2':>8} {'g3':>8}   {'mean':>8} {'spread':>7}")
    print(f"{'human':8} {statistics.mean(h_vals):>8.4f} {'':>8} {'':>8}   "
          f"{statistics.mean(h_vals):>8.4f} {'--':>7}  (one generation)")

    per_arm: dict[str, list[float]] = {}
    for arm in MODEL_ARMS:
        gen_means = []
        for suffix in GENS:
            path = FIXTURES / f"answers-{arm}{suffix}.jsonl"
            if not path.exists():
                continue
            rows = {json.loads(x)["id"]: json.loads(x)["answer"]
                    for x in path.read_text().splitlines() if x.strip()}
            vals = [v for i in ids if (v := nll(model, tok, rows[i], device)) is not None]
            gen_means.append(statistics.mean(vals))
        per_arm[arm] = gen_means
        cells = "".join(f"{m:>9.4f}" for m in gen_means)
        spread = max(gen_means) - min(gen_means)
        print(f"{arm:8}{cells}   {statistics.mean(gen_means):>8.4f} {spread:>7.4f}")

    print("\n=== does any predictability gap clear run-to-run spread? ===")
    h_mean = statistics.mean(h_vals)
    for arm in MODEL_ARMS:
        margin = abs(statistics.mean(per_arm[arm]) - h_mean)
        spread = max(per_arm[arm]) - min(per_arm[arm])
        v = "CLEARS" if margin > spread else "does not clear"
        print(f"  {arm:7} vs human   margin {margin:>7.4f}  spread {spread:>7.4f}  -> {v}")
    for a in MODEL_ARMS:
        for b in MODEL_ARMS:
            if a >= b:
                continue
            margin = abs(statistics.mean(per_arm[a]) - statistics.mean(per_arm[b]))
            spread = max(max(per_arm[a]) - min(per_arm[a]), max(per_arm[b]) - min(per_arm[b]))
            v = "CLEARS" if margin > spread else "does not clear"
            print(f"  {a:7} vs {b:7} margin {margin:>7.4f}  spread {spread:>7.4f}  -> {v}")

    (Path(__file__).resolve().parents[1] / "runs" / "ppl-seeded.json").write_text(
        json.dumps({"human": h_mean, "arms": per_arm}, indent=1)
    )
    print("\nwrote ppl-seeded.json")


if __name__ == "__main__":
    main()
