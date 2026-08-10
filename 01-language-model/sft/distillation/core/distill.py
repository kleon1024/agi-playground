"""Top-k logit distillation, with the teacher's forward pass run live.

[The chapter](../README.md) draws the line between sequence-level
distillation (train on a teacher's text) and logit-level distillation (train
on a teacher's distribution). This file is the second kind, done the
on-the-fly way section 5 describes: the teacher's forward pass runs inside
this student's training step, so nothing is written to disk before training
starts and there is no dataset snapshot to go stale.

Three pieces carry the whole mechanism:

1. **Top-k extraction.** Storing or comparing the full ~16k-wide distribution
   is unnecessary -- keep the teacher's k highest log-probabilities and which
   vocabulary ids they belong to (`topk_teacher_targets`). These are the same
   `topk_ids` / `topk_logprobs` the chapter's storage arithmetic prices; here
   they exist only for the duration of one training step, never on disk.

2. **Temperature-scaled soft cross-entropy.** The student is trained to put
   its own probability where the teacher put its top-k probability, both
   softened by temperature and the loss rescaled by T^2
   (`topk_soft_ce_loss`) -- see the chapter's section 2 for why T^2, not T,
   is the correction.

3. **A byte-exact storage check.** `demo_storage_shard` writes one example
   shard in the chapter's section-3 format and asserts its size against the
   stated 4k-bytes-per-token formula, so that arithmetic is not just prose.

Teacher and student share one architecture family and one 16,512-token
vocabulary -- see the chapter's tokenizer-coupling section for why that
sharing is not optional. The teacher here is a larger, untrained instance of
the same `Transformer`: no pretrained checkpoint exists in this repository
yet (this chapter is `status: draft`), so its logits carry no distilled
knowledge. Running this file exercises the mechanism -- shapes, gradients,
temperature scaling, the storage arithmetic -- not a quality claim.

Run:  python distill.py train --steps 20
      python distill.py storage-check --k 16 --tokens 4096
"""

from __future__ import annotations

import argparse
import array
import struct
import sys
from dataclasses import replace
from pathlib import Path

import torch
from torch.nn import functional as F

# The student's architecture is not re-derived here -- it is imported from the
# mission stage that owns it, the same way stage 03's SFT script reuses stage
# 02's model instead of keeping a second copy.
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[4]
        / "01-language-model" / "02-pretrain" / "core"
    ),
)
from model import Config, Transformer


def teacher_config(student: Config) -> Config:
    """A larger instance of the same architecture family, standing in for a
    teacher this repo has not trained. Same vocabulary size (the same
    tokenizer, per the chapter's section 4), more layers and width -- the one
    difference the tokenizer-coupling constraint permits."""
    return replace(
        student,
        n_layer=student.n_layer * 2,
        d_model=student.d_model * 2,
        n_head=student.n_head * 2,
        n_kv_head=student.n_kv_head * 2,
        d_ff=student.d_ff * 2,
    )


@torch.no_grad()
def topk_teacher_targets(
    teacher: Transformer, idx: torch.Tensor, k: int, temperature: float
) -> tuple[torch.Tensor, torch.Tensor]:
    """One live teacher forward pass, reduced to its top-k log-probabilities.

    Returns `(topk_ids, topk_logprobs)`, each shaped `(B, T, k)` -- exactly
    the two arrays the chapter's storage section prices, held only in memory
    here. `teacher` runs under `no_grad`: nothing about the teacher is
    trained during distillation, its distribution is the target.
    """
    teacher.eval()
    logits, _ = teacher(idx)
    logprobs = F.log_softmax(logits / temperature, dim=-1)
    topk_logprobs, topk_ids = logprobs.topk(k, dim=-1)
    return topk_ids, topk_logprobs


