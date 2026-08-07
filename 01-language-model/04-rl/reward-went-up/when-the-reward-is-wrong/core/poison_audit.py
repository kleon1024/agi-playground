"""The reward curve lies twice: when the labels are wrong, and when they
are late.

The parent chapter showed a rising reward curve lying when the policy
hacks a *correct* reward. This audit covers the other two ways the curve
can lie, both of them in the label supply rather than the model: the
reward labels are poisoned (a fraction of correctness labels flipped, the
RLHF analogue of preference-label poisoning) or delayed (the ground truth
drifts and the label used at training time reflects the world as it was L
steps ago). A stale label is a poisoned label whose error rate is the
drift — so both are one failure family, and the detection is the same:
the training reward and a clean held-out verifier are allowed to
disagree, and disagreement above a threshold stops the run.

Measured here, on the real 04-rl char-level GRPO trainer, CPU-only:

  1. Warm start. The parent chapter's Exercise 1, executed: a handful of
     supervised steps on well-formed `<think>/<answer>` examples so GRPO
     can fire at all (the base run measured 200/200 degenerate groups from
     a cold start).
  2. Advantage distortion. Real rollouts from the warm-started policy,
     scored under clean labels and under flipped labels at flip rates
     0.05 / 0.1 / 0.2: how often the poison changes which completion the
     group pushes up, and how often the pushed completion is wrong.
  3. Training comparison. The same 30-step GRPO budget, clean reward vs a
     10%-flipped reward, same seed and problem stream: each arm's training
     reward and its held-out true correctness on the same completions.
  4. Delay. The ground truth drifts and the label lags; the run measures
     the lagged label's agreement with current truth as a function of lag
     and drift rate, so the delay is priced as a poison rate.

Deterministic (single seed), CPU-only, about 8 minutes. No dataset and no
external checkpoint are needed: the warm start is trained here on
hand-written examples over the task's own character vocabulary.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import random
import sys
from pathlib import Path

import torch

_GRPO = Path(__file__).resolve().parents[3] / "core" / "grpo.py"
spec = importlib.util.spec_from_file_location("grpo", _GRPO)
grpo = importlib.util.module_from_spec(spec)
sys.modules["grpo"] = grpo
spec.loader.exec_module(grpo)


def cfg():
    return grpo.Config(
        vocab_size=len(grpo.VOCAB),
        n_layer=4,
        n_head=4,
        n_kv_head=2,
        d_model=128,
        d_ff=320,
        block_size=96,
    )


# ---------------------------------------------------------------------------
# 1. Warm start: supervised steps on well-formed examples, so the policy
# emits <think>/<answer> often enough for GRPO groups to become
# non-degenerate. Hand-written, over the task's own char vocabulary.
# ---------------------------------------------------------------------------
WARM_EXAMPLES = [
    ("Q: What is 3 + 4? A:", "<think>3 plus 4 is 7.</think><answer>7</answer>"),
    ("Q: What is 9 - 5? A:", "<think>9 minus 5 is 4.</think><answer>4</answer>"),
    ("Q: What is 6 * 7? A:", "<think>6 times 7 is 42.</think><answer>42</answer>"),
    ("Q: What is 2 + 8? A:", "<think>2 plus 8 is 10.</think><answer>10</answer>"),
    ("Q: What is 12 - 4? A:", "<think>12 minus 4 is 8.</think><answer>8</answer>"),
    ("Q: What is 5 * 3? A:", "<think>5 times 3 is 15.</think><answer>15</answer>"),
    ("Q: What is 7 + 6? A:", "<think>7 plus 6 is 13.</think><answer>13</answer>"),
    ("Q: What is 20 - 9? A:", "<think>20 minus 9 is 11.</think><answer>11</answer>"),
    ("Q: What is 4 * 4? A:", "<think>4 times 4 is 16.</think><answer>16</answer>"),
    ("Q: What is 10 + 5? A:", "<think>10 plus 5 is 15.</think><answer>15</answer>"),
    ("Q: What is 8 - 3? A:", "<think>8 minus 3 is 5.</think><answer>5</answer>"),
    ("Q: What is 2 * 9? A:", "<think>2 times 9 is 18.</think><answer>18</answer>"),
    ("Q: What is 15 + 6? A:", "<think>15 plus 6 is 21.</think><answer>21</answer>"),
    ("Q: What is 18 - 7? A:", "<think>18 minus 7 is 11.</think><answer>11</answer>"),
    ("Q: What is 3 * 8? A:", "<think>3 times 8 is 24.</think><answer>24</answer>"),
    ("Q: What is 11 + 9? A:", "<think>11 plus 9 is 20.</think><answer>20</answer>"),
    ("Q: What is 14 - 6? A:", "<think>14 minus 6 is 8.</think><answer>8</answer>"),
    ("Q: What is 7 * 5? A:", "<think>7 times 5 is 35.</think><answer>35</answer>"),
    ("Q: What is 16 + 4? A:", "<think>16 plus 4 is 20.</think><answer>20</answer>"),
    ("Q: What is 13 - 8? A:", "<think>13 minus 8 is 5.</think><answer>5</answer>"),
    ("Q: What is 9 * 2? A:", "<think>9 times 2 is 18.</think><answer>18</answer>"),
    ("Q: What is 1 + 1? A:", "<think>1 plus 1 is 2.</think><answer>2</answer>"),
    ("Q: What is 17 - 9? A:", "<think>17 minus 9 is 8.</think><answer>8</answer>"),
    ("Q: What is 6 * 6? A:", "<think>6 times 6 is 36.</think><answer>36</answer>"),
]


def warm_start(device: torch.device, steps: int, seed: int) -> tuple:
    """Train the char-level policy on the well-formed examples; return the
    model and its optimizer state so GRPO resumes from here."""
    torch.manual_seed(seed)
    model = grpo.Transformer(cfg()).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    sequences = []
    for prompt, completion in WARM_EXAMPLES:
        ids = grpo.encode(prompt + completion) + [grpo.EOS_ID]
        sequences.append(ids)
    for step in range(steps):
        opt.zero_grad(set_to_none=True)
        total = torch.zeros((), device=device)
        for ids in sequences:
            ids = torch.tensor(ids, dtype=torch.long, device=device)[: cfg().block_size + 1]
            if len(ids) < 4:
                continue
            _, loss = model(ids[:-1].unsqueeze(0), ids[1:].unsqueeze(0))
            total = total + loss
        (total / len(sequences)).backward()
        opt.step()
    return model, opt


def fire_rate(model, device: torch.device, rng: random.Random, n: int = 24) -> dict:
    """Fraction of sampled completions that carry the tags GRPO's format
    reward requires — the warm start's only acceptance bar."""
    tagged = total = 0
    with torch.no_grad():
        for _ in range(n):
            problem = grpo.sample_problem(rng)
            prompt_ids = torch.tensor(grpo.encode(problem.prompt), dtype=torch.long)
            tokens, _, lengths = grpo.rollout_group(
                model, prompt_ids, 4, 56, 1.0, device
            )
            for i in range(tokens.shape[0]):
                text = grpo.decode(tokens[i, : lengths[i]].tolist())
                total += 1
                if "<think>" in text and "<answer>" in text:
                    tagged += 1
    return {"tagged": tagged, "total": total,
            "rate": tagged / max(1, total)}


