"""Retrain seed 0 (matching the reported run) and print a few real
eval predictions from both models side by side, for the README's artifact
example. Not part of the reported metrics -- those come from train.py's own
run; this only needs one illustrative, real, reproducible instance.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import torch
from tokenizer import Tokenizer
from train import DATA_DIR, build_examples, generate_answer, load_jsonl, train_one
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

    vision_model, _ = train_one(cfg, True, train_ex, seed=0, device=device, epochs=30, batch_size=64)
    text_model, _ = train_one(cfg, False, train_ex, seed=0, device=device, epochs=30, batch_size=64)

    print("id,question,ground_truth,vision_pred,text_only_pred")
    for i, e in enumerate(eval_ex[:12]):
        answer_start = e["answer_start"]
        q_ids = e["text_ids"][: answer_start - 1]
        gt = tok.decode(e["text_ids"][answer_start:-1])
        vpred = generate_answer(vision_model, tok, e["pixels"], q_ids)
        tpred = generate_answer(text_model, tok, e["pixels"], q_ids)
        question_text = tok.decode(q_ids)
        print(f"{i}|{question_text}|{gt}|{vpred}|{tpred}")


if __name__ == "__main__":
    main()
