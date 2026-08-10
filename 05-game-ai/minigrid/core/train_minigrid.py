"""GRPO on MiniGrid -- the mission's genuine crossing of the partially-
observed line `does_not_prove` names. Unlike the fully-observed grid-world
(stages 00-01/03), a single open-loop text completion cannot plan a whole
episode here: the agent only ever sees a 7x7 patch in front of itself, so it
must act on what it currently sees and re-observe after every move.

What is reused unmodified: `Config`/`Transformer` from
`../../../01-language-model/rl/core/grpo.py` (the exact same
architecture every other stage in this mission uses), and the k3 KL
estimator / clipped-surrogate math grpo.py's own `grpo_loss` implements --
copied here as `masked_grpo_loss` because `grpo_loss` assumes the
completion is one contiguous span after a fixed prompt (`token_logprobs`
slices `[prompt_len : prompt_len+completion_len]`), which does not hold once
environment-supplied observation text is interleaved between action tokens.
`masked_grpo_loss` takes an explicit boolean mask over arbitrary positions
instead of a contiguous span; every other line matches `grpo_loss`.

What is new: the interleaved rollout loop itself (env truth injected as
non-optimized context, only the single action token per step is sampled and
scored) and the reward, both because MiniGrid's step-by-step interaction has
no analogue in any prior stage of this mission.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

import gymnasium as gym
import minigrid  # noqa: F401  (registers MiniGrid-* environment ids)
import torch
import torch.nn.functional as F
from env_render import EOS_ID, PAD_ID, VOCAB, encode, itos, render_step

_GRPO_DIR = Path(__file__).resolve().parents[3] / "01-language-model" / "04-rl" / "core"
sys.path.insert(0, str(_GRPO_DIR))
from grpo import Config, Transformer

assert PAD_ID == 0 and EOS_ID == 1

_ACTION_TO_ENV = {"F": 2, "L": 0, "R": 1}  # MiniGrid Actions: 0=left 1=right 2=forward


class Episode:
    __slots__ = ("action_positions", "invalid_actions", "old_logp", "token_ids", "total_reward")

    def __init__(self) -> None:
        self.token_ids: list[int] = []
        self.action_positions: list[int] = []
        self.old_logp: list[float] = []
        self.total_reward: float = 0.0
        self.invalid_actions: int = 0


@torch.no_grad()
def rollout_episode(model: Transformer, env: gym.Env, layout_seed: int, max_steps: int, temperature: float, device: torch.device) -> Episode:
    """One full MiniGrid episode. At every step: render the environment's
    OWN observation as text (not generated -- injected, exactly like
    `env.step`'s true return value), append it to the running sequence, one
    forward pass gives the next-token distribution, sample one token as the
    action, execute it (or treat it as a wasted turn if it is not a legal
    action character -- the same real-environment default illegal moves get
    in the fully-observed grid-world), and repeat."""
    model.eval()
    obs, _info = env.reset(seed=layout_seed)
    ep = Episode()
    for step in range(max_steps):
        prompt_ids = encode(render_step(obs, step))
        ep.token_ids.extend(prompt_ids)

        seq = torch.tensor([ep.token_ids], dtype=torch.long, device=device)
        logits, _ = model(seq)
        last_logits = logits[0, -1, :]
        probs = F.softmax(last_logits / temperature, dim=-1)
        action_id = int(torch.multinomial(probs, num_samples=1))
        logp = float(torch.log(probs[action_id] + 1e-12))

        ep.token_ids.append(action_id)
        ep.action_positions.append(len(ep.token_ids) - 1)
        ep.old_logp.append(logp)

        ch = itos[action_id]
        if ch in _ACTION_TO_ENV:
            obs, reward, terminated, truncated, _info = env.step(_ACTION_TO_ENV[ch])
            if terminated:
                ep.total_reward = float(reward)
                break
            if truncated:
                break
        else:
            ep.invalid_actions += 1
    model.train()
    return ep


def masked_grpo_loss(model: Transformer, ref_model: Transformer, episodes: list[Episode], advantages: list[float], clip_eps: float, kl_beta: float, device: torch.device) -> tuple[torch.Tensor, int]:
    """Same math as `grpo.py`'s `grpo_loss` (clipped surrogate + k3 KL
    estimator against a frozen reference), applied position-by-position to
    an explicit list of action-token indices instead of a contiguous
    completion span -- see module docstring for why. Returns the summed
    loss and the total number of action tokens it was summed over, so the
    caller can average across a whole group in one place."""
    total_loss = torch.zeros((), device=device)
    total_positions = 0
    for ep, adv in zip(episodes, advantages):
        if not ep.action_positions:
            continue
        seq = torch.tensor([ep.token_ids], dtype=torch.long, device=device)
        new_logits, _ = model(seq)
        new_logp_full = F.log_softmax(new_logits[0, :-1, :], dim=-1)
        with torch.no_grad():
            ref_logits, _ = ref_model(seq)
            ref_logp_full = F.log_softmax(ref_logits[0, :-1, :], dim=-1)

        targets = seq[0, 1:]
        new_logp_tok = new_logp_full.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
        ref_logp_tok = ref_logp_full.gather(-1, targets.unsqueeze(-1)).squeeze(-1)

        idx = torch.tensor([p - 1 for p in ep.action_positions], device=device)
        new_logp = new_logp_tok[idx]
        ref_logp = ref_logp_tok[idx]
        old_logp = torch.tensor(ep.old_logp, device=device)

        ratio = torch.exp(new_logp - old_logp)
        clipped = torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps)
        surrogate = torch.min(ratio * adv, clipped * adv)

        log_ratio = ref_logp - new_logp
        kl = torch.exp(log_ratio) - log_ratio - 1

        per_token_loss = -surrogate + kl_beta * kl
        total_loss = total_loss + per_token_loss.sum()
        total_positions += len(ep.action_positions)
    return total_loss, total_positions


def evaluate(model: Transformer, env: gym.Env, max_steps: int, trials: int, seed: int, device: torch.device, greedy: bool, temperature: float) -> dict:
    successes = 0
    for i in range(trials):
        model.eval()
        obs, _info = env.reset(seed=seed + i)
        token_ids: list[int] = []
        reached = False
        with torch.no_grad():
            for step in range(max_steps):
                token_ids.extend(encode(render_step(obs, step)))
                seq = torch.tensor([token_ids], dtype=torch.long, device=device)
                logits, _ = model(seq)
                last_logits = logits[0, -1, :]
                if greedy:
                    action_id = int(last_logits.argmax())
                else:
                    probs = F.softmax(last_logits / temperature, dim=-1)
                    action_id = int(torch.multinomial(probs, num_samples=1))
                token_ids.append(action_id)
                ch = itos[action_id]
                if ch in _ACTION_TO_ENV:
                    obs, reward, terminated, truncated, _info = env.step(_ACTION_TO_ENV[ch])
                    if terminated:
                        reached = reward > 0
                        break
                    if truncated:
                        break
        successes += int(reached)
    return {"trials": trials, "successes": successes, "success_rate": successes / trials}


def train(args: argparse.Namespace) -> dict:
    device = torch.device(args.device)
    cfg = Config(vocab_size=len(VOCAB), n_layer=4, n_head=4, n_kv_head=2, d_model=128, d_ff=320, block_size=args.block_size)
    model = Transformer(cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    ref_model = copy.deepcopy(model).to(device)
    ref_model.eval()
    for p in ref_model.parameters():
        p.requires_grad_(False)

    torch.manual_seed(args.seed)
    env = gym.make(args.env_id, max_steps=args.max_steps)

    history: list[dict] = []
    degenerate_steps = 0
    t0 = time.perf_counter()

    for step in range(args.steps):
        layout_seed = args.seed * 100_000 + step
        episodes = [rollout_episode(model, env, layout_seed, args.max_steps, args.temperature, device) for _ in range(args.group_size)]
        rewards = torch.tensor([ep.total_reward for ep in episodes], device=device)
        std = rewards.std(unbiased=False)
        if float(std) < 1e-6:
            degenerate_steps += 1
            continue
        advantages = ((rewards - rewards.mean()) / (std + 1e-4)).tolist()

        last_loss = 0.0
        for _ in range(args.inner_epochs):
            optimizer.zero_grad(set_to_none=True)
            total_loss, total_positions = masked_grpo_loss(model, ref_model, episodes, advantages, args.clip_eps, args.kl_beta, device)
            if total_positions == 0:
                break
            loss = total_loss / total_positions
            loss.backward()
            optimizer.step()
            last_loss = float(loss.detach())

        if step % args.log_every == 0:
            record = {
                "step": step,
                "mean_reward": float(rewards.mean()),
                "success_rate": float((rewards > 0).float().mean()),
                "loss": last_loss,
                "mean_invalid_actions": sum(ep.invalid_actions for ep in episodes) / len(episodes),
            }
            history.append(record)
            print(json.dumps(record), flush=True)

    elapsed = time.perf_counter() - t0
    eval_greedy = evaluate(model, env, args.max_steps, args.eval_trials, args.seed + 10_000, device, greedy=True, temperature=args.temperature)
    eval_sampled = evaluate(model, env, args.max_steps, args.eval_trials, args.seed + 10_000, device, greedy=False, temperature=args.temperature)
    env.close()

    return {
        "env_id": args.env_id,
        "seed": args.seed,
        "steps": args.steps,
        "degenerate_steps": degenerate_steps,
        "wall_clock_s": elapsed,
        "history": history,
        "eval_greedy": eval_greedy,
        "eval_sampled": eval_sampled,
    }


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GRPO on MiniGrid (mission 06 stage 04).")
    p.add_argument("--env-id", type=str, default="MiniGrid-Empty-6x6-v0")
    p.add_argument("--steps", type=int, default=60)
    p.add_argument("--group-size", type=int, default=4)
    p.add_argument("--max-steps", type=int, default=8)
    p.add_argument("--block-size", type=int, default=640)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--clip-eps", type=float, default=0.2)
    p.add_argument("--kl-beta", type=float, default=0.04)
    p.add_argument("--inner-epochs", type=int, default=2)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", type=str, default="cpu")
    p.add_argument("--log-every", type=int, default=5)
    p.add_argument("--eval-trials", type=int, default=100)
    p.add_argument("--out", type=Path, default=None)
    return p


def main() -> None:
    args = build_argparser().parse_args()
    result = train(args)
    out_path = args.out or (Path(__file__).resolve().parent.parent / "runs" / f"minigrid-seed{args.seed}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
