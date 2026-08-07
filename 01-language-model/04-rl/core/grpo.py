"""GRPO from scratch, on a verifiable arithmetic task (RLVR).

This is Group Relative Policy Optimization (Shao et al., 2024, DeepSeekMath):
PPO's clipped surrogate and KL penalty, unchanged, with the critic deleted.
PPO estimates the advantage `A(s,a) = Q(s,a) - V(s)` from a learned value
model trained alongside the policy. GRPO instead samples a *group* of `G`
completions to the same prompt and uses the group's own reward statistics as
the baseline:

    A_i = (r_i - mean(r_1..r_G)) / (std(r_1..r_G) + eps)

No value network is trained, saved, or even instantiated anywhere in this
file. That is the entire contribution over PPO — everything downstream (the
clipped objective, the KL penalty against a frozen reference policy) is
copied from PPO verbatim. The trade: `G`x more generation per update step,
paid for by the memory a critic would have occupied.

The environment is Reinforcement Learning from Verifiable Rewards (RLVR):
the reward is a rule, not a learned reward model. Given "what is 13 * 17?",
the reward function can just compute 221 and compare — no reward-model
training, no reward-model drift, no separate hacking surface for that model.
The reward here has two parts, both explained in the lesson README:
a *format* reward (did the completion wrap its reasoning in <think></think>
and its answer in <answer></answer>) and a *correctness* reward (does the
extracted answer match the ground truth). Read `compute_reward` for exactly
how they combine, and the README for how each half gets gamed in practice.

Scale and fine-tuning choice, stated plainly: this trains a randomly
initialized, few-hundred-thousand-parameter Transformer (imported from
`02-pretrain/core/model.py`, not redefined) with a small character-level
vocabulary built for this task alone — not the BPE tokenizer or a pretrained
checkpoint from earlier stages. There is no SFT stage behind this policy;
it is a cold start, in the DeepSeek-R1-Zero sense, chosen so the file can be
read start to finish without a GPU or an upstream checkpoint. Every update
here is **full fine-tuning** of every parameter, not LoRA: at this scale
(well under a million parameters) full fine-tuning is cheap and keeps the
GRPO update-rule code free of low-rank adapter bookkeeping. `prod/trl_grpo.py`
is where LoRA is wired in, at the scale (a real pretrained checkpoint) where
it actually matters.

No GPU is available while writing this file, so nothing here has been run:
no reward curve, no wall-clock, no `runs/` entry. That is what `status: draft`
in the README means, and it stays draft until a `runs/` entry exists.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.nn import functional as F

# Reuse the model architecture from stage 02 instead of redefining it — GRPO
# changes the objective the policy is trained against, not the policy's shape.
_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "02-pretrain" / "core"
sys.path.insert(0, str(_MODEL_DIR))
from model import Config, Transformer

# --------------------------------------------------------------------------
# A closed, character-level vocabulary for this task only. Full BPE (stage 01)
# is overkill for a domain this narrow, and using it would tie this lesson's
# vocab_size to a tokenizer.json this file would then have to load — a
# self-contained alphabet keeps the RL mechanics the only thing under test.
# --------------------------------------------------------------------------
_SPECIALS = ["<pad>", "<eos>"]
_CHARS = sorted(
    set(
        "0123456789+-*/=?:.,() \n"
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "<>_"
    )
)
VOCAB = _SPECIALS + _CHARS
stoi = {ch: i for i, ch in enumerate(VOCAB)}
itos = {i: ch for ch, i in stoi.items()}
PAD_ID = stoi["<pad>"]
EOS_ID = stoi["<eos>"]


def encode(text: str) -> list[int]:
    return [stoi[ch] for ch in text]


def decode(ids: list[int]) -> str:
    """Render ids back to text, stopping at the first <eos> and dropping pad."""
    out = []
    for i in ids:
        if i == EOS_ID:
            break
        if i == PAD_ID:
            continue
        out.append(itos[i])
    return "".join(out)


# --------------------------------------------------------------------------
# The verifiable environment: an arithmetic question with a programmatically
# checkable answer. This is the entire "reward model" — a Python function.
# --------------------------------------------------------------------------
OPS = {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b}


@dataclass
class Problem:
    prompt: str
    target: int


def sample_problem(rng: random.Random) -> Problem:
    a, b = rng.randint(1, 20), rng.randint(1, 20)
    op = rng.choice(list(OPS))
    prompt = f"Q: What is {a} {op} {b}? A:"
    return Problem(prompt=prompt, target=OPS[op](a, b))


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_ANSWER_RE = re.compile(r"<answer>\s*(-?\d+)\s*</answer>")
_WELL_FORMED_RE = re.compile(r"^\s*<think>.*?</think>\s*<answer>-?\d+</answer>\s*$", re.DOTALL)


def format_reward(text: str) -> float:
    """Reward the *shape* of the completion, independent of correctness.

    1.0  — exactly a <think> block immediately followed by an <answer> block.
    0.5  — both tags are present, but out of order, duplicated, or padded with
           stray text — a real attempt at the format, imperfectly executed.
    0.2  — only one of the two tags shows up.
    0.0  — neither tag appears at all.

    This partial-credit ladder exists because a 0/1 format reward gives the
    policy no gradient signal on the way to getting the format right — see
    the README's "why the format reward is needed" section for what breaks
    without it, and "how it gets gamed" for what breaks *with* it.
    """
    has_think = bool(_THINK_RE.search(text))
    has_answer = bool(_ANSWER_RE.search(text))
    if _WELL_FORMED_RE.match(text):
        return 1.0
    if has_think and has_answer:
        return 0.5
    if has_think or has_answer:
        return 0.2
    return 0.0


def correctness_reward(text: str, target: int) -> float:
    match = _ANSWER_RE.search(text)
    if not match:
        return 0.0
    return 1.0 if int(match.group(1)) == target else 0.0


def compute_reward(
    text: str, target: int, format_weight: float = 0.2, correctness_weight: float = 1.0
) -> tuple[float, dict[str, float]]:
    """Additive reward, R1-style: format nudges toward the shape, correctness
    is what actually matters. Additive (not multiplicative) so an imperfectly
    formatted-but-correct answer still scores above a well-formatted wrong
    one, which is the ordering a verifier should enforce.
    """
    f = format_reward(text)
    c = correctness_reward(text, target)
    total = format_weight * f + correctness_weight * c
    return total, {"format": f, "correctness": c, "total": total}


# --------------------------------------------------------------------------
# Rollout: sample a group of G completions for one prompt, recording the
# log-prob of every sampled token under the *current* (pre-update) policy —
# this is pi_theta_old in the GRPO/PPO objective below.
# --------------------------------------------------------------------------
def rollout_group(
    model: Transformer,
    prompt_ids: torch.Tensor,
    group_size: int,
    max_new_tokens: int,
    temperature: float,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Autoregressively sample `group_size` completions for one prompt.

    No KV cache: every step recomputes attention over the whole sequence so
    far. That is O(n^2) per rollout instead of O(n), and is the first thing
    to fix for anything past this lesson's toy scale (see track 06, serving)
    — reading clearly, not throughput, is the point of this file.

    Returns (tokens, old_logp, lengths):
      tokens    [G, T] generated ids, right-padded with PAD_ID
      old_logp  [G, T] log-prob of each generated token under this policy
      lengths   [G]    true completion length (including the trailing <eos>)
    """
    model.eval()
    with torch.no_grad():
        seq = prompt_ids.unsqueeze(0).repeat(group_size, 1).to(device)
        tokens = torch.full((group_size, max_new_tokens), PAD_ID, dtype=torch.long, device=device)
        old_logp = torch.zeros(group_size, max_new_tokens, device=device)
        lengths = torch.full((group_size,), max_new_tokens, dtype=torch.long, device=device)
        done = torch.zeros(group_size, dtype=torch.bool, device=device)

        used = max_new_tokens
        for t in range(max_new_tokens):
            logits, _ = model(seq)
            probs = F.softmax(logits[:, -1, :] / temperature, dim=-1)
            sampled = torch.multinomial(probs, num_samples=1).squeeze(-1)
            step_logp = torch.log(probs.gather(-1, sampled.unsqueeze(-1)).squeeze(-1) + 1e-12)

            # Sequences that already emitted <eos> get frozen at pad, and
            # contribute nothing to old_logp — the completion mask (built
            # from `lengths` at scoring time) excludes these positions anyway.
            sampled = torch.where(done, torch.full_like(sampled, PAD_ID), sampled)
            tokens[:, t] = sampled
            old_logp[:, t] = torch.where(done, torch.zeros_like(step_logp), step_logp)

            newly_done = (sampled == EOS_ID) & (~done)
            lengths = torch.where(newly_done, torch.full_like(lengths, t + 1), lengths)
            done = done | newly_done

            seq = torch.cat([seq, sampled.unsqueeze(1)], dim=1)
            if bool(done.all()):
                used = t + 1
                break
    model.train()
    return tokens[:, :used], old_logp[:, :used], lengths.clamp(max=used)


