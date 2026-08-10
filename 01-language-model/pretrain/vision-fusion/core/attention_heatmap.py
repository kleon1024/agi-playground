"""Real attention-weight heatmap for the README: retrains the vision pathway
(seed 0, matching `runs/2026-07-31-vision-vs-text-only.md` and
`dump_examples.py`'s reproducible-example convention) and renders one
held-out example's actual post-softmax weights from text tokens to vision
patches.

`FusedAttention.forward` -- the training path -- calls
`F.scaled_dot_product_attention`, which never exposes attention weights. This
script instead calls `VisionLanguageTransformer.forward_capturing_attention`,
a diagnostic-only method added in `vlm_model.py` that recomputes exactly one
block's attention with an explicit `q @ k.T / sqrt(d_head)` + softmax. It is
never called from `train.py` and does not change the training path.

Run:
    python3 attention_heatmap.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from tokenizer import Tokenizer
from train import DATA_DIR, build_examples, load_jsonl, train_one
from vlm_model import PATCHES_PER_SIDE, Config

OUT_DIR = HERE.parent / "runs"
LAYER = 3  # last of the 4 blocks -- where fused vision/text mixing is most settled
EXAMPLE_INDEX = 11  # flat eval_ex index: "how many shapes are in the image ?" / ground truth "1"


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

    model, _ = train_one(cfg, True, train_ex, seed=0, device=device, epochs=30, batch_size=64)
    model.eval()

    e = eval_ex[EXAMPLE_INDEX]
    ids = e["text_ids"]
    text_in = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
    valid_lens = torch.tensor([len(ids) - 1], device=device)
    pixels = e["pixels"].unsqueeze(0).to(device)

    with torch.no_grad():
        weights = model.forward_capturing_attention(pixels, text_in, valid_lens, layer=LAYER)
    # weights: (n_head, T, T); average across heads for one readable matrix.
    weights = weights.mean(dim=0)
    nv = model.num_vision_tokens
    text_to_vision = weights[nv:, :nv].numpy()  # (text_len, 64)

    token_strs = [tok.vocab[i] for i in ids[:-1]]
    question_text = tok.decode(ids[: e["answer_start"] - 1])
    ground_truth = tok.decode(ids[e["answer_start"] : -1])
    print(f"question: {question_text}")
    print(f"ground truth: {ground_truth}")
    print(f"attention matrix shape (text tokens x vision patches): {text_to_vision.shape}")
    print(f"min={text_to_vision.min():.5f} max={text_to_vision.max():.5f} mean={text_to_vision.mean():.5f}")

    fig, ax = plt.subplots(figsize=(7.5, 0.35 * len(token_strs) + 1.5))
    im = ax.imshow(text_to_vision, aspect="auto", cmap="viridis")
    ax.set_yticks(range(len(token_strs)))
    ax.set_yticklabels(token_strs, fontsize=8)
    ax.set_xlabel(f"vision patch index (row-major {PATCHES_PER_SIDE}x{PATCHES_PER_SIDE} grid)")
    ax.set_title(
        f"Layer {LAYER} attention: text tokens -> vision patches\n"
        f'"{question_text}" -- ground truth "{ground_truth}"',
        fontsize=9,
    )
    for col in range(PATCHES_PER_SIDE, text_to_vision.shape[1], PATCHES_PER_SIDE):
        ax.axvline(col - 0.5, color="white", linewidth=0.4, alpha=0.5)
    fig.colorbar(im, ax=ax, label="attention weight")
    fig.tight_layout()

    out_path = OUT_DIR / "attention-heatmap-vqa-100007.png"
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
