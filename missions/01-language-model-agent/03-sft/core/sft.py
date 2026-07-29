"""Supervised fine-tuning: a pretrained base checkpoint in, a chat model out.

Stage 02 trained a next-token predictor over web documents. That model has no
notion of "answer the question" — asked something, it is just as likely to
continue the prompt with a plausible-looking *next question* as to answer it,
because that is what web text does. SFT does not teach new knowledge; it
teaches the model to recognize a conversation and to stop when its turn is
over. Two mechanisms carry all of that:

**The chat template.** Wrapping `(role, content)` turns in literal marker
tokens — `<|im_start|>role\\n...content...<|im_end|>\\n` here, matching the
ChatML convention most 2026 open chat models ship with — turns an
undifferentiated string into a structure the model can learn to recognize.
There is nothing privileged about these particular markers; they are a
convention the model *learns to obey*, not a syntax the model already
understands. Get the template wrong at inference time (different markers, or
missing whitespace) and a well-trained chat model degrades toward its base
behavior, because the input no longer matches anything it was trained on.

**Loss masking.** The loss is computed only on assistant tokens. `labels[i]`
equals `ids[i]` where token `i` belongs to an assistant turn, and `-100`
(PyTorch's `CrossEntropyLoss`/`cross_entropy` default `ignore_index`)
everywhere else — see `render_and_mask` below for the exact span bookkeeping.
Skipping this and training on the full sequence, prompt included, wastes most
of a batch's compute reproducing text the model will never have to generate
(the user's turn is *given* at inference time, never predicted), and it
actively teaches the model to continue by generating a plausible next user
turn instead of stopping — the same failure mode as an un-tuned base model,
reintroduced by the fine-tune meant to fix it.

This file also packs multiple short conversations into one training sequence
instead of padding each one to `block_size` — see `pack()` for why, and for
the one limitation that reusing `model.py` unmodified imposes on packing here.

Because SFT perturbs a model that already works, the learning rate is roughly
30x lower than stage 02's pretraining peak (`--lr` defaults to 2e-5 here vs.
6e-4 there) and training runs a handful of epochs over a small dataset rather
than a fraction of one epoch over billions of tokens. A peak pretraining-scale
LR applied to a converged model does not fine-tune it; it re-randomizes it,
a phenomenon usually described as catastrophic forgetting.

Everything else — gradient accumulation, bf16 autocast, cosine LR decay,
resumable optimizer-state checkpoints, MFU reporting — is reused from stage
02's `train.py`, because none of it is specific to SFT. Only the data
pipeline and the loss target change.

Run:  python sft.py train --tokenizer <tokenizer_hf.json> \\
          --init-checkpoint ../../02-pretrain/ckpt/ckpt.pt --out ckpt
      python sft.py sample --tokenizer <tokenizer_hf.json> \\
          --checkpoint ckpt/ckpt.pt --prompt "What causes seasons on Earth?"
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import torch
from tokenizers import Tokenizer
from torch.nn import functional as F

# The base model and training-loop plumbing live one stage over. Importing
# them — rather than keeping a second copy — is the point: SFT must fine-tune
# the exact architecture and loop stage 02 built, not a lookalike.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02-pretrain" / "core"))

from model import Config, Transformer
from train import lr_at, save_checkpoint

# ---------------------------------------------------------------------------
# Special tokens
#
# stage 01's tokenizer covers ids 0..16383. stage 02 padded Config.vocab_size
# up to 16512 (the next multiple of 128) and spent id 16384 on a document
# separator, leaving 127 ids unused purely for tensor-core alignment. That
# headroom is exactly where chat-template and packing scaffolding belongs: we
# spend three more of those free ids here instead of touching Config at all.
IGNORE_INDEX = -100  # cross_entropy's default ignore_index; see note below
IM_START = 16385  # opens every turn: "<|im_start|>"
IM_END = 16386  # closes every turn, and is the token that teaches a stop
PAD_ID = 16387  # fills the tail of a packed block; never a loss target


def render_and_mask(turns: list[dict], tok: Tokenizer) -> tuple[list[int], list[int]]:
    """Render a multi-turn conversation into (token ids, loss labels).

    Every turn becomes `<|im_start|>{role}\\n{content}<|im_end|>\\n`. `labels`
    is the same length as `ids`: it equals `ids` wherever the token is part of
    an assistant turn's content or its closing `<|im_end|>`, and `IGNORE_INDEX`
    everywhere else — the header (`<|im_start|>role\\n`) is never a target, on
    any turn, because at inference time the harness supplies it; the model
    never has to generate its own turn markers, so training on them wastes
    capacity teaching the model to impersonate the chat scaffold instead of
    the user.

    Concretely, for one assistant turn "yes." (say it tokenizes to 3 ids):

        ids     <|im_start|>  assistant \\n   yes   .   <|im_end|>  \\n
        labels     -100         -100   -100   yes   .   <|im_end|>  -100

    Only "yes.<|im_end|>" — the part the model must produce — is trained on.
    Everything that precedes it is context; everything after it is the
    turn-separator whitespace, also not something the model needs to predict.

    `labels[i] == ids[i]` (never a separate sentinel value) is deliberate: it
    means these labels can be handed to `Transformer.forward` completely
    unmodified. `model.py`'s loss is `F.cross_entropy(logits, targets)` with
    no `ignore_index` argument, which means it already defaults to -100 — the
    exact value used here. No change to the frozen model was needed to make
    it SFT-aware; -100 is why AND is not a coincidence, it is the reason that
    sentinel is the field's near-universal choice for masked labels.
    """
    ids: list[int] = []
    labels: list[int] = []
    for turn in turns:
        header = tok.encode(f"{turn['role']}\n").ids
        body = tok.encode(turn["content"]).ids
        tail = tok.encode("\n").ids  # the blank line separating turns

        ids += [IM_START] + header + body + [IM_END] + tail
        prefix_len = 1 + len(header)  # <|im_start|> + "role\n": never a target
        if turn["role"] == "assistant":
            labels += (
                [IGNORE_INDEX] * prefix_len + body + [IM_END] + [IGNORE_INDEX] * len(tail)
            )
        else:
            labels += [IGNORE_INDEX] * (prefix_len + len(body) + 1 + len(tail))
    return ids, labels


def render_prompt(turns: list[dict], tok: Tokenizer) -> list[int]:
    """Render turns for generation: stop right after the assistant header.

    This is what a real inference harness does — it supplies everything up to
    and including "<|im_start|>assistant\\n" and lets the model produce what
    comes after. Reusing `render_and_mask` and discarding its labels keeps the
    two paths (train, generate) from silently drifting apart.
    """
    ids, _ = render_and_mask(turns, tok)
    return ids + [IM_START] + tok.encode("assistant\n").ids


def pack(
    examples: list[tuple[list[int], list[int]]], block_size: int
) -> list[tuple[list[int], list[int]]]:
    """Greedily bin-pack rendered examples into fixed-length blocks.

    Each block holds `block_size + 1` tokens: `block_size` inputs plus the one
    extra token every input position needs a next-token target from (see
    `get_batch`). Padding each short conversation to `block_size` on its own —
    the naive alternative — spends most of a batch's forward pass on tokens
    that carry no signal at all, and a well-curated SFT set like the one this
    stage targets is exactly the short, high-variance-length data where that
    waste is worst. Greedy next-fit packing instead keeps closing a block only
    once the next example no longer fits it, so nearly every position holds a
    real token from some conversation; only the small remainder left in each
    block after the last example that fit needs padding, not the whole tail.

    One thing this function does NOT do: reset attention at packing
    boundaries. `Attention.forward` in stage 02's `model.py` always calls
    `scaled_dot_product_attention(..., is_causal=True)` over the entire
    sequence, so a token near the start of conversation B in a block can
    technically attend to conversation A's tokens earlier in the same block.
    Production packing (TRL, torchtune) adds a block-diagonal attention mask
    so packed examples cannot see each other at all — see `prod/trl_sft.py`'s
    comment on exactly this point. Doing that here would mean editing the
    frozen `model.py` this stage reuses rather than redefines, so the leak is
    accepted rather than fixed. It does not corrupt *what* is trained: loss
    masking depends only on `labels`, never on attention, so the model is
    never taught to predict the wrong thing — it just occasionally spends a
    little attention capacity on an unrelated, unhelpful conversation.
    """
    length = block_size + 1
    closed: list[tuple[list[int], list[int]]] = []
    cur_ids: list[int] = []
    cur_labels: list[int] = []
    dropped = 0
    for ids, labels in examples:
        if len(ids) > length:
            dropped += 1  # longer than one whole block; skip rather than
            continue  # truncate a response mid-sentence and train on that
        if cur_ids and len(cur_ids) + len(ids) > length:
            closed.append((cur_ids, cur_labels))
            cur_ids, cur_labels = [], []
        cur_ids += ids
        cur_labels += labels
    if cur_ids:
        closed.append((cur_ids, cur_labels))
    if dropped:
        print(f"packing: dropped {dropped} example(s) longer than one block", flush=True)

    blocks = []
    for ids, labels in closed:
        pad = length - len(ids)
        blocks.append((ids + [PAD_ID] * pad, labels + [IGNORE_INDEX] * pad))
    return blocks


def _rows(dataset: str, split: str):
    """A hub dataset, or a local JSONL of the same `messages` shape.

    The local path exists so an arm trained on teacher-generated answers runs
    through this trainer unchanged. Distillation at sequence level *is* this
    trainer -- the only thing that differs is who wrote the assistant turn, so
    forking a second training script to say so would be duplicating the code
    in order to hide the point.
    """
    from datasets import load_dataset  # deferred: only needed for this path

    if dataset.endswith((".jsonl", ".json")):
        return load_dataset("json", data_files=dataset, split="train")
    return load_dataset(dataset, split=split)


def load_examples(dataset: str, split: str, tok: Tokenizer, limit: int | None):
    """Pull a chat-formatted instruct dataset and render every row.

    Default is HuggingFaceH4/no_robots: ~10,000 examples written by
    professional annotators rather than sampled from another model — a
    reproduction of LIMA's argument (Zhou et al., 2023) that a small,
    carefully curated instruction set gets most of the way to a much larger,
    noisier one. Each row's `messages` field is already `[{"role", "content"},
    ...]`, the same shape `render_and_mask` expects.
    """
    rows = _rows(dataset, split)
    if limit:
        rows = rows.select(range(min(limit, len(rows))))

    examples = []
    skipped = 0
    for row in rows:
        turns = row["messages"]
        if not turns or turns[-1]["role"] != "assistant":
            skipped += 1  # nothing to train the loss on in this row
            continue
        examples.append(render_and_mask(turns, tok))
    if skipped:
        print(f"{dataset}/{split}: skipped {skipped} row(s) not ending in assistant", flush=True)
    return examples


def get_batch(blocks: list[tuple[list[int], list[int]]], batch: int, device: str):
    """Sample packed blocks and split each into (input, next-token target).

    Mirrors stage 02's `get_batch`: `x` is the block's first `block_size`
    tokens, `y` is its labels shifted one position later, so `y[t]` is the
    (possibly masked) target for the token the model predicts after seeing
    `x[0..t]`.
    """
    idx = torch.randint(len(blocks), (batch,))
    xs, ys = [], []
    for i in idx.tolist():
        ids, labels = blocks[i]
        xs.append(torch.tensor(ids[:-1], dtype=torch.long))
        ys.append(torch.tensor(labels[1:], dtype=torch.long))
    x, y = torch.stack(xs), torch.stack(ys)
    if device.startswith("cuda"):
        return (
            x.pin_memory().to(device, non_blocking=True),
            y.pin_memory().to(device, non_blocking=True),
        )
    return x.to(device), y.to(device)


@torch.no_grad()
def evaluate(model, blocks, batch: int, device: str, iters: int, autocast) -> float:
    if not blocks:
        return float("nan")
    model.eval()
    n = max(1, min(iters, len(blocks) // max(1, min(batch, len(blocks)))))
    losses = []
    for _ in range(n):
        x, y = get_batch(blocks, min(batch, len(blocks)), device)
        with autocast:
            _, loss = model(x, y)
        losses.append(loss.item())
    model.train()
    return sum(losses) / len(losses)


@torch.no_grad()
def generate(
    model,
    tok: Tokenizer,
    prompt_ids: list[int],
    max_new_tokens: int,
    device: str,
    block_size: int,
    temperature: float = 0.8,
    top_k: int = 50,
) -> str:
    """Greedy/temperature sampling, one token at a time, no KV cache.

    Recomputing the full forward pass on every step is deliberately naive —
    caching keys and values so each step costs one token, not the whole
    prefix, is stage 05's subject. This function exists to compare the base
    checkpoint and the SFT checkpoint on identical prompts, not to serve.
    """
    model.eval()
    ids = list(prompt_ids)
    for _ in range(max_new_tokens):
        window = ids[-block_size:]
        x = torch.tensor([window], dtype=torch.long, device=device)
        logits, _ = model(x)
        logits = logits[0, -1] / max(temperature, 1e-6)
        if top_k:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits = logits.masked_fill(logits < v[-1], float("-inf"))
        probs = F.softmax(logits, dim=-1)
        next_id = int(torch.multinomial(probs, 1).item())
        ids.append(next_id)
        if next_id == IM_END:
            break
    model.train()
    vocab_size = tok.get_vocab_size()
    generated = [t for t in ids[len(prompt_ids) :] if t < vocab_size]
    return tok.decode(generated)


def build_optimizer(model: torch.nn.Module, lr: float, weight_decay: float, device: str):
    # Weight decay on matrices only, never on RMSNorm gains — same rule stage
    # 02 applies, restated here because SFT builds its own optimizer instead
    # of resuming stage 02's (a fresh optimizer at a much lower LR, not the
    # pretraining Adam state, is exactly the point: see the module docstring).
    decay = [p for _, p in model.named_parameters() if p.dim() >= 2]
    no_decay = [p for _, p in model.named_parameters() if p.dim() < 2]
    return torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": weight_decay},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=lr,
        betas=(0.9, 0.95),
        eps=1e-8,
        fused=(device == "cuda"),
    )


def cmd_train(args: argparse.Namespace) -> None:
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    tok = Tokenizer.from_file(str(args.tokenizer))
    cfg = Config()
    model = Transformer(cfg).to(args.device)

    init_ckpt = torch.load(args.init_checkpoint, map_location=args.device, weights_only=False)
    model.load_state_dict(init_ckpt["model"])
    print(
        f"loaded base checkpoint: {args.init_checkpoint} "
        f"({init_ckpt.get('tokens_seen', 0) / 1e9:.2f}B pretraining tokens)",
        flush=True,
    )

    # Eval may come from somewhere other than training. Comparing arms that
    # were trained on different authors' answers requires holding the *target*
    # fixed: each arm is scored on the same held-out human-written turns, not on
    # a sample of its own teacher. Score an arm against its own teacher and the
    # number rewards a model for imitating whoever it was trained to imitate,
    # which is the one thing every arm is guaranteed to do.
    eval_source = args.eval_dataset or args.dataset
    train_examples = load_examples(args.dataset, args.train_split, tok, args.limit)
    eval_examples = load_examples(eval_source, args.eval_split, tok, args.eval_limit)
    train_blocks = pack(train_examples, cfg.block_size)
    eval_blocks = pack(eval_examples, cfg.block_size)

    real = sum(sum(1 for t in ids if t != PAD_ID) for ids, _ in train_blocks)
    capacity = len(train_blocks) * (cfg.block_size + 1)
    print(
        f"train: {len(train_examples):,} conversations -> {len(train_blocks):,} packed "
        f"block(s) of {cfg.block_size + 1}, {real / max(1, capacity):.1%} real tokens",
        flush=True,
    )
    print(f"eval:  {len(eval_examples):,} conversations -> {len(eval_blocks):,} block(s)",
          flush=True)

    steps_per_epoch = max(1, len(train_blocks) // (args.batch * args.grad_accum))
    total_steps = steps_per_epoch * args.epochs
    if args.max_steps:
        # Epochs are the wrong budget when the arms differ in answer length. A
        # model teacher writes longer answers than a human annotator, so the
        # same 3,000 prompts pack into more blocks, and "3 epochs" silently
        # hands that arm more gradient steps and more tokens. Capping steps
        # makes the optimizer budget identical and leaves author as the only
        # thing that varies -- which was the entire point of the comparison.
        total_steps = min(total_steps, args.max_steps)
    print(
        f"epochs {args.epochs} x {steps_per_epoch:,} steps/epoch -> {total_steps:,} steps "
        f"(micro {args.batch} x accum {args.grad_accum})",
        flush=True,
    )

    opt = build_optimizer(model, args.lr, args.weight_decay, args.device)
    autocast = (
        torch.autocast("cuda", dtype=torch.bfloat16)
        if args.device == "cuda"
        else nullcontext()
    )
    peak_flops = 165e12  # bf16 dense, adjust per card; only affects the MFU figure
    n_params = sum(p.numel() for p in model.parameters())

    history: list[dict] = []
    tokens_seen = 0
    start_step = 0
    t0 = time.time()

    ckpt_path = args.out / "ckpt.pt"
    if args.resume and ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=args.device, weights_only=False)
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["optimizer"])
        start_step = ckpt["step"]
        history = ckpt.get("history", [])
        tokens_seen = ckpt.get("tokens_seen", 0)
        print(f"resumed from {ckpt_path}: step {start_step:,}", flush=True)

    for step in range(start_step, total_steps + 1):
        lr = lr_at(step, args.warmup, total_steps, args.lr)
        for g in opt.param_groups:
            g["lr"] = lr

        if step % args.eval_every == 0:
            val = evaluate(model, eval_blocks, args.batch, args.device, args.eval_iters, autocast)
            elapsed = time.time() - t0
            tps = tokens_seen / elapsed if elapsed > 0 else 0
            flops_per_token = 6 * n_params + 12 * cfg.n_layer * cfg.block_size * cfg.d_model
            mfu = tps * flops_per_token / peak_flops * 100
            rec = {
                "step": step, "val_loss": val, "lr": lr,
                "tokens": tokens_seen, "elapsed_s": round(elapsed, 1),
                "tok_per_s": round(tps), "mfu_pct": round(mfu, 1),
            }
            history.append(rec)
            (args.out / "history.json").write_text(json.dumps(history, indent=1))
            print(
                f"step {step:>6,}  val {val:.4f}  lr {lr:.2e}  "
                f"{tokens_seen / 1e6:7.1f}M tok  {tps / 1e3:5.1f}k tok/s  MFU {mfu:4.1f}%",
                flush=True,
            )

        if step > 0 and step % args.checkpoint_every == 0:
            save_checkpoint(ckpt_path, model, opt, cfg, step, history, tokens_seen)

        if step == total_steps:
            break

        opt.zero_grad(set_to_none=True)
        for _ in range(args.grad_accum):
            x, y = get_batch(train_blocks, args.batch, args.device)
            with autocast:
                _, loss = model(x, y)
                loss = loss / args.grad_accum
            loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip)
        opt.step()
        tokens_seen += args.batch * cfg.block_size * args.grad_accum

    save_checkpoint(ckpt_path, model, opt, cfg, total_steps, history, tokens_seen)
    print(f"done in {(time.time() - t0) / 3600:.2f}h -> {ckpt_path}", flush=True)

    print(f"\n{args.samples_after} sample completion(s) after training:", flush=True)
    prompts = _first_user_turns(eval_source, args.eval_split, args.samples_after)
    for i, turns in enumerate(prompts):
        prompt_ids = render_prompt(turns, tok)
        reply = generate(model, tok, prompt_ids, args.max_new_tokens, args.device, cfg.block_size)
        print(f"  [{i}] {turns[-1]['content'][:80]!r} -> {reply[:200]!r}", flush=True)


def _first_user_turns(dataset: str, split: str, n: int):
    """Re-pull just enough rows to get their leading user turn, for the
    after-training sample prints. A second, small dataset fetch is simpler and
    cheaper than carrying raw turns alongside every rendered/packed example."""
    if n <= 0:
        return
    rows = _rows(dataset, split).select(range(n))
    for row in rows:
        turns = row["messages"]
        yield [t for t in turns if t["role"] != "assistant"]


def cmd_sample(args: argparse.Namespace) -> None:
    tok = Tokenizer.from_file(str(args.tokenizer))
    cfg = Config()
    model = Transformer(cfg).to(args.device)
    ckpt = torch.load(args.checkpoint, map_location=args.device, weights_only=False)
    model.load_state_dict(ckpt["model"])

    turns = []
    if args.system:
        turns.append({"role": "system", "content": args.system})
    turns.append({"role": "user", "content": args.prompt})

    prompt_ids = render_prompt(turns, tok)
    reply = generate(model, tok, prompt_ids, args.max_new_tokens, args.device, cfg.block_size)
    print(reply)


def cmd_score(args: argparse.Namespace) -> None:
    """Loss of one checkpoint on one held-out set, printed as JSON.

    Separated from `train` so the same checkpoint can be scored against several
    reference sets. When arms are trained on answers by different authors, a
    single held-out set cannot settle which arm is better: it is drawn from one
    author, and the arm trained on that author will win on it whether or not it
    learned anything else. Scoring every arm on every author's held-out answers
    turns that objection into a table you can read.
    """
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    tok = Tokenizer.from_file(str(args.tokenizer))
    cfg = Config()
    model = Transformer(cfg).to(args.device)
    ckpt = torch.load(args.checkpoint, map_location=args.device, weights_only=False)
    model.load_state_dict(ckpt["model"])

    blocks = pack(load_examples(args.dataset, args.split, tok, args.limit), cfg.block_size)
    autocast = (
        torch.autocast("cuda", dtype=torch.bfloat16)
        if args.device == "cuda"
        else nullcontext()
    )
    loss = evaluate(model, blocks, args.batch, args.device, args.eval_iters, autocast)
    print(json.dumps({
        "checkpoint": str(args.checkpoint),
        "dataset": args.dataset,
        "split": args.split,
        "blocks": len(blocks),
        "loss": round(loss, 4),
    }), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train")
    t.add_argument("--tokenizer", type=Path, required=True,
                    help="HF tokenizers JSON, see ../../01-tokenizer/prod/hf_tokenizer.py export")
    t.add_argument("--init-checkpoint", type=Path, required=True,
                    help="stage 02 pretrained ckpt.pt")
    t.add_argument("--out", type=Path, default=Path("ckpt"))
    t.add_argument("--dataset", default="HuggingFaceH4/no_robots")
    t.add_argument("--train-split", default="train")
    t.add_argument("--eval-dataset", default=None,
                   help="score against this instead of --dataset; the held-out "
                        "target when arms differ in who wrote their answers")
    t.add_argument("--eval-split", default="test")
    t.add_argument("--limit", type=int, default=None, help="cap training rows, for a quick pass")
    t.add_argument("--eval-limit", type=int, default=200)
    t.add_argument("--epochs", type=int, default=3)
    t.add_argument("--max-steps", type=int, default=None,
                   help="cap total steps, to give arms an equal optimizer budget")
    t.add_argument("--batch", type=int, default=8, help="micro-batch size, in packed blocks")
    t.add_argument("--grad-accum", type=int, default=4)
    t.add_argument("--lr", type=float, default=2e-5,
                    help="~30x below stage 02's 6e-4 peak; see module docstring")
    t.add_argument("--warmup", type=int, default=30)
    t.add_argument("--weight-decay", type=float, default=0.0)
    t.add_argument("--clip", type=float, default=1.0)
    t.add_argument("--eval-every", type=int, default=50)
    t.add_argument("--eval-iters", type=int, default=20)
    t.add_argument("--checkpoint-every", type=int, default=200)
    t.add_argument("--samples-after", type=int, default=3)
    t.add_argument("--max-new-tokens", type=int, default=200)
    t.add_argument("--device", default="cuda")
    t.add_argument("--seed", type=int, default=1337)
    t.add_argument("--resume", action="store_true")
    t.set_defaults(func=cmd_train)

    s = sub.add_parser("sample")
    s.add_argument("--tokenizer", type=Path, required=True)
    s.add_argument("--checkpoint", type=Path, required=True,
                    help="any ckpt.pt: stage 02's for the 'before', this stage's for the 'after'")
    s.add_argument("--prompt", required=True)
    s.add_argument("--system", default=None)
    s.add_argument("--max-new-tokens", type=int, default=200)
    s.add_argument("--device", default="cuda")
    s.set_defaults(func=cmd_sample)

    e = sub.add_parser("score")
    e.add_argument("--tokenizer", type=Path, required=True)
    e.add_argument("--checkpoint", type=Path, required=True)
    e.add_argument("--dataset", default="HuggingFaceH4/no_robots",
                   help="hub id or a local JSONL of held-out reference answers")
    e.add_argument("--split", default="test")
    e.add_argument("--limit", type=int, default=200)
    e.add_argument("--batch", type=int, default=8)
    e.add_argument("--eval-iters", type=int, default=20)
    e.add_argument("--device", default="cuda")
    e.add_argument("--seed", type=int, default=1337)
    e.set_defaults(func=cmd_score)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
