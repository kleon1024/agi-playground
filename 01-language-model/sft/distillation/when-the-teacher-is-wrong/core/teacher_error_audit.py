"""Deterministic audit of what sequence-level distillation copies when the
teacher is wrong: train a clean teacher and a systematically-erroring
teacher on the same corpus, distil each into a student on the teacher's own
generated completions (the chapter's path one: copy the words), and measure
what transfers.

The failure mode this chapter is about is not that distillation is slow or
expensive; it is that distillation copies the teacher's *output
distribution*, and a teacher's systematic errors live inside that
distribution. Factuality and correctness are not a separate channel that
distillation can keep while dropping the errors -- the student gets the
teacher's whole distribution, style and mistakes together. An untrained
teacher transfers nothing at all, because there is no signal in its output.

No CUDA GPU is available in this environment, so the audit trains tiny
character-level models on tinyshakespeare (the same corpus the serving
stage's speculative and cascade chapters train on):

* teacher-good:    trained on clean text  -> its errors are the model's own
* teacher-noisy:   trained on text where every 'e' is replaced by 'x' ->
  its output distribution is systematically wrong on one letter class, the
  way a teacher with a real factual blind spot is confidently wrong on one
  subject
* teacher-random:  untrained -> no signal to transfer
* students:        one per teacher, trained on that teacher's greedy
  completions of held-out prompts

Measured per model: cross-entropy on clean held-out text, plus the
inheritance metric -- the 'e' and 'x' rates in the model's own completions.
A clean lineage writes 'e' at the natural rate and essentially no 'x'; the
corrupted lineage swaps them; a student distilled from the corrupted teacher
inherits the swap.

Run:  uv run --group torch python3 teacher_error_audit.py
"""

from __future__ import annotations

import argparse
import random
import sys
import time
import urllib.request
from pathlib import Path

import torch
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "01-language-model/pretrain/core"))
from model import Config, Transformer

DEVICE = "cpu"
DATA_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
DATA_PATH = Path(__file__).resolve().parent / "data" / "cache" / "shakespeare.txt"


def load_corpus() -> str:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    return DATA_PATH.read_text()


def build_tokenizer(text: str):
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    itos = {i: c for c, i in stoi.items()}
    encode = lambda s: [stoi[c] for c in s]
    decode = lambda ids: "".join(itos[i] for i in ids)
    return len(chars), encode, decode, stoi


def get_batch(data: torch.Tensor, block: int, batch: int, rng: torch.Generator):
    ix = torch.randint(len(data) - block - 1, (batch,), generator=rng)
    x = torch.stack([data[i : i + block] for i in ix])
    y = torch.stack([data[i + 1 : i + block + 1] for i in ix])
    return x, y