# ---------------------------------------------------------------------------
# 2. Poisoned labels: flip a completion's correctness verdict with prob p.
# The flip is seeded by (problem, completion) so the clean and poisoned arms
# see identical completions and differ only in the labels.
# ---------------------------------------------------------------------------
def poisoned_rewards(texts, targets, p: float, flip_rng: random.Random) -> list[float]:
    """compute_reward with each completion's correctness flipped with
    probability p; the format component is untouched."""
    out = []
    for text, target in zip(texts, targets):
        f = grpo.format_reward(text)
        c = grpo.correctness_reward(text, target)
        if flip_rng.random() < p:
            c = 1.0 - c
        out.append(0.2 * f + 1.0 * c)
    return out


def measure_distortion(
    model, device: torch.device, seed: int, group_size: int,
    max_new_tokens: int, n_groups: int,
) -> dict:
    """Real rollouts scored under clean labels and under flipped labels at
    three flip rates. The distortion is how often the poison changes which
    completion the group pushes to the top advantage, and how often the
    pushed completion is wrong."""
    base_rng = random.Random(seed)
    rows = []
    for _ in range(n_groups):
        problem = grpo.sample_problem(base_rng)
        prompt_ids = torch.tensor(grpo.encode(problem.prompt), dtype=torch.long)
        tokens, _, lengths = grpo.rollout_group(
            model, prompt_ids, group_size, max_new_tokens, 1.0, device
        )
        texts = [grpo.decode(tokens[i, : lengths[i]].tolist()) for i in range(group_size)]
        true_correct = [grpo.correctness_reward(t, problem.target) for t in texts]
        clean = [0.2 * grpo.format_reward(t) + 1.0 * c
                 for t, c in zip(texts, true_correct)]
        rows.append({
            "texts": texts, "clean": clean, "true": true_correct,
            "target": problem.target,
        })

    out = {}
    for p in (0.05, 0.1, 0.2):
        flip_rng = random.Random(seed)
        pushed_wrong = changed = total = 0
        poisoned_all: list[float] = []
        true_all: list[float] = []
        for row in rows:
            poisoned = poisoned_rewards(
                row["texts"], [row["target"]] * len(row["texts"]), p, flip_rng
            )
            total += 1
            c_best = max(range(len(row["clean"])), key=lambda i: row["clean"][i])
            p_best = max(range(len(poisoned)), key=lambda i: poisoned[i])
            poisoned_all += poisoned
            true_all += row["true"]
            if c_best != p_best:
                changed += 1
                if row["true"][p_best] == 0.0:
                    pushed_wrong += 1
        out[p] = {
            "groups": total,
            "changed_argmax": changed,
            "changed_share": changed / max(1, total),
            "pushed_wrong": pushed_wrong,
            "pushed_wrong_share": pushed_wrong / max(1, total),
            "spearman": _spearman(poisoned_all, true_all),
        }
    return out


