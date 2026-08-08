"""GRPO on the tool-use decision task, reusing mission 01 04-rl's mechanism
unmodified: `rollout_group` (autoregressive sampling with per-token
log-probs), `token_logprobs` (teacher-forced re-scoring), `grpo_loss`
(clipped surrogate + KL leash against a frozen reference), `Rollout`, and
`Config`/`Transformer` are all imported directly from
`../../../01-language-model/04-rl/core/grpo.py`, not reimplemented --
the same import this mission's every prior training stage (01-grpo,
04-minigrid) has used. What changes, exactly as it did moving from stage 01
to stage 04, is the rollout environment and the reward function: this
stage's `env_text.py` (prompt + vocab) and `reward.py` (the tool-cost
decision reward) replace the grid-world's.

`rollout_and_score` and `train` are rewritten here for the same reason
`01-grpo/core/train_grpo.py`'s own versions were: `grpo.py`'s originals
hardcode a call to its own arithmetic-specific `sample_problem`/
`compute_reward`. Every other line matches that file's structure.

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
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_text import DIGIT_LEVELS, EOS_ID, PAD_ID, VOCAB, Problem, decode, encode, sample_problem
from reward import compute_reward, extract_decision

_GRPO_DIR = Path(__file__).resolve().parents[3] / "01-language-model" / "04-rl" / "core"
sys.path.insert(0, str(_GRPO_DIR))
from grpo import Config, Rollout, Transformer, grpo_loss, rollout_group

assert PAD_ID == 0 and EOS_ID == 1  # required for grpo.py's rollout_group/token_logprobs to apply unmodified


def rollout_and_score(
    model: Transformer,
    problem: Problem,
    group_size: int,
    max_new_tokens: int,
    temperature: float,
    device: torch.device,
    reward_rng: random.Random,
) -> Rollout | None:
    """Same shape as `grpo.py`'s own `rollout_and_score` -- sample a group,
    score it, group-normalize -- with this task's `compute_reward`
    substituted for arithmetic's. `reward_rng` is threaded through so the
    per-rollout Bernoulli draw inside `outcome_reward` (see reward.py) is
    reproducible given the caller's seed, the same as `sample_problem`'s own
    draws share one `random.Random` instance across a whole run."""
    prompt_ids = torch.tensor(encode(problem.prompt), dtype=torch.long)
    tokens, old_logp, lengths = rollout_group(
        model, prompt_ids, group_size, max_new_tokens, temperature, device
    )
    texts = [decode(tokens[i, : lengths[i]].tolist()) for i in range(group_size)]
    scored = [compute_reward(t, problem.digit_count, reward_rng) for t in texts]
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
    """Deterministic (argmax) decode for evaluation -- the decode mode a
    deployed policy would actually run, same distinction stage 01 draws."""
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
def generate_sampled(
    model: Transformer, prompt: str, max_new_tokens: int, temperature: float, device: torch.device
) -> str:
    """Temperature-sampled decode -- the distribution training's rollouts are
    drawn from, scored the eval way (one draw per problem, not best-of-G)."""
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
    model: Transformer,
    trials: int,
    seed: int,
    device: torch.device,
    max_new_tokens: int,
    greedy: bool,
    temperature: float = 1.0,
) -> dict:
    """Overall mean reward plus a per-difficulty-level breakdown of which
    decision the policy actually took -- the concrete check for whether it
    learned to *discriminate* by difficulty, not merely to prefer one
    decision on average. A policy that always says TOOL scores exactly the
    always-tool baseline's mean here and shows `answer_rate == 0` at every
    level; a calibrated one shows `answer_rate` falling as digit_count
    rises, roughly at the level this stage's reward crosses (see reward.py's
    `simulated_accuracy` docstring: level 2 to level 3 for TOOL_COST=0.30).
    """
    rng = random.Random(seed)
    reward_sum = 0.0
    per_level = {d: {"n": 0, "answer": 0, "tool": 0, "malformed": 0, "reward_sum": 0.0} for d in DIGIT_LEVELS}
    for _ in range(trials):
        problem = sample_problem(rng)
        if greedy:
            text = generate_greedy(model, problem.prompt, max_new_tokens, device)
        else:
            text = generate_sampled(model, problem.prompt, max_new_tokens, temperature, device)
        reward, breakdown = compute_reward(text, problem.digit_count, rng)
        reward_sum += reward
        lvl = per_level[problem.digit_count]
        lvl["n"] += 1
        lvl["reward_sum"] += reward
        decision = breakdown["decision"]
        if decision == "ANSWER":
            lvl["answer"] += 1
        elif decision == "TOOL":
            lvl["tool"] += 1
        else:
            lvl["malformed"] += 1

    per_level_summary = {}
    for d, v in per_level.items():
        n = v["n"]
        per_level_summary[d] = {
            "n": n,
            "answer_rate": v["answer"] / n if n else None,
            "tool_rate": v["tool"] / n if n else None,
            "malformed_rate": v["malformed"] / n if n else None,
            "mean_reward": v["reward_sum"] / n if n else None,
        }
    return {"trials": trials, "mean_reward": reward_sum / trials, "per_level": per_level_summary}


def dump_examples(model: Transformer, n_per_level: int, seed: int, device: torch.device, max_new_tokens: int) -> list[dict]:
    """A handful of real greedy-decoded completions per difficulty level, for
    a concrete artifact rather than only an aggregate number."""
    rng = random.Random(seed)
    examples = []
    for digit_count in DIGIT_LEVELS:
        for _ in range(n_per_level):
            # Resample until this level comes up -- simplest way to get an
            # even spread across levels from the same sampler every other
            # part of this file uses, at this scale not worth a dedicated
            # per-level sampler.
            problem = sample_problem(rng)
            while problem.digit_count != digit_count:
                problem = sample_problem(rng)
            text = generate_greedy(model, problem.prompt, max_new_tokens, device)
            decision = extract_decision(text)
            examples.append(
                {
                    "prompt": problem.prompt,
                    "raw_completion": text,
                    "decision": decision,
                    "real_target": problem.target,
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
        step_breakdowns: list[dict] = []
        for _ in range(args.prompts_per_step):
            problem = sample_problem(rng)
            ro = rollout_and_score(model, problem, args.group_size, args.max_new_tokens, args.temperature, device, rng)
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
            decided = [b for b in step_breakdowns if b["decision"] is not None]
            record = {
                "step": step,
                "mean_reward": sum(step_rewards) / len(step_rewards),
                "mean_format": sum(b["format"] for b in step_breakdowns) / len(step_breakdowns),
                "mean_outcome": sum(b["outcome"] for b in step_breakdowns) / len(step_breakdowns),
                "tool_rate": (sum(1 for b in decided if b["decision"] == "TOOL") / len(decided)) if decided else None,
                "loss": last_loss,
                "groups_used": len(rollouts),
            }
            history.append(record)
            print(json.dumps(record), flush=True)

    elapsed = time.perf_counter() - t0
    eval_greedy = evaluate(model, args.eval_trials, args.seed + 10_000, device, args.max_new_tokens, greedy=True)
    eval_sampled = evaluate(
        model, args.eval_trials, args.seed + 10_000, device, args.max_new_tokens, greedy=False, temperature=args.temperature
    )
    examples = dump_examples(model, 3, args.seed + 20_000, device, args.max_new_tokens)
    print(f"eval (greedy): mean_reward={eval_greedy['mean_reward']:.4f} per_level={eval_greedy['per_level']}", flush=True)
    print(f"eval (sampled): mean_reward={eval_sampled['mean_reward']:.4f} per_level={eval_sampled['per_level']}", flush=True)

    return {
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
    p = argparse.ArgumentParser(description="GRPO on the tool-use decision task (mission 06 stage 06).")
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--group-size", type=int, default=8)
    p.add_argument("--prompts-per-step", type=int, default=4)
    p.add_argument("--max-new-tokens", type=int, default=8)
    p.add_argument("--block-size", type=int, default=96)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--clip-eps", type=float, default=0.2)
    p.add_argument("--kl-beta", type=float, default=0.04)
    p.add_argument("--inner-epochs", type=int, default=2)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", type=str, default="cpu")
    p.add_argument("--log-every", type=int, default=5)
    p.add_argument("--eval-trials", type=int, default=1000)
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