def train(
    model: Transformer,
    data: torch.Tensor,
    block: int,
    batch: int,
    steps: int,
    lr: float,
    seed: int,
    label: str,
) -> float:
    gen = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    model.train()
    t0 = time.perf_counter()
    for step in range(steps):
        x, y = get_batch(data, block, batch, gen)
        _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % max(1, steps // 4) == 0 or step == steps - 1:
            print(f"  [{label}] step {step:4d}/{steps}  loss {loss.item():.4f}")
    model.eval()
    return time.perf_counter() - t0


def corrupt(text: str, char: str, replacement: str, p: float, seed: int) -> str:
    """Replace `char` with `replacement` with probability p, seeded and
    deterministic -- the teacher's systematic, partially unpredictable error."""
    rng = random.Random(seed)
    return "".join(
        replacement if c == char and rng.random() < p else c for c in text
    )


@torch.no_grad()
def greedy(model: Transformer, prompt_ids: list[int], n_tokens: int) -> list[int]:
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    generated = []
    for _ in range(n_tokens):
        logits, _ = model(idx)
        nxt = int(logits[0, -1].argmax())
        generated.append(nxt)
        idx = torch.cat([idx, torch.tensor([[nxt]])], dim=1)
    return generated


@torch.no_grad()
def sample(
    model: Transformer,
    prompt_ids: list[int],
    n_tokens: int,
    temperature: float,
    seed: int,
) -> list[int]:
    """Temperature-1.0 sampling continuation -- the way a real trace generator
    produces diverse completions, instead of greedy loops."""
    rng = torch.Generator().manual_seed(seed)
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    generated = []
    for _ in range(n_tokens):
        logits, _ = model(idx)
        logits = logits[0, -1] / temperature
        probs = F.softmax(logits, dim=-1)
        nxt = int(torch.multinomial(probs, 1, generator=rng).item())
        generated.append(nxt)
        idx = torch.cat([idx, torch.tensor([[nxt]])], dim=1)
    return generated


@torch.no_grad()
def clean_ce(model: Transformer, data: torch.Tensor, block: int, n: int, seed: int) -> float:
    """Average next-token CE on clean held-out text."""
    gen = torch.Generator().manual_seed(seed)
    model.eval()
    total, count = 0.0, 0
    for _ in range(n):
        x, y = get_batch(data, block, 8, gen)
        logits, _ = model(x)
        loss = F.cross_entropy(
            logits.reshape(-1, logits.size(-1)), y.reshape(-1), reduction="sum"
        )
        total += loss.item()
        count += y.numel()
    return total / count


def distill(
    student: Transformer,
    completions: list[list[int]],
    prompt_lens: list[int],
    steps: int,
    lr: float,
    seed: int,
    label: str,
) -> float:
    """Path-one distillation: train the student on the teacher's greedy
    completions of the given prompts, masking the prompt (the chapter's loss
    masking, at char scale)."""
    rng = random.Random(seed)
    opt = torch.optim.AdamW(student.parameters(), lr=lr)
    student.train()
    t0 = time.perf_counter()
    for step in range(steps):
        indices = rng.sample(range(len(completions)), k=min(8, len(completions)))
        batch = [completions[i] for i in indices]
        lengths = [prompt_lens[i] for i in indices]
        # one sequence per row; pad to the longest in the batch
        width = max(len(seq) for seq in batch)
        x = torch.tensor(
            [[seq[i] if i < len(seq) else 0 for i in range(width)] for seq in batch]
        )
        y = torch.tensor(
            [
                [
                    seq[i + 1] if i + 1 < len(seq) and i >= lengths[r] else -100
                    for i in range(width)
                ]
                for r, seq in enumerate(batch)
            ]
        )
        logits, _ = student(x)
        loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % max(1, steps // 4) == 0 or step == steps - 1:
            print(f"  [{label}] step {step:4d}/{steps}  loss {loss.item():.4f}")
    student.eval()
    return time.perf_counter() - t0


@torch.no_grad()
def inheritance(
    model: Transformer,
    prompt_ids_list: list[list[int]],
    n_gen: int,
    stoi: dict[str, int],
) -> tuple[float, float, float]:
    """For each held-out clean prompt, generate greedily and count the 'e'
    and 'x' rates in the output. A clean lineage writes 'e' at the natural
    rate and essentially no 'x'; the corrupted lineage swaps them."""
    e_id, x_id = stoi["e"], stoi["x"]
    e_total = x_total = n_total = 0
    for prompt_ids in prompt_ids_list:
        generated = greedy(model, prompt_ids, n_gen)
        for gen_tok in generated:
            n_total += 1
            if gen_tok == x_id:
                x_total += 1
            if gen_tok == e_id:
                e_total += 1
    x_rate = x_total / n_total if n_total else float("nan")
    e_rate = e_total / n_total if n_total else float("nan")
    return x_rate, e_rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher-steps", type=int, default=600)
    ap.add_argument("--student-steps", type=int, default=300)
    ap.add_argument("--block", type=int, default=128)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--n-prompts", type=int, default=200)
    ap.add_argument("--prompt-len", type=int, default=80)
    ap.add_argument("--n-gen", type=int, default=96)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--corrupt-p", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1337)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    text = load_corpus()
    vocab_size, encode, decode, stoi = build_tokenizer(text)
    data = torch.tensor(encode(text), dtype=torch.long)
    noisy_text = corrupt(text, "e", "x", args.corrupt_p, args.seed)
    noisy_data = torch.tensor(encode(noisy_text), dtype=torch.long)

    teacher_cfg = Config(
        vocab_size=vocab_size, n_layer=3, n_head=3, n_kv_head=3,
        d_model=192, d_ff=512, block_size=args.block,
    )
    student_cfg = Config(
        vocab_size=vocab_size, n_layer=2, n_head=2, n_kv_head=2,
        d_model=96, d_ff=256, block_size=args.block,
    )

    teacher_good = Transformer(teacher_cfg)
    teacher_noisy = Transformer(teacher_cfg)
    teacher_random = Transformer(teacher_cfg)  # untrained: no signal
    print(f"teacher: {teacher_good.param_report()}")
    print(f"student: {Transformer(student_cfg).param_report()}")
    print()

    print("training teacher-good on clean text...")
    t_tg = train(teacher_good, data, args.block, args.batch, args.teacher_steps, 3e-4, args.seed, "teacher-good")
    print(f"  teacher-good train wall-clock: {t_tg:.2f}s\n")
    print("training teacher-noisy on e->x corrupted text...")
    t_tn = train(teacher_noisy, noisy_data, args.block, args.batch, args.teacher_steps, 3e-4, args.seed + 1, "teacher-noisy")
    print(f"  teacher-noisy train wall-clock: {t_tn:.2f}s\n")

    # Two disjoint prompt sets: one to distil on (teacher completions), one
    # held out for the inheritance metric and the samples.
    rng = random.Random(args.seed + 2)
    span = args.prompt_len + args.n_gen
    n_eval = 20
    starts = sorted(
        rng.randrange(len(data) - span - 1)
        for _ in range(args.n_prompts + n_eval)
    )
    distill_prompts = [data[s : s + args.prompt_len].tolist() for s in starts[: args.n_prompts]]
    eval_prompts = [data[s : s + args.prompt_len].tolist() for s in starts[args.n_prompts :]]

    students = {}
    for name, teacher in (("student-from-good", teacher_good), ("student-from-noisy", teacher_noisy), ("student-from-random", teacher_random)):
        print(f"distilling {name} on the teacher's completions...")
        student = Transformer(student_cfg)
        completions = [
            p + sample(teacher, p, args.n_gen, args.temperature, args.seed + 5)
            for p in distill_prompts
        ]
        t = distill(
            student, completions, [args.prompt_len] * len(completions),
            args.student_steps, 3e-4, args.seed + 3, name,
        )
        print(f"  {name} distill wall-clock: {t:.2f}s\n")
        students[name] = student

    base_student = Transformer(student_cfg)  # untrained student, no teacher at all

    print("measuring clean held-out CE and error inheritance...\n")
    models = {
        "teacher-good": teacher_good,
        "teacher-noisy": teacher_noisy,
        "teacher-random": teacher_random,
        "student-from-good": students["student-from-good"],
        "student-from-noisy": students["student-from-noisy"],
        "student-from-random": students["student-from-random"],
        "base student (no teacher)": base_student,
    }
    print(
        f"{'model':<26}{'clean CE':>10}{'x rate':>9}{'e rate':>9}"
    )
    print("-" * 54)
    for name, model in models.items():
        ce = clean_ce(model, data, args.block, 32, args.seed + 4)
        x_rate, e_rate = inheritance(model, eval_prompts, args.n_gen, stoi)
        print(f"{name:<26}{ce:>10.3f}{100 * x_rate:>8.1f}%{100 * e_rate:>8.1f}%")

    print()
    print("sample continuations on a held-out clean prompt:")
    sample_prompt = eval_prompts[0]
    print(f"  prompt: {decode(sample_prompt)!r}")
    for name in ("teacher-good", "teacher-noisy", "student-from-good", "student-from-noisy"):
        out = greedy(models[name], sample_prompt, 40)
        print(f"  {name:<20}: {decode(out)!r}")


if __name__ == "__main__":
    main()
