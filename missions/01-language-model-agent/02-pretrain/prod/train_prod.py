"""The production lane for stage 02: the same pretraining job through HF `Trainer`.

`core/model.py`'s four architectural choices — RMSNorm, RoPE, SwiGLU, GQA —
are not a teaching simplification of something else; they are Llama's
architecture, described from scratch. So this script does not reach for a
different model family as a stand-in the way stage 03's `trl_sft.py` and the
distillation chapter's `prod/` do: `transformers.LlamaConfig` /
`LlamaForCausalLM` already implement exactly this architecture, and mapping
`core/model.py`'s `Config` onto `LlamaConfig` field-for-field produces a model
with the identical parameter count, checked by actually instantiating both:

    core/model.py's Transformer(Config()):            88,197,888 params
    LlamaForCausalLM(LlamaConfig(<mapped fields>)):    88,197,888 params

Same architecture, same size. What differs is the training engineering
`core/train.py` hand-builds, which is the entire point of comparing them:

- **Gradient accumulation.** `core/train.py` divides each micro-batch's loss
  by the accumulation count and calls `.backward()` that many times before
  stepping. `TrainingArguments(gradient_accumulation_steps=...)` does the same
  averaging internally — the framework does this *for* you, not differently.

- **Warmup then decay.** `core/train.py`'s `lr_at` warms up linearly, then
  decays on a cosine curve to a **floor** (`floor_ratio`, default 10% of
  peak) rather than to zero. `TrainingArguments(lr_scheduler_type="cosine")`
  warms up the same way, but its default cosine schedule decays fully to
  zero by the end of training — there is no floor unless you reach for a
  differently-named scheduler variant and its own kwargs. This is a real
  behavioral difference, not a naming one: the two curves cross zero at
  different places, and it is worth confirming in your installed
  `transformers` version's docs rather than assuming `"cosine"` alone
  reproduces `core/train.py`'s curve.

- **Gradient clipping.** `core/train.py` calls
  `torch.nn.utils.clip_grad_norm_(model.parameters(), clip)` once per step,
  after the accumulated backward passes. `TrainingArguments(max_grad_norm=...)`
  does the same clip at the same point in the loop — for you, not differently.

- **Weight decay on matrices only.** `core/train.py` explicitly splits
  parameters by `dim() >= 2` so RMSNorm gains are never decayed.
  `TrainingArguments(weight_decay=...)`'s own field documentation states
  weight decay is "automatically excluded from bias and LayerNorm
  parameters" — for `LlamaForCausalLM` specifically, whose norm layers are a
  class `Trainer` already recognizes, this lands on the same split `core/`
  builds by hand. That auto-detection is keyed on the model's own module
  types, so it is worth re-checking for any architecture `Trainer` does not
  already recognize as a norm layer.

- **Checkpointing and resume.** `core/train.py`'s `save_checkpoint` writes
  model weights, optimizer state, and the training step. `Trainer`'s
  `save_strategy`/`resume_from_checkpoint` save at least that much per
  checkpoint directory, plus the RNG state `core/train.py` does not persist —
  a resume under `Trainer` restores a few bits of state ours quietly drops.

- **MFU.** Not reported by `Trainer` at all. Its logs give loss, learning
  rate, and a samples/tokens-per-second figure — not the FLOPs-vs-peak ratio
  `core/train.py` computes. Wanting MFU here still means computing it
  yourself from the logged throughput, exactly the gap stage 03's
  `trl_sft.py` already notes for TRL.

- **Data.** Both scripts read the identical `data/tokens/{train,val}.bin`
  files `core/prepare_data.py` writes — `MemmapWindows` below adapts that
  same random-window-with-replacement sampling to the one-example-at-a-time
  protocol `Trainer`'s dataloader expects. See its docstring for the one
  small difference: `Trainer`'s causal-LM loss shifts `labels` internally,
  so an identical `input_ids`/`labels` pair trains on one fewer position per
  window than `core/train.py`'s explicit `x`/`y` split does.

Run:  python train_prod.py --data ../core/data/tokens --out ckpt-hf
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from transformers import LlamaConfig, LlamaForCausalLM, Trainer, TrainingArguments


class MemmapWindows(torch.utils.data.Dataset):
    """Random fixed-length windows over a token binary, sampled with
    replacement — the same policy `core/train.py`'s `get_batch` uses, so a
    document's tokens land at many different context offsets over training
    rather than always the same one.

    `Trainer` wants one example per `__getitem__` call rather than a whole
    batch, and expects a nominal `__len__` to define "one epoch" even though
    sampling here never actually exhausts the data — `length` is a size
    Trainer paces logging and epoch counters against, not a hard limit.

    `input_ids` and `labels` are the *same* window. `LlamaForCausalLM`
    shifts internally (`logits[:, :-1]` against `labels[:, 1:]`), so a
    `block_size`-token window yields `block_size - 1` trained predictions.
    `core/train.py` instead reads `block_size + 1` raw tokens and builds `x`
    and `y` as two overlapping length-`block_size` slices, so every one of
    `block_size` positions gets a target. The one-fewer-position-per-window
    gap here is the price of passing `labels` the idiomatic HF way (the same
    convention `transformers`' own `run_clm.py` example uses) instead of
    re-deriving `core/train.py`'s exact window construction.
    """

    def __init__(self, path: Path, block_size: int, length: int):
        self.data = np.memmap(path, dtype=np.uint16, mode="r")
        self.block_size = block_size
        self.length = length

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, _idx: int) -> dict[str, torch.Tensor]:
        i = np.random.randint(0, len(self.data) - self.block_size)
        ids = torch.from_numpy(self.data[i : i + self.block_size].astype(np.int64))
        return {"input_ids": ids, "labels": ids.clone()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data/tokens"),
                    help="same directory core/prepare_data.py writes train.bin/val.bin into")
    ap.add_argument("--out", type=Path, default=Path("ckpt-hf"))
    ap.add_argument("--tokens", type=float, default=3.0e9, help="matches core/train.py's budget")
    ap.add_argument("--block-size", type=int, default=1024, help="matches core/model.py's Config")
    ap.add_argument("--batch", type=int, default=16, help="micro-batch size")
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--warmup-steps", type=int, default=500)
    ap.add_argument("--weight-decay", type=float, default=0.1)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--eval-steps", type=int, default=500)
    ap.add_argument("--checkpoint-steps", type=int, default=2000)
    ap.add_argument("--resume-from-checkpoint", type=str, default=None)
    args = ap.parse_args()

    # Field-for-field from core/model.py's Config -- see the module docstring
    # for the parameter count this reproduces exactly.
    hf_cfg = LlamaConfig(
        vocab_size=16512,
        hidden_size=768,
        intermediate_size=2048,
        num_hidden_layers=12,
        num_attention_heads=12,
        num_key_value_heads=4,
        max_position_embeddings=args.block_size,
        rope_theta=10_000.0,
        tie_word_embeddings=True,
    )
    model = LlamaForCausalLM(hf_cfg)
    model.config.use_cache = False  # training only; no generation cache to keep coherent
    print(f"model params: {sum(p.numel() for p in model.parameters()):,}")

    tokens_per_step = args.batch * args.block_size * args.grad_accum
    total_steps = int(args.tokens / tokens_per_step)

    train_dataset = MemmapWindows(
        args.data / "train.bin", args.block_size,
        length=args.batch * args.grad_accum * total_steps,
    )
    eval_dataset = MemmapWindows(
        args.data / "val.bin", args.block_size,
        length=args.batch * 50,  # a handful of eval batches per evaluation, not a full pass
    )

    training_args = TrainingArguments(
        output_dir=str(args.out),
        max_steps=total_steps,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",  # see module docstring: decays to 0, not core/'s floor
        warmup_steps=args.warmup_steps,
        weight_decay=args.weight_decay,
        max_grad_norm=args.clip,
        bf16=True,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        logging_steps=10,
        save_strategy="steps",
        save_steps=args.checkpoint_steps,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )
    trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    trainer.save_model(str(args.out))
    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