def token_logprobs(
    model: Transformer, full_ids: torch.Tensor, prompt_len: int, completion_len: int
) -> torch.Tensor:
    """Log-prob of each completion token under `model`, via one teacher-forced
    forward pass over the full (prompt + completion) sequence.

    `full_ids[:, t]` is predicted by the logits at position `t-1`, so the
    completion — which starts at index `prompt_len` in the full sequence —
    is predicted by logits starting at index `prompt_len - 1`.
    """
    logits, _ = model(full_ids)
    logp = F.log_softmax(logits[:, :-1, :], dim=-1)
    targets = full_ids[:, 1:]
    tok_logp = logp.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
    start = prompt_len - 1
    return tok_logp[:, start : start + completion_len]


@dataclass
class Rollout:
    full_ids: torch.Tensor          # [G, P+L]
    old_logp: torch.Tensor          # [G, L]
    mask: torch.Tensor              # [G, L] 1.0 on real completion tokens, 0.0 on padding
    advantage: torch.Tensor         # [G]
    rewards: list[float]
    breakdowns: list[dict[str, float]]
    prompt_len: int
    completion_len: int


def rollout_and_score(
    model: Transformer,
    problem: Problem,
    group_size: int,
    max_new_tokens: int,
    temperature: float,
    device: torch.device,
) -> Rollout | None:
    """Roll out a group, score it against the verifier, and group-normalize.

    Returns None when the group is degenerate — every completion scored
    identically, so std=0 and (r_i - mean)/std is 0/0. This is not rare: an
    easy prompt the policy already answers correctly every time produces
    exactly this, and the GRPO update contributes nothing from that group
    (skipping it is the standard fix, alongside adding an epsilon to std).
    """
    prompt_ids = torch.tensor(encode(problem.prompt), dtype=torch.long)
    tokens, old_logp, lengths = rollout_group(
        model, prompt_ids, group_size, max_new_tokens, temperature, device
    )
    texts = [decode(tokens[i, : lengths[i]].tolist()) for i in range(group_size)]
    scored = [compute_reward(t, problem.target) for t in texts]
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


