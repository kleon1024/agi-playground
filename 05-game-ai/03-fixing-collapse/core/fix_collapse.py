"""Stage 03: is stage 01's greedy-decode collapse fixable by tuning the
training signal alone, on the SAME 5x5 grid-world, with no other variable
changed?

Reuses stage 01's environment, vocab, reward, and GRPO mechanism unmodified
(`sample_problem`, `rollout_and_score`, `evaluate`, `evaluate_sampled`,
`dump_examples`, `Config`, `Transformer`, `grpo_loss`, `rollout_group`, all
imported from `../../01-grpo/core/train_grpo.py` and `grpo.py`, not
reimplemented). Two variables are swept, each in isolation against stage
01's own baseline config (group_size=8, no entropy bonus):

1. Smaller group size (group_size=4 instead of 8) -- per Fan et al.,
   "Learning Without Critics? Revisiting GRPO in Classical RL Environments"
   (arXiv 2511.03527), smaller groups reduced collapse in their classical-RL
   GRPO experiments, the opposite of typical LLM-RLHF intuition.
2. An entropy bonus added to the training loss (`total_loss - entropy_coef *
   mean_completion_entropy`), which directly penalizes exactly the failure
   mode observed: a policy whose argmax has converged to one action
   regardless of the board, while its full distribution still carries real
   signal (this is what sampled decode was already scoring on).

Neither changes `grpo.py`'s own `grpo_loss`/`rollout_group`/`token_logprobs`
-- the entropy term is computed here, in this stage's own train loop, and
added on top of the imported loss, matching the mission's own "changing only
the reward function and rollout environment, not the training algorithm"
framing extended to "or an additive loss term local to this stage."
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "01-grpo" / "core"))
from env_text import VOCAB
from train_grpo import (
    dump_examples,
    evaluate,
    evaluate_sampled,
    rollout_and_score,
    sample_problem,
)

_GRPO_DIR = Path(__file__).resolve().parents[3] / "01-language-model" / "04-rl" / "core"
sys.path.insert(0, str(_GRPO_DIR))
from grpo import Config, Transformer, grpo_loss


def mean_completion_entropy(model: Transformer, full_ids: torch.Tensor, prompt_len: int, completion_len: int) -> torch.Tensor:
    """Mean token-level entropy of the policy's own distribution over the
    completion positions -- the same teacher-forced forward pass shape as
    `grpo.py`'s `token_logprobs`, computing entropy instead of the log-prob
    of one target token."""
    logits, _ = model(full_ids)
    logp = F.log_softmax(logits[:, :-1, :], dim=-1)
    p = logp.exp()
    entropy = -(p * logp).sum(dim=-1)  # [B, T-1]
    start = prompt_len - 1
    return entropy[:, start : start + completion_len].mean()


def train_variant(args: argparse.Namespace) -> dict:
    device = torch.device(args.device)
    cfg = Config(vocab_size=len(VOCAB), n_layer=4, n_head=4, n_kv_head=2, d_model=128, d_ff=320, block_size=args.block_size)
    model = Transformer(cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    ref_model = copy.deepcopy(model).to(device)
    ref_model.eval()
    for p in ref_model.parameters():
        p.requires_grad_(False)

    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    history: list[dict] = []
    degenerate_steps = 0

    t0 = time.perf_counter()
    for step in range(args.steps):
        rollouts = []
        step_rewards: list[float] = []
        step_breakdowns: list[dict[str, float]] = []
        for _ in range(args.prompts_per_step):
            problem = sample_problem(rng, args.size, args.num_walls, args.max_steps)
            ro = rollout_and_score(model, problem, args.group_size, args.max_steps, args.temperature, device)
            if ro is None:
                continue
            rollouts.append(ro)
            step_rewards.extend(ro.rewards)
            step_breakdowns.extend(ro.breakdowns)

        if not rollouts:
            degenerate_steps += 1
            continue

        last_loss = 0.0
        last_entropy = 0.0
        for _ in range(args.inner_epochs):
            optimizer.zero_grad(set_to_none=True)
            total_loss = torch.zeros((), device=device)
            total_entropy = torch.zeros((), device=device)
            for ro in rollouts:
                total_loss = total_loss + grpo_loss(model, ref_model, ro, args.clip_eps, args.kl_beta)
                if args.entropy_coef > 0:
                    ent = mean_completion_entropy(model, ro.full_ids, ro.prompt_len, ro.completion_len)
                    total_loss = total_loss - args.entropy_coef * ent
                    total_entropy = total_entropy + ent.detach()
            total_loss = total_loss / len(rollouts)
            total_loss.backward()
            optimizer.step()
            last_loss = float(total_loss.detach())
            last_entropy = float(total_entropy.detach() / len(rollouts))

        if step % args.log_every == 0:
            record = {
                "step": step,
                "mean_reward": sum(step_rewards) / len(step_rewards),
                "mean_success": sum(b["success"] for b in step_breakdowns) / len(step_breakdowns),
                "loss": last_loss,
                "mean_entropy": last_entropy,
                "groups_used": len(rollouts),
            }
            history.append(record)
            print(json.dumps(record), flush=True)

    elapsed = time.perf_counter() - t0
    eval_greedy = evaluate(model, args.size, args.num_walls, args.max_steps, args.eval_trials, args.seed + 10_000, device)
    eval_sampled = evaluate_sampled(model, args.size, args.num_walls, args.max_steps, args.eval_trials, args.seed + 10_000, device, args.temperature)
    examples = dump_examples(model, args.size, args.num_walls, args.max_steps, 8, args.seed + 20_000, device)

    return {
        "variant": args.variant,
        "group_size": args.group_size,
        "entropy_coef": args.entropy_coef,
        "seed": args.seed,
        "steps": args.steps,
        "degenerate_steps": degenerate_steps,
        "wall_clock_s": elapsed,
        "history": history,
        "eval_greedy": eval_greedy,
        "eval_sampled": eval_sampled,
        "examples": examples,
    }


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Stage 03: sweep group size / entropy bonus for greedy-decode collapse fix.")
    p.add_argument("--variant", type=str, required=True, choices=["small-group", "entropy-bonus"])
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--group-size", type=int, default=8)
    p.add_argument("--entropy-coef", type=float, default=0.0)
    p.add_argument("--prompts-per-step", type=int, default=4)
    p.add_argument("--size", type=int, default=5)
    p.add_argument("--num-walls", type=int, default=4)
    p.add_argument("--max-steps", type=int, default=12)
    p.add_argument("--block-size", type=int, default=96)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--clip-eps", type=float, default=0.2)
    p.add_argument("--kl-beta", type=float, default=0.04)
    p.add_argument("--inner-epochs", type=int, default=2)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", type=str, default="cpu")
    p.add_argument("--log-every", type=int, default=5)
    p.add_argument("--eval-trials", type=int, default=500)
    p.add_argument("--out", type=Path, default=None)
    return p


def main() -> None:
    args = build_argparser().parse_args()
    result = train_variant(args)
    out_path = args.out or (Path(__file__).resolve().parent.parent / "runs" / f"{args.variant}-seed{args.seed}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
