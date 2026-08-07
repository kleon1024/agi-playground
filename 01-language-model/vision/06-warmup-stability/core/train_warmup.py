"""Does a linear LR warmup close stage 01's seed-2 vision-fusion collapse?

Stage 01's report measured vision-pathway eval exact-match across 3 seeds:
[0.5128, 0.5153, 0.2844]. Two seeds decisively beat every text-only seed;
the third collapsed below all of them. Stage 01's own diagnosis: that seed's
final train loss (0.6853) sat close to text-only's losses while the other
two vision seeds reached 0.53/0.49, suggesting the collapsed seed's vision
pathway got stuck in a poorly-fit region under the fixed, un-scheduled,
lr=3e-3 AdamW setup used for all six of stage 01's runs -- and stage 01's
own "what this does not establish" section named a warmup or schedule as
untested future work.

This script changes exactly one mechanism relative to stage 01's train.py:
a linear LR warmup over the first `warmup_frac` of total optimizer steps
(0 -> base_lr), then held constant at base_lr for the remainder -- the
standard, simplest fix, and the one stage 01's own diagnosis points at.
Model class (`VisionLanguageTransformer`), `Config`, `Tokenizer`, dataset,
epochs, batch size, base learning rate, optimizer (AdamW), and all 3 seeds
(0, 1, 2) are imported or reused unchanged from stage 01's core/ -- only the
vision pathway is retrained here; text-only is not re-run since the
collapse and the hypothesis under test are specific to vision.

Run:
    uv run --group torch python train_warmup.py --seeds 3 --epochs 30 --batch-size 64
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import torch

STAGE01_CORE = Path(__file__).resolve().parents[2] / "01-vision-fusion" / "core"
sys.path.insert(0, str(STAGE01_CORE))
from tokenizer import Tokenizer
from train import build_examples, evaluate, load_jsonl, make_batch
from vlm_model import Config, VisionLanguageTransformer

DATA_DIR = STAGE01_CORE.parents[1] / "00-image-caption-task" / "data" / "raw"

BASE_LR = 3e-3  # unchanged from stage 01
WARMUP_FRAC = 0.10  # first 10% of optimizer steps ramp 0 -> BASE_LR


def train_one_warmup(
    cfg: Config, train_ex: list[dict], seed: int, device, epochs: int, batch_size: int
) -> tuple[VisionLanguageTransformer, float, int, int]:
    torch.manual_seed(seed)
    rng = random.Random(seed)
    model = VisionLanguageTransformer(cfg, use_vision=True).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=BASE_LR)
    max_input_len = max(len(e["text_ids"]) - 1 for e in train_ex)
    order = list(range(len(train_ex)))

    steps_per_epoch = (len(order) + batch_size - 1) // batch_size
    total_steps = steps_per_epoch * epochs
    warmup_steps = max(1, int(WARMUP_FRAC * total_steps))

    last_loss = 0.0
    step = 0
    for _ in range(epochs):
        rng.shuffle(order)
        for start in range(0, len(order), batch_size):
            lr = BASE_LR * min(1.0, (step + 1) / warmup_steps)
            for g in opt.param_groups:
                g["lr"] = lr
            idxs = order[start : start + batch_size]
            batch_examples = [train_ex[i] for i in idxs]
            batch = make_batch(batch_examples, max_input_len, device)
            model.train()
            _, loss = model(batch["pixels"], batch["text_in"], batch["valid_lens"], batch["targets"])
            opt.zero_grad()
            loss.backward()
            opt.step()
            last_loss = loss.item()
            step += 1
    return model, last_loss, total_steps, warmup_steps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--out", type=Path, default=Path("../runs"))
    args = ap.parse_args()

    device = torch.device("cpu")
    train_raw = load_jsonl(DATA_DIR / "train.jsonl")
    eval_raw = load_jsonl(DATA_DIR / "eval.jsonl")

    # Rebuild the tokenizer exactly as stage 01 does (same vocab source: all
    # train+eval question/answer text), so token ids match stage 01's run.
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
    print(f"vocab size: {len(tok)}  words: {tok.vocab}")
    print(f"train qa pairs: {len(train_ex)}  eval qa pairs: {len(eval_ex)}")

    accs: list[float] = []
    losses: list[float] = []
    t0 = time.perf_counter()
    n_params = None
    total_steps = warmup_steps = None
    for seed in range(args.seeds):
        model, last_loss, total_steps, warmup_steps = train_one_warmup(
            cfg, train_ex, seed, device, args.epochs, args.batch_size
        )
        if n_params is None:
            n_params = sum(p.numel() for p in model.parameters())
        acc = evaluate(model, tok, eval_ex, device)
        accs.append(acc)
        losses.append(last_loss)
        print(f"[vision+warmup] seed={seed} final_train_loss={last_loss:.4f} eval_exact_match={acc:.4f}")
    elapsed = time.perf_counter() - t0

    def summarize(xs: list[float]) -> dict:
        mean = sum(xs) / len(xs)
        spread = max(xs) - min(xs)
        return {"mean": round(mean, 4), "spread": round(spread, 4), "per_seed": [round(x, 4) for x in xs]}

    print("\n=== SUMMARY ===")
    print(f"wall-clock: {elapsed:.1f}s  device: {device}")
    print(f"vision+warmup eval exact-match: {summarize(accs)}")
    print(f"vision+warmup final train loss: {summarize(losses)}")

    args.out.mkdir(parents=True, exist_ok=True)
    result = {
        "stage": "06-warmup-stability",
        "base_lr": BASE_LR,
        "warmup_frac": WARMUP_FRAC,
        "total_steps": total_steps,
        "warmup_steps": warmup_steps,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "n_params": n_params,
        "eval_exact_match": summarize(accs),
        "final_train_loss": summarize(losses),
        "wall_clock_s": elapsed,
        "stage01_baseline_eval_exact_match": {
            "mean": 0.4375,
            "spread": 0.2309,
            "per_seed": [0.5128, 0.5153, 0.2844],
        },
        "stage01_baseline_final_train_loss": {
            "mean": 0.5689,
            "spread": 0.1957,
            "per_seed": [0.5317, 0.4896, 0.6853],
        },
    }
    (args.out / "warmup-results.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