def grpo_loss(
    model: Transformer, ref_model: Transformer, rollout: Rollout, clip_eps: float, kl_beta: float
) -> torch.Tensor:
    """The clipped, group-relative objective — PPO's surrogate with the
    critic's advantage swapped for the group-normalized one, plus a KL leash
    against the frozen reference policy. Nothing here trains a value model.
    """
    new_logp = token_logprobs(model, rollout.full_ids, rollout.prompt_len, rollout.completion_len)
    with torch.no_grad():
        ref_logp = token_logprobs(
            ref_model, rollout.full_ids, rollout.prompt_len, rollout.completion_len
        )

    ratio = torch.exp(new_logp - rollout.old_logp)
    clipped = torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps)
    adv = rollout.advantage[:, None]
    # Pessimistic bound: for adv > 0 the objective stops rewarding a ratio
    # past 1+eps, so one good group can't push the policy arbitrarily hard.
    surrogate = torch.min(ratio * adv, clipped * adv)

    # k3 KL estimator (Schulman, "Approximating KL Divergence"): unbiased and
    # always >= 0, unlike the naive (new_logp - ref_logp) difference, which
    # is unbiased but can go negative and add noisy sign-flipping gradient.
    log_ratio = ref_logp - new_logp
    kl = torch.exp(log_ratio) - log_ratio - 1

    per_token_loss = -surrogate + kl_beta * kl
    return (per_token_loss * rollout.mask).sum() / rollout.mask.sum().clamp(min=1)


def save_checkpoint(path: str, model: Transformer, optimizer: torch.optim.Optimizer, step: int) -> None:
    torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(), "step": step}, path)


