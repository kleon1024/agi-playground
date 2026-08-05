"""Where the decoder looks when the image matters: attention mass on the
vision prefix, split by question type.

The mission's recorded accuracy already shows the vision pathway separates
from text-only exactly where the question cannot leak (shape_color 50.1%
versus 27.2%). This script measures the mechanism behind that separation:
at the last fusion layer, how much of each text query's attention lands on
the 64 vision-prefix tokens, split by whether the question is
color-dependent (the leak-proof type) or not. A model that conditions on
pixels should spend measurably more attention on the vision prefix for
color questions; a model that answers from phrasing should not differ.

It retrains the vision pathway (seed 0, 30 epochs, CPU — the same recipe
the recorded run used) and reuses `forward_capturing_attention`, the
diagnostic-only method that never touches the training path.

Run:
    uv run --group torch python core/vision_attention_mass.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "core"))

from tokenizer import Tokenizer
from train import DATA_DIR, build_examples, load_jsonl, train_one
from vlm_model import Config


def main() -> None:
    device = torch.device("cpu")
    train_raw = load_jsonl(DATA_DIR / "train.jsonl")
    eval_raw = load_jsonl(DATA_DIR / "eval.jsonl")
    all_text = []
    for split in (train_raw, eval_raw):
        for ex in split:
            for qa in ex["qa"]:
                all_text.append(qa["question"])
                all_text.append(qa["answer"])
    tok = Tokenizer.build(all_text)
    train_ex = build_examples(train_raw, tok)
    eval_ex = build_examples(eval_raw, tok)
    cfg = Config(vocab_size=len(tok))

    print(f"retraining vision pathway, seed 0, {len(train_ex)} train examples")
    model, _ = train_one(cfg, True, train_ex, seed=0, device=device, epochs=30, batch_size=64)
    model.eval()
    nv = model.num_vision_tokens

    # Rebuild the eval order so each example keeps its question text.
    questions = [qa["question"] for ex in eval_raw for qa in ex["qa"]]
    assert len(questions) == len(eval_ex)

    color_mass: list[float] = []
    other_mass: list[float] = []
    with torch.no_grad():
        for e, question in zip(eval_ex, questions):
            ids = e["text_ids"]
            text_in = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
            valid_lens = torch.tensor([len(ids) - 1], device=device)
            pixels = e["pixels"].unsqueeze(0).to(device)
            weights = model.forward_capturing_attention(pixels, text_in, valid_lens, layer=3)
            weights = weights.mean(dim=0)  # average heads
            mass = float(weights[nv:, :nv].mean())
            (color_mass if "color" in question else other_mass).append(mass)

    def stats(name: str, values: list[float]) -> None:
        mean = sum(values) / len(values)
        spread = (max(values) - min(values)) / 2
        print(f"  {name:<14} n={len(values):>4}  mean vision mass={mean:.5f}  "
              f"half-range={spread:.5f}")

    print("\nmean attention mass on the 64 vision tokens, layer 3, by question type:")
    stats("color", color_mass)
    stats("other", other_mass)
    if color_mass and other_mass:
        ratio = (sum(color_mass) / len(color_mass)) / (sum(other_mass) / len(other_mass))
        print(f"  ratio color/other = {ratio:.2f}x")


if __name__ == "__main__":
    main()
