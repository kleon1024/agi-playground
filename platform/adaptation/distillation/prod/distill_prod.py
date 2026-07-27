"""The production lane for this chapter: the same on-the-fly job via TRL.

`core/distill.py` hand-builds the top-k extraction, the temperature-scaled
soft cross-entropy, and the training loop, against a stand-in teacher this
repo has not trained. TRL's `DistillationTrainer` collapses that into a
handful of `DistillationConfig` fields and runs it against real, same-
tokenizer public checkpoints:

- **Top-k extraction.** `core/distill.py`'s `topk_teacher_targets` keeps the
  teacher's k highest log-probabilities by hand. `DistillationConfig`'s
  `loss_top_k` does the same restriction internally — set here to 16 to match
  the chapter's worked byte arithmetic (section 3).
- **Temperature-scaled soft cross-entropy.** `core/distill.py`'s
  `topk_soft_ce_loss` divides both distributions' logits by `temperature`
  before comparing and rescales the loss by `temperature ** 2` by hand.
  `DistillationConfig(temperature=...)` applies the same softening; the T^2
  gradient correction is internal to the trainer's loss, not a call-site
  concern.
- **Whose trajectory is scored.** `lmbda=0.0` below trains against the fixed
  dataset's own assistant turns — supervised, off-policy, the same shape
  `core/distill.py`'s synthetic token batches take. Raising `lmbda` toward
  1.0 switches to on-policy: the student generates, and only then does the
  teacher score what the student actually produced. That axis is the one
  [post-training's distillation section](../../post-training/README.md#6-use-distillation-when-the-teacher-supplies-a-richer-target)
  already covers; this script fixes it at 0 so the comparison to `core/`
  stays apples to apples.
- **The teacher forward pass stays live either way.** Whether `lmbda` is 0 or
  1, `DistillationTrainer` calls the teacher model during every training
  step to score whatever tokens are on the table that step. Nothing about
  the teacher's distribution is precomputed or cached to disk — this is
  section 5's on-the-fly path, not section 3's stored-shard path.
- **`beta`** interpolates the divergence direction: 0.0 is forward KL (what
  `core/distill.py`'s soft cross-entropy approximates), 1.0 is reverse KL.
  Set to 0.0 here for the same reason as `lmbda`.

One honest gap, the same one `../../../missions/01-language-model-agent/03-sft/prod/trl_sft.py`
already discloses: `DistillationTrainer` expects a `transformers.PreTrainedModel`
pair sharing one tokenizer. This repo's `model.py` is a bespoke `nn.Module`
with our own from-scratch BPE, so distilling *our* checkpoint under TRL would
need the same HF-interface wrapper that stage's docstring describes as
missing, not a gap this script closes. Two small SmolLM2 checkpoints stand in
instead — they share one tokenizer across sizes, which is exactly the
constraint the chapter's tokenizer-coupling section requires and this repo's
own tokenizer, trained only for stage 02's model, cannot satisfy against a
different-sized version of itself that does not exist.

Run:  python distill_prod.py \\
          --teacher HuggingFaceTB/SmolLM2-360M --student HuggingFaceTB/SmolLM2-135M \\
          --out ckpt-distill
"""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
from trl.experimental.distillation import DistillationConfig, DistillationTrainer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--teacher",
        default="HuggingFaceTB/SmolLM2-360M",
        help="larger checkpoint sharing the student's tokenizer (see module docstring)",
    )
    ap.add_argument(
        "--student",
        default="HuggingFaceTB/SmolLM2-135M",
        help="same tokenizer family, close to stage 02's parameter count",
    )
    ap.add_argument("--dataset", default="HuggingFaceH4/no_robots", help="same set stage 03 uses")
    ap.add_argument("--train-split", default="train_sft")
    ap.add_argument("--out", type=Path, default=Path("ckpt-distill"))
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-5, help="matches stage 03's fine-tuning LR")
    ap.add_argument("--temperature", type=float, default=1.0, help="matches the chapter's default")
    ap.add_argument("--top-k", type=int, default=16, help="matches the chapter's worked example")
    ap.add_argument(
        "--lmbda", type=float, default=0.0,
        help="0.0: off-policy on the dataset's own assistant turns (default, matches core/); "
        "1.0: fully on-policy, the student generates and the teacher scores it",
    )
    ap.add_argument("--beta", type=float, default=0.0, help="0.0: forward KL, matching core/'s loss")
    args = ap.parse_args()

    train_dataset = load_dataset(args.dataset, split=args.train_split)

    config = DistillationConfig(
        output_dir=str(args.out),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        learning_rate=args.lr,
        lmbda=args.lmbda,
        beta=args.beta,
        temperature=args.temperature,
        loss_top_k=args.top_k,
        bf16=True,
        logging_steps=10,
        save_strategy="no",
    )

    trainer = DistillationTrainer(
        model=args.student,
        teacher_model=args.teacher,
        args=config,
        train_dataset=train_dataset,
    )
    trainer.train()
    trainer.save_model(str(args.out))
    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