def topk_soft_ce_loss(
    student_logits: torch.Tensor,
    topk_ids: torch.Tensor,
    topk_teacher_logprobs: torch.Tensor,
    temperature: float,
) -> torch.Tensor:
    """Soft cross-entropy against the teacher's top-k distribution only.

    The teacher's kept probabilities are renormalized to sum to 1 over just
    the k entries (`teacher_p`) -- the tail outside the top-k is dropped,
    the approximation every top-k distillation recipe makes in exchange for
    never touching the full vocabulary. The student's log-probability is
    gathered at the *same* ids: they line up 1:1 only because teacher and
    student share one tokenizer (chapter section 4) -- this line would be
    comparing two unrelated strings otherwise. Scaling by `temperature ** 2`
    is the correction the chapter's section 2 derives for keeping gradient
    magnitude comparable as temperature changes.
    """
    teacher_p = topk_teacher_logprobs.exp()
    teacher_p = teacher_p / teacher_p.sum(dim=-1, keepdim=True)

    student_logprobs = F.log_softmax(student_logits / temperature, dim=-1)
    student_topk_logprobs = student_logprobs.gather(-1, topk_ids)

    per_token = -(teacher_p * student_topk_logprobs).sum(dim=-1)
    return (temperature**2) * per_token.mean()


def demo_storage_shard(out_path: Path, num_tokens: int, k: int) -> int:
    """Write one example top-k shard and confirm the chapter's byte formula.

    `input_ids` is not written here -- every fine-tuning run already stores
    it, so the chapter counts it as a sunk cost, not part of distillation's
    price. What is written, and what this function checks, is exactly the
    `4 * k` extra bytes per token the chapter's section 3 derives: 2 bytes
    per kept id (`array`'s `"H"` code, an unsigned short) and 2 bytes per
    kept log-probability (`struct`'s `"e"` code, IEEE half-precision float --
    a stand-in for bfloat16 here since both are 2 bytes wide, which is the
    only property this check depends on).
    """
    n = num_tokens * k
    ids = array.array("H", [i % 16512 for i in range(n)])
    logprobs = struct.pack(f"<{n}e", *(-0.01 * (i % (k + 1)) for i in range(n)))

    with open(out_path, "wb") as f:
        f.write(ids.tobytes())
        f.write(logprobs)

    actual = out_path.stat().st_size
    expected = num_tokens * 4 * k
    assert actual == expected, f"{actual} bytes on disk != {expected} expected from 4*k*tokens"
    print(
        f"wrote {actual:,} bytes for {num_tokens:,} tokens at k={k} "
        f"({actual / num_tokens:.0f} bytes/token, matches 4*k={4 * k})"
    )
    return actual


def cmd_train(args: argparse.Namespace) -> None:
    torch.manual_seed(args.seed)
    student_cfg = Config()
    student = Transformer(student_cfg)
    teacher = Transformer(teacher_config(student_cfg))
    teacher.eval()
    for p in teacher.parameters():
        p.requires_grad_(False)

    opt = torch.optim.AdamW(student.parameters(), lr=args.lr)

    print(
        f"student: {sum(p.numel() for p in student.parameters()):,} params  "
        f"teacher (stand-in, untrained): {sum(p.numel() for p in teacher.parameters()):,} params"
    )

    for step in range(args.steps):
        idx = torch.randint(0, student_cfg.vocab_size, (args.batch, args.block_size))
        topk_ids, topk_logprobs = topk_teacher_targets(teacher, idx, args.k, args.temperature)

        student_logits, _ = student(idx)
        loss = topk_soft_ce_loss(student_logits, topk_ids, topk_logprobs, args.temperature)

        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        print(f"step {step:>3}  top-{args.k} soft-CE loss {loss.item():.4f}  T={args.temperature}")

    print(
        "\nThis loss is real, but the teacher is untrained -- it is not evidence "
        "of anything about response quality (see the chapter's evidence-boundary section)."
    )


def cmd_storage_check(args: argparse.Namespace) -> None:
    demo_storage_shard(args.out, args.tokens, args.k)
    args.out.unlink()  # this call only demonstrates the arithmetic; nothing is worth keeping


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train", help="on-the-fly top-k logit distillation, teacher forward pass live")
    t.add_argument("--steps", type=int, default=20)
    t.add_argument("--batch", type=int, default=4)
    t.add_argument("--block-size", type=int, default=64)
    t.add_argument("--k", type=int, default=16)
    t.add_argument("--temperature", type=float, default=1.0)
    t.add_argument("--lr", type=float, default=3e-4)
    t.add_argument("--seed", type=int, default=1337)
    t.set_defaults(func=cmd_train)

    s = sub.add_parser("storage-check", help="write one shard, verify the 4k-bytes/token formula")
    s.add_argument("--out", type=Path, default=Path("shard.bin"))
    s.add_argument("--tokens", type=int, default=4096)
    s.add_argument("--k", type=int, default=16)
    s.set_defaults(func=cmd_storage_check)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