def load_checkpoint(path: str, model: Transformer, optimizer: torch.optim.Optimizer) -> int:
    ckpt = torch.load(path, map_location="cpu")
    model.load_state_dict(ckpt["model"])
    optimizer.load_state_dict(ckpt["optimizer"])
    return ckpt["step"]


def train(args: argparse.Namespace) -> None:
    device = torch.device(args.device)
    cfg = Config(
        vocab_size=len(VOCAB),
        n_layer=4,
        n_head=4,
        n_kv_head=2,
        d_model=128,
        d_ff=320,
        block_size=96,
    )
    model = Transformer(cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    start_step = 0
    if Path(args.checkpoint).exists():
        start_step = load_checkpoint(args.checkpoint, model, optimizer)
        print(f"resumed from {args.checkpoint} at step {start_step}", flush=True)

    # The frozen reference policy the KL penalty is measured against. Cloned
    # once, here, before any GRPO update — never touched by the optimizer.
    ref_model = copy.deepcopy(model).to(device)
    ref_model.eval()
    for p in ref_model.parameters():
        p.requires_grad_(False)

    rng = random.Random(args.seed)
    history: list[dict] = []
    if Path(args.history).exists():
        history = json.loads(Path(args.history).read_text())

    for step in range(start_step, args.steps):
        rollouts = []
        step_rewards: list[float] = []
        step_breakdowns: list[dict[str, float]] = []
        for _ in range(args.prompts_per_step):
            problem = sample_problem(rng)
            ro = rollout_and_score(
                model, problem, args.group_size, args.max_new_tokens, args.temperature, device
            )
            if ro is None:
                continue
            rollouts.append(ro)
            step_rewards.extend(ro.rewards)
            step_breakdowns.extend(ro.breakdowns)

        if not rollouts:
            print(f"step {step}: every group this step was degenerate, skipping", flush=True)
            continue

        # `inner_epochs` > 1 replays the same rollouts against the objective
        # more than once — the point at which `ratio` actually leaves 1.0 and
        # the clip starts doing work. At inner_epochs=1, old==new at the
        # first (only) gradient step and clipping is a no-op by construction.
        last_loss = 0.0
        for _ in range(args.inner_epochs):
            optimizer.zero_grad(set_to_none=True)
            total_loss = torch.zeros((), device=device)
            for ro in rollouts:
                total_loss = total_loss + grpo_loss(model, ref_model, ro, args.clip_eps, args.kl_beta)
            total_loss = total_loss / len(rollouts)
            total_loss.backward()
            optimizer.step()
            last_loss = float(total_loss)

        if step % args.log_every == 0:
            record = {
                "step": step,
                "mean_reward": sum(step_rewards) / len(step_rewards),
                "mean_format": sum(b["format"] for b in step_breakdowns) / len(step_breakdowns),
                "mean_correctness": sum(b["correctness"] for b in step_breakdowns)
                / len(step_breakdowns),
                "loss": last_loss,
                "groups_used": len(rollouts),
            }
            history.append(record)
            print(json.dumps(record), flush=True)

        if step % args.checkpoint_every == 0 or step == args.steps - 1:
            save_checkpoint(args.checkpoint, model, optimizer, step + 1)
            Path(args.history).write_text(json.dumps(history, indent=2))

    print(f"done: {args.steps} steps, history in {args.history}", flush=True)


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GRPO from scratch on a verifiable arithmetic task.")
    p.add_argument("command", choices=["train"])
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--group-size", type=int, default=8, help="G: completions sampled per prompt")
    p.add_argument("--prompts-per-step", type=int, default=4)
    p.add_argument("--max-new-tokens", type=int, default=56)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--clip-eps", type=float, default=0.2)
    p.add_argument("--kl-beta", type=float, default=0.04)
    p.add_argument("--inner-epochs", type=int, default=2)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", type=str, default="cpu")
    p.add_argument("--checkpoint", type=str, default="grpo.ckpt.pt")
    p.add_argument("--history", type=str, default="grpo_history.json")
    p.add_argument("--log-every", type=int, default=5)
    p.add_argument("--checkpoint-every", type=int, default=20)
    return p


def main() -> None:
    args = build_argparser().parse_args()
    if args.command == "train":
        train(args)


if __name__ == "__main__":
    main()