def _spearman(xs: list[float], ys: list[float]) -> float:
    """Rank correlation over a paired list; ties broken by index."""
    order_x = sorted(range(len(xs)), key=lambda i: (xs[i], i))
    order_y = sorted(range(len(ys)), key=lambda i: (ys[i], i))
    rank_x = {i: r for r, i in enumerate(order_x)}
    rank_y = {i: r for r, i in enumerate(order_y)}
    n = len(xs)
    if n < 2:
        return 0.0
    d2 = sum((rank_x[i] - rank_y[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1))


# ---------------------------------------------------------------------------
# 3. Training comparison: the same 30-step GRPO budget under a clean reward
# and a 10%-flipped reward, same seed and problem stream.
# ---------------------------------------------------------------------------
def run_grpo(
    model, opt, device: torch.device, seed: int, steps: int,
    group_size: int, prompts_per_step: int, max_new_tokens: int,
    inner_epochs: int, kl_beta: float, clip_eps: float, p: float,
) -> list[dict]:
    """GRPO for `steps`, scoring with flipped labels at rate p (p=0.0 is the
    clean arm). Records the arm's training reward AND held-out true
    correctness on the same completions."""
    ref_model = copy.deepcopy(model).to(device)
    ref_model.eval()
    for param in ref_model.parameters():
        param.requires_grad_(False)
    rng = random.Random(seed)
    history = []
    for step in range(steps):
        rollouts = []
        step_rewards: list[float] = []
        step_true: list[float] = []
        for _ in range(prompts_per_step):
            problem = grpo.sample_problem(rng)
            prompt_ids = torch.tensor(grpo.encode(problem.prompt), dtype=torch.long)
            tokens, old_logp, lengths = grpo.rollout_group(
                model, prompt_ids, group_size, max_new_tokens, 1.0, device
            )
            texts = [grpo.decode(tokens[i, : lengths[i]].tolist())
                     for i in range(group_size)]
            true_correct = [grpo.correctness_reward(t, problem.target) for t in texts]
            flip_rng = random.Random(seed * 100003 + step * 7 + _ * 11)
            rewards = poisoned_rewards(texts, [problem.target] * group_size, p, flip_rng)
            r_t = torch.tensor(rewards, device=device)
            std = r_t.std(unbiased=False)
            if float(std) < 1e-6:
                continue
            advantage = (r_t - r_t.mean()) / (std + 1e-4)
            completion_len = tokens.shape[1]
            idx = torch.arange(completion_len, device=device)[None, :]
            mask = (idx < lengths[:, None].to(device)).float()
            prompt_batch = prompt_ids.unsqueeze(0).repeat(group_size, 1).to(device)
            full_ids = torch.cat([prompt_batch, tokens], dim=1)
            rollouts.append(
                grpo.Rollout(
                    full_ids=full_ids, old_logp=old_logp, mask=mask,
                    advantage=advantage, rewards=rewards,
                    breakdowns=[{}] * group_size,
                    prompt_len=prompt_ids.shape[0], completion_len=completion_len,
                )
            )
            step_rewards += rewards
            step_true += true_correct
        if not rollouts:
            history.append({"step": step, "mean_reward": float("nan"),
                            "mean_true": float("nan"), "groups_used": 0})
            continue
        for _ in range(inner_epochs):
            opt.zero_grad(set_to_none=True)
            total_loss = torch.zeros((), device=device)
            for ro in rollouts:
                total_loss = total_loss + grpo.grpo_loss(
                    model, ref_model, ro, clip_eps, kl_beta
                )
            (total_loss / len(rollouts)).backward()
            opt.step()
        history.append({
            "step": step,
            "mean_reward": sum(step_rewards) / len(step_rewards),
            "mean_true": sum(step_true) / len(step_true),
            "groups_used": len(rollouts),
        })
    return history


# ---------------------------------------------------------------------------
# 4. Delay: the ground truth drifts and the label lags. A stale label is a
# poisoned label whose error rate is the drift times the lag.
# ---------------------------------------------------------------------------
def delay_agreement(drift: float, lag: int, trials: int = 4000, seed: int = 0) -> float:
    """Share of labels computed `lag` steps ago that still match the truth
    now, when the truth flips with probability `drift` per step."""
    rng = random.Random(seed)
    agree = 0
    for _ in range(trials):
        truth = rng.random() < 0.5
        lagged = truth
        for _ in range(lag):
            if rng.random() < drift:
                lagged = not lagged
        if lagged == truth:
            agree += 1
    return agree / trials


def run(args) -> None:
    device = torch.device(args.device)
    print("poisoned-reward audit (real 04-rl GRPO trainer, CPU, "
          f"seed {args.seed}):")
    print()

    model, opt = warm_start(device, args.warm_steps, args.seed)
    fire = fire_rate(model, device, random.Random(args.seed))
    print("  1. warm start, executed:")
    print(f"     {args.warm_steps} supervised steps over "
          f"{len(WARM_EXAMPLES)} hand-written examples")
    print(f"     tag fire rate: {fire['rate']:.1%} "
          f"({fire['tagged']}/{fire['total']} completions carry "
          f"<think>/<answer>)")
    print()

    dist = measure_distortion(
        model, device, args.seed, args.group_size, args.max_new_tokens,
        args.distortion_groups,
    )
    print("  2. advantage distortion, executed (real rollouts, "
          f"{args.distortion_groups} groups x {args.group_size}):")
    for p, d in dist.items():
        print(f"     flip rate {p:.0%}: {d['changed_share']:.1%} of groups "
              f"change which completion is pushed "
              f"({d['changed_argmax']}/{d['groups']}); "
              f"{d['pushed_wrong_share']:.1%} push a wrong completion; "
              f"poisoned-vs-true rank corr {d['spearman']:.3f}")
    print()

    clean = run_grpo(
        copy.deepcopy(model), copy.deepcopy(opt), device, args.seed,
        args.rl_steps, args.group_size, args.prompts_per_step,
        args.max_new_tokens, args.inner_epochs, args.kl_beta, args.clip_eps,
        0.0,
    )
    poisoned = run_grpo(
        copy.deepcopy(model), copy.deepcopy(opt), device, args.seed,
        args.rl_steps, args.group_size, args.prompts_per_step,
        args.max_new_tokens, args.inner_epochs, args.kl_beta, args.clip_eps,
        args.flip_rate,
    )
    print(f"  3. training comparison, executed ({args.rl_steps} GRPO steps, "
          f"clean vs {args.flip_rate:.0%}-flipped, same seed and problems):")
    print("     step | clean reward | clean true | poison reward | poison true")
    for c, p in zip(clean, poisoned):
        if c["groups_used"] or p["groups_used"]:
            print(f"     {c['step']:>4} | {c['mean_reward']:11.3f} | "
                  f"{c['mean_true']:10.3f} | {p['mean_reward']:12.3f} | "
                  f"{p['mean_true']:11.3f}")
    print()

    print("  4. delay priced as poison, executed (truth flips with prob "
          "drift per step; the label lags L steps):")
    print("     drift | lag | label agreement | label error rate")
    for drift in (0.02, 0.05):
        for lag in (1, 5, 10, 20):
            agree = delay_agreement(drift, lag)
            print(f"     {drift:.0%}  | {lag:>3} | {agree:14.1%} | "
                  f"{1 - agree:15.1%}")
    print()
    print("  verdict: a rising reward curve is evidence only when the labels")
    print("  it rises against are trusted. A clean held-out verifier that")
    print("  disagrees with the training reward is the detection; a stale")
    print("  label is a poisoned label with error rate = drift x lag, and")
    print("  the budget belongs in the label pipeline, not the optimizer.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--warm-steps", type=int, default=250)
    ap.add_argument("--group-size", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=56)
    ap.add_argument("--distortion-groups", type=int, default=20)
    ap.add_argument("--rl-steps", type=int, default=30)
    ap.add_argument("--prompts-per-step", type=int, default=4)
    ap.add_argument("--inner-epochs", type=int, default=2)
    ap.add_argument("--kl-beta", type=float, default=0.04)
    ap.add_argument("--clip-eps", type=float, default=0.2)
    ap.add_argument("--flip-rate", type=float, default=0.1)
    args = ap.parse_args()
    run(args)


if __name__ == "__main__":
    main()
