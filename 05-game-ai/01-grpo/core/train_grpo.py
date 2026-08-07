"""GRPO on the grid-world environment, reusing mission 01 04-rl's mechanism
unmodified: `rollout_group` (autoregressive sampling with per-token
log-probs), `token_logprobs` (teacher-forced re-scoring), `grpo_loss`
(clipped surrogate + KL leash against a frozen reference), `Rollout`, and
the checkpoint helpers are all imported directly from
`../../01-language-model-agent/04-rl/core/grpo.py`, not reimplemented. The
grid vocab (`env_text.py`) is built specifically so `PAD_ID == 0` and
`EOS_ID == 1` there too, matching `grpo.py`'s own hardcoded constants --
that is what lets those imported functions run against a completely
different vocabulary with no patching.

What could not be imported unmodified: `rollout_and_score` and `train`,
because `grpo.py`'s own versions hardcode a call to its own arithmetic-
specific `sample_problem`/`compute_reward`. Both are rewritten here with the
grid-world's own reward and problem sampler substituted in; every other line
matches `grpo.py`'s structure, which is the concrete, checkable form of
"changing only the reward function and rollout environment, not the
training algorithm."

Run:
    uv run --group torch python train_grpo.py --steps 200 --seed 0
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-gridworld-baselines" / "core"))
from gridworld import Grid, sample_grid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_text import EOS_ID, PAD_ID, VOCAB, decode, encode, render_prompt
from reward import compute_reward, extract_actions

_GRPO_DIR = Path(__file__).resolve().parents[3] / "01-language-model-agent" / "04-rl" / "core"
sys.path.insert(0, str(_GRPO_DIR))
from grpo import Config, Rollout, Transformer, grpo_loss, rollout_group

assert PAD_ID == 0 and EOS_ID == 1  # required for grpo.py's rollout_group/token_logprobs to apply unmodified


@dataclass
class GridProblem:
    prompt: str
    grid: Grid
    max_steps: int


def sample_problem(rng: random.Random, size: int, num_walls: int, max_steps: int) -> GridProblem:
    grid = sample_grid(rng, size=size, num_walls=num_walls)
    return GridProblem(prompt=render_prompt(grid, max_steps), grid=grid, max_steps=max_steps)


def rollout_and_score(
    model: Transformer,
    problem: GridProblem,
    group_size: int,
    max_new_tokens: int,
    temperature: float,
    device: torch.device,
) -> Rollout | None:
    """Same shape as `grpo.py`'s own `rollout_and_score` -- sample a group,
    score it, group-normalize -- with the grid-world's `compute_reward`
    substituted for arithmetic's. Returns None for a degenerate group
    (every completion scored identically), the same skip rule `grpo.py`
    applies to its own zero-gradient groups."""
    prompt_ids = torch.tensor(encode(problem.prompt), dtype=torch.long)
    tokens, old_logp, lengths = rollout_group(
        model, prompt_ids, group_size, max_new_tokens, temperature, device
    )
    texts = [decode(tokens[i, : lengths[i]].tolist()) for i in range(group_size)]
    scored = [compute_reward(t, problem.grid, problem.max_steps) for t in texts]
    rewards = torch.tensor([s[0] for s in scored], device=device)

    std = rewards.std(unbiased=False)
    if float(std) < 1e-6:
        return None
    advantage = (rewards - rewards.mean()) / (std + 1e-4)

    completion_len = tokens.shape[1]
    idx = torch.arange(completion_len, device=device)[None, :]
    mask = (idx < lengths[:, None].to(device)).float()

    prompt_batch = prompt_ids.unsqueeze(0).repeat(group_size, 1).to(device)
    full_ids = torch.cat([prompt_batch, tokens], dim=1)

    return Rollout(
        full_ids=full_ids,
        old_logp=old_logp,
        mask=mask,
        advantage=advantage,
        rewards=[s[0] for s in scored],
        breakdowns=[s[1] for s in scored],
        prompt_len=prompt_ids.shape[0],
        completion_len=completion_len,
    )


@torch.no_grad()
def generate_greedy(model: Transformer, prompt: str, max_new_tokens: int, device: torch.device) -> str:
    """Deterministic (argmax) decode for evaluation -- separate from the
    temperature-sampled rollouts training learns from, the same distinction
    mission 05's `generate_answer` draws between exploration and scoring."""
    model.eval()
    seq = torch.tensor([encode(prompt)], dtype=torch.long, device=device)
    out_ids: list[int] = []
    for _ in range(max_new_tokens):
        logits, _ = model(seq)
        next_id = int(logits[0, -1, :].argmax())
        if next_id == EOS_ID:
            break
        out_ids.append(next_id)
        seq = torch.cat([seq, torch.tensor([[next_id]], device=device)], dim=1)
    model.train()
    return decode(out_ids)


@torch.no_grad()
def generate_sampled(model: Transformer, prompt: str, max_new_tokens: int, temperature: float, device: torch.device) -> str:
    """Temperature-sampled decode -- the same distribution training's rollouts
    are drawn from, as opposed to `generate_greedy`'s argmax. Kept separate
    so eval can check whether a policy that looks like it is learning under
    sampling (what training actually observes) also looks that way under the
    deterministic decode a deployed policy would actually use."""
    model.eval()
    seq = torch.tensor([encode(prompt)], dtype=torch.long, device=device)
    out_ids: list[int] = []
    for _ in range(max_new_tokens):
        logits, _ = model(seq)
        probs = torch.softmax(logits[0, -1, :] / temperature, dim=-1)
        next_id = int(torch.multinomial(probs, num_samples=1))
        if next_id == EOS_ID:
            break
        out_ids.append(next_id)
        seq = torch.cat([seq, torch.tensor([[next_id]], device=device)], dim=1)
    model.train()
    return decode(out_ids)


