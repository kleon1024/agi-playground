"""Train the same model three ways on the same problems, and compare accuracy.

The three arms differ only in what sits between the question and the answer:

- **`direct`** — nothing. The model must do every hop inside one forward pass.
- **`cot`** — the walk, written out as tokens. Each step is generated, read
  back through the embedding table, and attended to by the next step.
- **`latent`** — the walk, carried as hidden states. Each step is generated and
  fed back *without* passing through the vocabulary, so it never has to commit
  to one token.

The latent arm's mechanism, in full:

    hidden, _ = model(embeds)                  # run the network
    embeds[:, slot] = hidden[:, slot - 1]      # write the thought into the next slot
                                               # repeat, once per thought

That is `n_latent + 1` forward passes per training step, because each thought
depends on the one before it and cannot be computed in parallel with it. The
cost is real and is reported: a continuous thought is not free, it just does not
spend its budget on tokens.

Training the latent arm cold does not work, and the curriculum is not optional
— see the run record. `--stage-steps` trains at n_latent=0 (identical to the
token-chain arm), then 1, then 2, and so on, so the model learns what a thought
should contain while it can still see the tokens that thought replaces.

Usage:
    python train.py --arm cot --steps 4000
    python train.py --arm latent --stage-steps 1500 --seeds 3 --out result.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from model import Config, Reasoner, masked_loss
from task import ANS, NO, THOUGHT, YES, GraphTask


def latent_forward(model: Reasoner, tokens: torch.Tensor, n_latent: int):
    """Forward pass in which `<thought>` slots are filled by the model itself.

    Each thought slot is overwritten with the hidden state at the position
    before it, which is the model's own representation of everything read so
    far. Because thought `j+1` must attend to thought `j`, the passes are
    sequential — this loop is the reason a latent step costs more wall-clock
    than a token step even though it emits fewer tokens.
    """
    embeds = model.embed(tokens)
    if n_latent == 0:
        return model(embeds)

    # Every example in a batch has the same shape — the edge count is fixed, so
    # the prefix length is too — which means the thought slots sit at the same
    # columns in every row and one column index serves the whole batch.
    slots = (tokens[0] == THOUGHT).nonzero(as_tuple=True)[0]
    assert len(slots) == n_latent, f"expected {n_latent} thought slots, found {len(slots)}"

    hidden, logits = model(embeds)
    for slot in slots.tolist():
        # The thought is the model's own state at the position before the slot:
        # everything it has read so far, written straight back in as input
        # without being rounded to the nearest token.
        embeds = torch.cat(
            [embeds[:, :slot], hidden[:, slot - 1 : slot], embeds[:, slot + 1 :]], dim=1
        )
        hidden, logits = model(embeds)
    return hidden, logits


@torch.no_grad()
def accuracy(model: Reasoner, task: GraphTask, arm: str, n_latent: int, rng, n: int, device: str):
    """Fraction of held-out questions answered correctly.

    Scored on the single answer token, by comparing the model's probability for
    `yes` against `no` at the position after `<a>`. Every arm is scored the same
    way, so a difference between arms is a difference in reasoning and not in
    how generously the output was read.
    """
    model.eval()
    correct = 0
    for _ in range(n):
        prefix, chain, answer = task.sample(rng)
        tokens, _ = task.encode(prefix, chain, answer, arm, n_latent)
        cut = tokens.index(ANS) + 1
        ids = torch.tensor([tokens[:cut]], device=device)
        _, logits = latent_forward(model, ids, n_latent if arm == "latent" else 0)
        scores = logits[0, -1]
        predicted = YES if scores[YES] > scores[NO] else NO
        correct += int(predicted == (YES if answer else NO))
    model.train()
    return correct / n


def train_one(arm: str, seed: int, args, task: GraphTask, device: str) -> dict:
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = Reasoner(Config(vocab_size=task.vocab_size, block_size=args.block_size)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    # The latent arm walks its curriculum; the other two hold at one setting.
    schedule = (
        [(s, args.stage_steps) for s in range(task.hops + 1)]
        if arm == "latent"
        else [(0, args.steps)]
    )
    history, started = [], time.perf_counter()
    for n_latent, steps in schedule:
        for step in range(steps):
            tokens_np, sup_np = task.batch(rng, args.batch, arm, n_latent)
            tokens = torch.from_numpy(tokens_np).to(device)
            supervised = torch.from_numpy(sup_np).to(device)
            _, logits = latent_forward(model, tokens, n_latent if arm == "latent" else 0)
            loss = masked_loss(logits, tokens, supervised)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            if step == steps - 1:
                history.append(
                    {"n_latent": n_latent, "loss": round(loss.item(), 4),
                     "accuracy": round(accuracy(model, task, arm, n_latent,
                                                np.random.default_rng(9_999), 200, device), 4)}
                )

    final_latent = task.hops if arm == "latent" else 0
    return {
        "seed": seed,
        "accuracy": round(
            accuracy(model, task, arm, final_latent, np.random.default_rng(9_999), 500, device), 4
        ),
        "curriculum": history,
        "wallclock_s": round(time.perf_counter() - started, 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arms", nargs="+", default=["direct", "cot", "latent"])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=6000, help="steps for direct and cot")
    ap.add_argument("--stage-steps", type=int, default=1500, help="steps per curriculum stage")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--hops", type=int, default=4)
    ap.add_argument("--entities", type=int, default=40)
    ap.add_argument("--block-size", type=int, default=256)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    task = GraphTask(n_entity=args.entities, hops=args.hops)
    result = {
        "task": {"entities": args.entities, "hops": args.hops, "vocab": task.vocab_size},
        "budget": "equal steps for direct and cot; latent trains stage_steps per curriculum stage",
        "seeds": args.seeds,
        "arms": {},
    }
    print(f"{'arm':<10}{'accuracy per seed':>34}{'mean':>9}{'spread':>9}{'wall':>9}")
    for arm in args.arms:
        runs = [train_one(arm, s, args, task, args.device) for s in range(args.seeds)]
        accs = [r["accuracy"] for r in runs]
        mean = sum(accs) / len(accs)
        result["arms"][arm] = {
            "runs": runs, "mean_accuracy": round(mean, 4),
            "seed_spread": round(max(accs) - min(accs), 4),
        }
        wall = sum(r["wallclock_s"] for r in runs) / len(runs)
        print(f"{arm:<10}{' '.join(f'{a:.3f}' for a in accs):>34}{mean:>9.3f}"
              f"{max(accs) - min(accs):>9.3f}{wall:>8.0f}s")
        if args.out:
            args.out.write_text(json.dumps(result, indent=2))
    if args.out:
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
