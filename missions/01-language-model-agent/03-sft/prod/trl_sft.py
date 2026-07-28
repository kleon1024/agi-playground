"""The production lane for stage 03: the same job via HuggingFace TRL.

`core/sft.py` hand-builds a chat template, an assistant-only loss mask, and a
bin-packing scheme, then reuses stage 02's hand-built training loop. TRL's
`SFTTrainer` collapses essentially that entire file into a handful of
`SFTConfig` fields. This script runs the same recipe — same dataset
(HuggingFaceH4/no_robots), same idea (loss on assistant turns only, packed
sequences, a low fine-tuning LR) — through it, so the comparison is apples to
apples.

One honest gap: TRL expects a `transformers.PreTrainedModel` and a tokenizer
with a registered chat template. Stage 02's checkpoint is a bespoke
`nn.Module` (`model.py`'s `Transformer`) paired with our own from-scratch BPE
— neither speaks the HuggingFace interface, and writing a `PreTrainedModel`
wrapper around a teaching model is its own project, not this stage's. So this
script fine-tunes a small public HF checkpoint close to stage 02's parameter
count instead, and says so here rather than pretending otherwise. If you want
to actually resume *our* checkpoint under TRL, the wrapper is the missing
piece — Chapter `05-serve`'s engine faces the same our-model-vs-HF-ecosystem
gap and is a better place to build that bridge once, for every later stage
that needs it.

What TRL does that `core/sft.py` does by hand:

- **Chat template + loss mask.** `core/sft.py`'s `render_and_mask` wraps turns
  in `<|im_start|>`/`<|im_end|>` and masks every non-assistant label by hand.
  TRL applies the tokenizer's own `chat_template` (a Jinja template)
  automatically, and `SFTConfig(assistant_only_loss=True)` computes the same
  assistant-only mask — provided the template emits the generation-boundary
  markers TRL looks for (TRL patches known model families' templates when it
  can).
- **Packing.** `core/sft.py`'s `pack()` greedily bin-packs fixed blocks, with
  a disclosed cross-example attention leak, because the frozen `model.py`
  can't take a custom mask. `SFTConfig(packing=True)` does the same bin-packing
  *and* builds a position-id/attention-mask scheme that keeps packed examples
  from attending to each other — the leak our version can't close.
- **The training loop.** `build_optimizer` plus the hand-rolled loop (grad
  accum, bf16 autocast, cosine `lr_at`, gradient clipping) becomes
  `SFTConfig(per_device_train_batch_size=..., gradient_accumulation_steps=...,
  bf16=True, lr_scheduler_type="cosine", max_grad_norm=...)` — all handled by
  the wrapped `transformers.Trainer`.
- **Checkpointing.** `save_checkpoint`/`--resume` (imported from stage 02's
  `train.py`) becomes `Trainer`'s own `output_dir` checkpointing and
  `resume_from_checkpoint=True`.
- **Scale.** `core/sft.py` is single-process only. `Trainer` is
  Accelerate-backed: the same script scales to multi-GPU under
  `accelerate launch`, no code change.
- **Evaluation.** `evaluate()` on packed val blocks becomes
  `SFTConfig(eval_strategy="steps", eval_steps=...)` against `eval_dataset`.
- **MFU.** Printed every eval step in `core/sft.py`. Not built the same way
  here — `Trainer`'s logs give loss and a tokens-per-second-ish metric, not
  the FLOPs-vs-peak ratio `train.py` computes. Wanting MFU under TRL still
  means computing it yourself from the logged throughput.
- **LoRA.** Not part of either script today, but the natural next step:
  `peft_config=LoraConfig(...)` turns this exact call site into stage
  `02-lora-and-peft`'s job — full-parameter and LoRA share one TRL entry
  point, which is not true of a from-scratch implementation.

Run:  python trl_sft.py --model HuggingFaceTB/SmolLM2-135M --out ckpt-trl
"""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

# HuggingFaceTB/SmolLM2-135M (the base checkpoint this script defaults to) has
# no chat_template at all — it was only ever pretrained on documents, same as
# our stage 02. Its own -Instruct sibling ships one, but a *native* template
# still won't help `assistant_only_loss`: TRL locates assistant spans via
# `{% generation %}...{% endgeneration %}` tags, and "most native model
# templates lack these markers" (TRL's own chat-templates doc). TRL ships
# pre-patched templates for a handful of families (Qwen, Llama, DeepSeek-V3,
# GPT-OSS); SmolLM2 isn't one of them as of this writing, so rather than guess
# at library coverage this script carries its own minimal, verified-shape
# ChatML template — the same <|im_start|>/<|im_end|> convention core/sft.py
# hand-renders, with the generation tags TRL requires added around the
# assistant branch only.
CHATML_WITH_GENERATION_TAGS = (
    "{%- for message in messages -%}"
    "{%- if message['role'] == 'assistant' -%}"
    "<|im_start|>{{ message['role'] }}\n"
    "{% generation %}{{ message['content'] }}<|im_end|>\n{% endgeneration %}"
    "{%- else -%}"
    "<|im_start|>{{ message['role'] }}\n{{ message['content'] }}<|im_end|>\n"
    "{%- endif -%}"
    "{%- endfor -%}"
    "{%- if add_generation_prompt -%}"
    "<|im_start|>assistant\n"
    "{%- endif -%}"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model",
        default="HuggingFaceTB/SmolLM2-135M",
        help="stand-in HF base model close to stage 02's parameter count "
        "(see module docstring for why this isn't our own checkpoint)",
    )
    ap.add_argument("--dataset", default="HuggingFaceH4/no_robots")
    ap.add_argument("--train-split", default="train")
    ap.add_argument("--eval-split", default="test")
    ap.add_argument("--out", type=Path, default=Path("ckpt-trl"))
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-5, help="matches core/sft.py's default")
    ap.add_argument("--max-length", type=int, default=1024, help="matches stage 02's block_size")
    ap.add_argument("--eval-steps", type=int, default=50)
    ap.add_argument("--no-packing", action="store_true", help="disable packing for comparison")
    ap.add_argument(
        "--force-chatml-template",
        action="store_true",
        help="use this script's own generation-tagged ChatML template even if --model "
        "ships its own (its native template likely lacks the tags assistant_only_loss needs)",
    )
    args = ap.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.chat_template is None or args.force_chatml_template:
        # See CHATML_WITH_GENERATION_TAGS above for why this isn't simply left
        # to whatever the checkpoint ships (usually nothing, on a base model).
        tokenizer.chat_template = CHATML_WITH_GENERATION_TAGS
    model = AutoModelForCausalLM.from_pretrained(args.model)

    train_dataset = load_dataset(args.dataset, split=args.train_split)
    eval_dataset = load_dataset(args.dataset, split=args.eval_split)

    config = SFTConfig(
        output_dir=str(args.out),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_steps=30,
        max_grad_norm=1.0,
        bf16=True,
        max_length=args.max_length,
        packing=not args.no_packing,
        assistant_only_loss=True,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        logging_steps=10,
        save_strategy="steps",
        save_steps=200,
    )

    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(args.out))
    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