def evaluate(
    model: Transformer, size: int, num_walls: int, max_steps: int, trials: int, seed: int, device: torch.device
) -> dict:
    rng = random.Random(seed)
    successes = 0
    for _ in range(trials):
        grid = sample_grid(rng, size=size, num_walls=num_walls)
        prompt = render_prompt(grid, max_steps)
        text = generate_greedy(model, prompt, max_steps, device)
        actions = extract_actions(text)
        reached, _ = grid.run_episode(actions, max_steps)
        successes += int(reached)
    return {"trials": trials, "successes": successes, "success_rate": successes / trials}


def evaluate_sampled(
    model: Transformer,
    size: int,
    num_walls: int,
    max_steps: int,
    trials: int,
    seed: int,
    device: torch.device,
    temperature: float,
) -> dict:
    """Same protocol as `evaluate`, decoding with `generate_sampled` instead
    of `generate_greedy` -- the training-time decode distribution, scored
    the eval way (single draw per grid, not best-of-G)."""
    rng = random.Random(seed)
    successes = 0
    for _ in range(trials):
        grid = sample_grid(rng, size=size, num_walls=num_walls)
        prompt = render_prompt(grid, max_steps)
        text = generate_sampled(model, prompt, max_steps, temperature, device)
        actions = extract_actions(text)
        reached, _ = grid.run_episode(actions, max_steps)
        successes += int(reached)
    return {"trials": trials, "successes": successes, "success_rate": successes / trials}


def dump_examples(model: Transformer, size: int, num_walls: int, max_steps: int, n: int, seed: int, device: torch.device) -> list[dict]:
    """A handful of real greedy-decoded completions on fresh eval grids, for
    a concrete artifact rather than only an aggregate number."""
    rng = random.Random(seed)
    examples = []
    for _ in range(n):
        grid = sample_grid(rng, size=size, num_walls=num_walls)
        prompt = render_prompt(grid, max_steps)
        text = generate_greedy(model, prompt, max_steps, device)
        actions = extract_actions(text)
        reached, steps = grid.run_episode(actions, max_steps)
        examples.append(
            {
                "board": grid.render_text(),
                "raw_completion": text,
                "extracted_actions": actions,
                "reached_goal": reached,
                "steps": steps,
            }
        )
    return examples


def train(args: argparse.Namespace) -> dict:
    device = torch.device(args.device)
    cfg = Config(
        vocab_size=len(VOCAB),
        n_layer=4,
        n_head=4,
        n_kv_head=2,
        d_model=128,
        d_ff=320,
        block_size=args.block_size,
    )
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
            if step % args.log_every == 0:
                print(f"step {step}: every group this step was degenerate, skipping", flush=True)
            continue

        last_loss = 0.0
        for _ in range(args.inner_epochs):
            optimizer.zero_grad(set_to_none=True)
            total_loss = torch.zeros((), device=device)
            for ro in rollouts:
                total_loss = total_loss + grpo_loss(model, ref_model, ro, args.clip_eps, args.kl_beta)
            total_loss = total_loss / len(rollouts)
            total_loss.backward()
            optimizer.step()
            last_loss = float(total_loss.detach())

        if step % args.log_every == 0:
            record = {
                "step": step,
                "mean_reward": sum(step_rewards) / len(step_rewards),
                "mean_format": sum(b["format"] for b in step_breakdowns) / len(step_breakdowns),
                "mean_success": sum(b["success"] for b in step_breakdowns) / len(step_breakdowns),
                "loss": last_loss,
                "groups_used": len(rollouts),
            }
            history.append(record)
            print(json.dumps(record), flush=True)

    elapsed = time.perf_counter() - t0
    eval_result = evaluate(
        model, args.size, args.num_walls, args.max_steps, args.eval_trials, args.seed + 10_000, device
    )
    eval_sampled_result = evaluate_sampled(
        model, args.size, args.num_walls, args.max_steps, args.eval_trials, args.seed + 10_000, device, args.temperature
    )
    examples = dump_examples(model, args.size, args.num_walls, args.max_steps, 8, args.seed + 20_000, device)
    print(f"eval (greedy): {eval_result}", flush=True)
    print(f"eval (sampled, T={args.temperature}): {eval_sampled_result}", flush=True)

    return {
        "seed": args.seed,
        "steps": args.steps,
        "degenerate_steps": degenerate_steps,
        "wall_clock_s": elapsed,
        "history": history,
        "eval_greedy": eval_result,
        "eval_sampled": eval_sampled_result,
        "examples": examples,
    }


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GRPO on the grid-world environment (mission 06 stage 01).")
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--group-size", type=int, default=8)
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
    p.add_argument("--eval-trials", type=int, default=200)
    p.add_argument("--out", type=Path, default=None)
    return p


def main() -> None:
    args = build_argparser().parse_args()
    result = train(args)
    out_path = args.out or (Path(__file__).resolve().parent.parent / "runs" / f"grpo-seed{args.seed}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
