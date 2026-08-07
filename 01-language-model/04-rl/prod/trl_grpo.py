"""GRPO via TRL's `GRPOTrainer` — the production counterpart of `core/grpo.py`.

Same task, same verifiable reward (`compute_reward`, imported unchanged from
`core/grpo.py` so the two files are never comparing different environments),
different amount of code, because TRL hides:

- **Rollout generation.** `core/grpo.py`'s `rollout_group` is a hand-rolled,
  no-KV-cache autoregressive loop. `GRPOTrainer` generates internally (with
  an optional vLLM backend for throughput) and never exposes a token tensor
  to this file.
- **Group-relative advantage.** `(r_i - mean(r)) / (std(r) + eps)` is not
  written anywhere below — it is what `GRPOConfig(num_generations=G)` does
  to whatever `reward_funcs` returns, internally.
- **The clipped surrogate and KL penalty.** `epsilon` and `beta` below are
  `core/grpo.py`'s `clip_eps` and `kl_beta`; the frozen reference-policy
  clone and the log-prob bookkeeping for both are entirely internal.
- **No critic anywhere.** Same as the from-scratch file: there is no
  `value_model` argument on `GRPOConfig`, because GRPO does not have one —
  contrast with TRL's own `PPOTrainer`/`PPOConfig`, which does.

What stays visible either way: the *task* (the dataset and the reward
function are both yours to define) and the *config knobs* that carry
mechanism-level meaning (`num_generations` is G, `epsilon` is the clip
range, `beta` is the KL coefficient). LoRA is wired in here via
`peft.LoraConfig` — this is the parameter-efficient path `core/grpo.py`
explicitly does not use at its scale (see that file's module docstring);
here, against a real pretrained checkpoint, it is the default choice.

No GPU is available in this repo's authoring environment, so this file has
not been run — no reward curve, no wall-clock, no `runs/` entry, and
`status: draft` in the lesson README stays draft until one exists. It is
written to the documented `GRPOTrainer`/`GRPOConfig` API as of TRL's
GRPO support; pin and verify the installed `trl` version before running it,
since trainer config field names have moved between releases.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from datasets import Dataset
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer

# Reuse the exact task and reward function `core/grpo.py` defines, so the two
# files are provably training against the same environment.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))
from grpo import Problem, compute_reward, sample_problem


def build_dataset(n: int, seed: int) -> Dataset:
    rng = random.Random(seed)
    problems: list[Problem] = [sample_problem(rng) for _ in range(n)]
    return Dataset.from_dict(
        {"prompt": [p.prompt for p in problems], "target": [p.target for p in problems]}
    )


def reward_fn(completions: list[str], target: list[int], **_kwargs: object) -> list[float]:
    """The RLVR reward, unchanged from `core.grpo.compute_reward`.

    TRL calls each function in `reward_funcs` once per generated group and
    sums the results; `target` arrives as the dataset column, broadcast by
    TRL to line up one-to-one with `completions`.
    """
    return [compute_reward(completion, t)[0] for completion, t in zip(completions, target)]


def build_trainer(
    model_name: str, output_dir: str, group_size: int, use_lora: bool
) -> GRPOTrainer:
    dataset = build_dataset(n=512, seed=0)

    config = GRPOConfig(
        output_dir=output_dir,
        num_generations=group_size,       # G in core/grpo.py's rollout_group
        epsilon=0.2,                      # clip_eps in core/grpo.py's grpo_loss
        beta=0.04,                        # kl_beta in core/grpo.py's grpo_loss
        temperature=1.0,
        max_completion_length=64,
        per_device_train_batch_size=group_size,
        learning_rate=1e-5,
        logging_steps=1,
        save_steps=50,
        report_to=[],                     # swap in "trackio" once a run actually happens
    )

    # The parameter-efficient path core/grpo.py opts out of at its scale.
    # Against a real pretrained checkpoint, updating every parameter under an
    # online RL loop is the expensive default; LoRA adapters make the memory
    # cost roughly the group-size-driven generation cost, not the model size.
    peft_config = (
        LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM")
        if use_lora
        else None
    )

    return GRPOTrainer(
        model=model_name,
        reward_funcs=[reward_fn],
        args=config,
        train_dataset=dataset,
        peft_config=peft_config,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output-dir", default="grpo-trl-out")
    parser.add_argument("--group-size", type=int, default=8)
    parser.add_argument("--no-lora", action="store_true")
    args = parser.parse_args()

    trainer = build_trainer(args.model, args.output_dir, args.group_size, not args.no_lora)
    trainer.train()


if __name__ == "__main__":
    main()
