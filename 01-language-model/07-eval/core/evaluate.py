"""An honest evaluation harness: perplexity, a small task suite, agent reports.

This is the stage that makes every earlier number in the mission honest. Three
subcommands, each enforcing one discipline the rest of this stage's README
argues for:

`perplexity` — refuses to run without the tokenizer's identity (sha256) and
the context length it scored at, because perplexity is not portable across
either one. A number without both is not reported.

`tasks` — scores a small suite (JSONL, one instance per line) of tasks an
88M-scale model can plausibly attempt. Two instance types:

    {"id": "...", "type": "loglik", "prompt": "...", "choices": ["...", ...],
     "answer_index": 0}
    {"id": "...", "type": "generate", "prompt": "...", "target": "...",
     "max_new_tokens": 16, "temperature": 0.8}

`loglik` instances are scored deterministically (which choice the model
assigns the highest log-probability) and get a bootstrap confidence interval
over which instances happened to be sampled. `generate` instances sample at
temperature > 0, so a single run is a coin flip on that run's seed rather than
a property of the model — `--seeds` (>= 3) is mandatory whenever the suite
contains any, and the script raises rather than silently reporting one seed.

`agent-report` — aggregates harness-disclosed transcripts from stage 06's
agent (a directory of `*.json` files, or one JSONL file). Each transcript
must be:

    {"task_id": "...", "outcome": "success" | "failure", "n_steps": 7,
     "harness": {"tools": [...], "max_steps": 15, "context_budget_tokens": 4096,
                 "model_endpoint": "http://localhost:8000", "temperature": 0.0,
                 "harness_version": "...", "seed": 0},
     "transcript": [...]}   # optional, for inspection

Missing any harness-disclosure field, or fewer than 3 rollouts for any task,
raises rather than summarizing a claim the transcripts cannot support.

Every report requires a named baseline (`--baseline-name/--value/--source`):
per `reference/standards/mission-contract.md`'s acceptance rule 1, a result that beats
nothing is not a result. Every report is written as JSON (`--out`) plus a
human-readable `.md` summary next to it, and includes a `caveats` list stating
what that specific number does not establish.

Run:
    python evaluate.py perplexity --ckpt <ckpt.pt> --tokenizer <tok.json> \\
        --data <val.bin> --baseline-name ... --baseline-value ... --baseline-source ...
    python evaluate.py tasks --ckpt <ckpt.pt> --tokenizer <tok.json> \\
        --suite tasks.jsonl --seeds 5 --baseline-name ... --baseline-value ... \\
        --baseline-source ...
    python evaluate.py agent-report --transcripts <dir-of-json> \\
        --baseline-name ... --baseline-value ... --baseline-source ...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
from tokenizers import Tokenizer

# The model architecture lives in stage 02; importing it rather than
# duplicating it is the point — perplexity must be measured against exactly
# the class that produced the checkpoint, not a re-typed copy of it that could
# silently drift (different RoPE base, different norm epsilon, ...).
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "02-pretrain" / "core")
)
from model import Config, Transformer

MIN_TASK_SEEDS = 3
MIN_AGENT_SEEDS = 3
N_BOOTSTRAP = 2000

REQUIRED_HARNESS_FIELDS = [
    "tools",
    "max_steps",
    "context_budget_tokens",
    "model_endpoint",
    "temperature",
    "harness_version",
    "seed",
]

CAVEATS = {
    "perplexity": [
        ("Comparable only to another run that used the identical tokenizer "
        "(matching sha256 above) and the identical context length; perplexity "
        "is not a cross-tokenizer or cross-context-length metric."),
        ("A held-out split drawn from the same source distribution as training "
        "does not establish generalization to a different domain or a live "
        "workload."),
    ],
    "task_suite": [
        ("A suite sized for an 88M model to plausibly attempt at all is not a "
        "capability benchmark comparable to frontier-model leaderboards."),
        ("The loglik confidence interval reflects instance-sampling uncertainty, "
        "not run-to-run stochasticity; only the generate-task numbers reflect "
        "genuine seed variance."),
    ],
    "agent": [
        ("Success rate is a property of (model, harness) jointly; it says "
        "nothing about how the same model would score under a different tool "
        "set, loop design, or context-management policy."),
        ("If harness_configs_seen > 1, the aggregate mixes non-comparable runs "
        "— read the per-transcript harness blocks in that case, not the "
        "aggregate."),
    ],
}


# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def load_checkpoint(ckpt_path: Path, device: str) -> tuple[Transformer, dict]:
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    cfg = ckpt["config"]
    model = Transformer(Config(**cfg)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, cfg


def checkpoint_identity(ckpt_path: Path, cfg: dict) -> dict:
    return {"path": str(ckpt_path), "sha256": sha256_file(ckpt_path), "config": cfg}


def require_baseline(name: str | None, value: str | None, source: str | None) -> dict:
    """A number with nothing to beat is not a result — see mission-contract.md."""
    if not name or not value or not source:
        raise ValueError(
            "a result without a named baseline is not interpretable "
            "(reference/standards/mission-contract.md, acceptance rule 1): pass "
            "--baseline-name, --baseline-value, and --baseline-source."
        )
    return {"name": name, "value": value, "source": source}


def bootstrap_ci(values: list[float], n_resamples: int = N_BOOTSTRAP, seed: int = 0) -> dict:
    """A 95% bootstrap CI over which instances happened to be sampled.

    Not a substitute for multi-seed variance where sampling is stochastic
    (see `generate` instances below) — this is the uncertainty that remains
    even for a fully deterministic scorer, because the eval set is finite.
    """
    rng = random.Random(seed)
    n = len(values)
    means = sorted(
        statistics.mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(n_resamples)
    )
    lo = means[int(0.025 * n_resamples)]
    hi = means[min(int(0.975 * n_resamples), n_resamples - 1)]
    return {"n": n, "mean": statistics.mean(values), "ci95_lo": lo, "ci95_hi": hi}


def write_report(report: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str))
    summary = render_summary(report)
    summary_path = out.with_suffix(".md")
    summary_path.write_text(summary)
    print(summary)
    print(f"\nwrote {out}")
    print(f"wrote {summary_path}")


def _baseline_line(report: dict) -> str:
    b = report["baseline"]
    return f"baseline     {b['name']} = {b['value']}  ({b['source']})"


def render_summary(report: dict) -> str:
    kind = report["eval_type"]
    lines = [f"# {kind} report — {report['generated_at']}", ""]

    if kind == "perplexity":
        m = report["metric"]
        lines += [
            (f"checkpoint   {report['checkpoint']['path']}"
            f"  (sha256 {report['checkpoint']['sha256'][:12]}...)"),
            (f"tokenizer    {report['tokenizer']['path']}"
            f"  (sha256 {report['tokenizer']['sha256'][:12]}...)"),
            f"context      {m['context_length']} tokens, stride {m['stride']}",
            f"windows      {m['n_windows']}",
            (f"perplexity   {m['perplexity']:.3f}"
            f"  (mean NLL {m['mean_nll']:.4f} +/- {m['std_nll']:.4f})"),
            _baseline_line(report),
        ]

    elif kind == "task_suite":
        lines += [
            f"checkpoint   {report['checkpoint']['path']}",
            f"context      {report['context_length']} tokens",
            f"loglik tasks {report['n_loglik_tasks']}",
        ]
        if report["loglik"]:
            loglik = report["loglik"]
            lines.append(
                f"  accuracy   {loglik['mean']:.3f}"
                f"  95% CI [{loglik['ci95_lo']:.3f}, {loglik['ci95_hi']:.3f}]"
                f"  (bootstrap, n={loglik['n']})"
            )
        lines.append(f"generate tasks {report['n_generate_tasks']}")
        if report["generate"]:
            gen = report["generate"]
            lines.append(
                f"  accuracy   {gen['mean']:.3f} +/- {gen['std']:.3f}"
                f"  across {gen['n_seeds']} seeds  {gen['per_seed_accuracy']}"
            )
        lines.append(_baseline_line(report))

    elif kind == "agent":
        lines += [
            f"transcripts  {report['n_transcripts']} across {report['n_tasks']} tasks",
            f"harness configs seen: {report['harness_configs_seen']}",
        ]
        for task, stats in report["per_task"].items():
            lines.append(
                f"  {task:<24} success {stats['success_rate_mean']:.2f}"
                f" +/- {stats['success_rate_std']:.2f}"
                f"  ({stats['n_rollouts']} rollouts, {stats['steps_mean']:.1f} steps avg)"
            )
        overall = report["overall_success_rate"]
        lines.append(
            f"overall      {overall['mean']:.3f}"
            f"  95% CI [{overall['ci95_lo']:.3f}, {overall['ci95_hi']:.3f}]"
        )
        lines.append(_baseline_line(report))
        if "warning" in report:
            lines += ["", f"WARNING: {report['warning']}"]

    lines += ["", "does not prove:"]
    lines += [f"  - {c}" for c in report["caveats"]]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# perplexity
# --------------------------------------------------------------------------- #


def compute_perplexity(
    model: Transformer,
    data: np.memmap,
    context_length: int,
    device: str,
    stride: int | None,
    limit_windows: int | None,
    batch: int,
) -> dict:
    stride = stride or context_length
    starts = list(range(0, len(data) - context_length - 1, stride))
    if limit_windows:
        starts = starts[:limit_windows]
    if not starts:
        raise ValueError("held-out split is shorter than one context window")

    losses: list[float] = []
    with torch.no_grad():
        for i in range(0, len(starts), batch):
            batch_starts = starts[i : i + batch]
            chunk = np.stack(
                [data[s : s + context_length + 1].astype(np.int64) for s in batch_starts]
            )
            ids = torch.from_numpy(chunk).to(device)
            x, y = ids[:, :-1], ids[:, 1:]
            logits, _ = model(x)
            per_token = torch.nn.functional.cross_entropy(
                logits.reshape(-1, logits.size(-1)), y.reshape(-1), reduction="none"
            )
            per_window = per_token.view(len(batch_starts), -1).mean(dim=1)
            losses.extend(per_window.tolist())

    mean_loss = statistics.mean(losses)
    return {
        "n_windows": len(losses),
        "context_length": context_length,
        "stride": stride,
        "mean_nll": mean_loss,
        "std_nll": statistics.pstdev(losses) if len(losses) > 1 else 0.0,
        "perplexity": math.exp(mean_loss),
    }


def cmd_perplexity(args: argparse.Namespace) -> None:
    model, cfg = load_checkpoint(args.ckpt, args.device)
    context_length = args.context_length or cfg["block_size"]
    data = np.memmap(args.data, dtype=np.uint16, mode="r")
    metric = compute_perplexity(
        model, data, context_length, args.device, args.stride, args.limit_windows, args.batch
    )
    report = {
        "eval_type": "perplexity",
        "generated_at": now_iso(),
        "checkpoint": checkpoint_identity(args.ckpt, cfg),
        "tokenizer": {"path": str(args.tokenizer), "sha256": sha256_file(args.tokenizer)},
        "data": str(args.data),
        "metric": metric,
        "baseline": require_baseline(args.baseline_name, args.baseline_value, args.baseline_source),
        "caveats": CAVEATS["perplexity"],
    }
    write_report(report, args.out)


# --------------------------------------------------------------------------- #
# task suite
# --------------------------------------------------------------------------- #


def _encode(tok: Tokenizer, text: str) -> list[int]:
    return tok.encode(text).ids


def score_choice(
    model: Transformer, tok: Tokenizer, prompt: str, choice: str, context_length: int, device: str
) -> float:
    """Sum log-probability the model assigns `choice` immediately after `prompt`."""
    prompt_ids, choice_ids = _encode(tok, prompt), _encode(tok, choice)
    ids = (prompt_ids + choice_ids)[-context_length:]
    n_choice = min(len(choice_ids), len(ids) - 1)
    if n_choice <= 0:
        return float("-inf")
    idx = torch.tensor([ids], device=device)
    with torch.no_grad():
        logits, _ = model(idx)
    logprobs = torch.log_softmax(logits[0, :-1].float(), dim=-1)
    target = idx[0, 1:]
    token_lp = logprobs.gather(-1, target.unsqueeze(-1)).squeeze(-1)
    return token_lp[-n_choice:].sum().item()


def generate_once(
    model: Transformer,
    tok: Tokenizer,
    prompt: str,
    max_new: int,
    temperature: float,
    context_length: int,
    device: str,
    seed: int,
) -> str:
    gen = torch.Generator(device=device).manual_seed(seed)
    ids = _encode(tok, prompt)[-context_length:]
    idx = torch.tensor([ids], device=device)
    with torch.no_grad():
        for _ in range(max_new):
            logits, _ = model(idx[:, -context_length:])
            probs = torch.softmax(logits[0, -1].float() / max(temperature, 1e-5), dim=-1)
            next_id = torch.multinomial(probs, num_samples=1, generator=gen)
            idx = torch.cat([idx, next_id.view(1, 1)], dim=1)
    return tok.decode(idx[0, len(ids) :].tolist())


def load_task_suite(path: Path) -> list[dict]:
    instances = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    for inst in instances:
        if inst["type"] not in ("loglik", "generate"):
            raise ValueError(f"unknown task type {inst['type']!r} in {inst.get('id')}")
    return instances


def cmd_tasks(args: argparse.Namespace) -> None:
    model, cfg = load_checkpoint(args.ckpt, args.device)
    tok = Tokenizer.from_file(str(args.tokenizer))
    context_length = args.context_length or cfg["block_size"]
    instances = load_task_suite(args.suite)

    loglik = [i for i in instances if i["type"] == "loglik"]
    generate = [i for i in instances if i["type"] == "generate"]

    if generate and (args.seeds is None or args.seeds < MIN_TASK_SEEDS):
        raise ValueError(
            f"suite has {len(generate)} sampled ('generate') task(s); a single-seed "
            f"accuracy is not a result. Pass --seeds >= {MIN_TASK_SEEDS}."
        )

    loglik_correct = []
    for inst in loglik:
        scores = [
            score_choice(model, tok, inst["prompt"], c, context_length, args.device)
            for c in inst["choices"]
        ]
        pred = max(range(len(scores)), key=lambda i: scores[i])
        loglik_correct.append(1.0 if pred == inst["answer_index"] else 0.0)
    loglik_summary = bootstrap_ci(loglik_correct) if loglik_correct else None

    generate_per_seed = []
    for seed in range(args.seeds or 0):
        correct = []
        for inst in generate:
            text = generate_once(
                model,
                tok,
                inst["prompt"],
                inst.get("max_new_tokens", 16),
                inst.get("temperature", 0.8),
                context_length,
                args.device,
                seed,
            )
            correct.append(1.0 if text.strip().startswith(inst["target"].strip()) else 0.0)
        generate_per_seed.append(statistics.mean(correct))

    generate_summary = None
    if generate_per_seed:
        generate_summary = {
            "n_seeds": len(generate_per_seed),
            "per_seed_accuracy": generate_per_seed,
            "mean": statistics.mean(generate_per_seed),
            "std": statistics.pstdev(generate_per_seed) if len(generate_per_seed) > 1 else 0.0,
        }

    report = {
        "eval_type": "task_suite",
        "generated_at": now_iso(),
        "checkpoint": checkpoint_identity(args.ckpt, cfg),
        "tokenizer": {"path": str(args.tokenizer), "sha256": sha256_file(args.tokenizer)},
        "context_length": context_length,
        "suite": str(args.suite),
        "n_loglik_tasks": len(loglik),
        "n_generate_tasks": len(generate),
        "loglik": loglik_summary,
        "generate": generate_summary,
        "baseline": require_baseline(args.baseline_name, args.baseline_value, args.baseline_source),
        "caveats": CAVEATS["task_suite"],
    }
    write_report(report, args.out)


# --------------------------------------------------------------------------- #
# agent report
# --------------------------------------------------------------------------- #


def load_transcripts(path: Path) -> list[dict]:
    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            raise ValueError(f"no *.json transcripts found in {path}")
        return [json.loads(f.read_text()) for f in files]
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def validate_harness_disclosure(transcript: dict) -> None:
    harness = transcript.get("harness")
    if harness is None:
        raise ValueError(
            f"transcript {transcript.get('task_id', '?')!r} has no 'harness' block; an "
            "agent-eval result without harness disclosure cannot be reported (see "
            "07-eval/whose-harness/ for why)."
        )
    missing = [f for f in REQUIRED_HARNESS_FIELDS if f not in harness]
    if missing:
        raise ValueError(
            f"transcript {transcript.get('task_id', '?')!r} is missing harness fields "
            f"{missing}; refusing to summarize an under-disclosed run."
        )


def cmd_agent_report(args: argparse.Namespace) -> None:
    transcripts = load_transcripts(args.transcripts)
    for t in transcripts:
        validate_harness_disclosure(t)

    by_task: dict[str, list[dict]] = defaultdict(list)
    for t in transcripts:
        by_task[t["task_id"]].append(t)

    under_seeded = {task: len(runs) for task, runs in by_task.items() if len(runs) < MIN_AGENT_SEEDS}
    if under_seeded:
        raise ValueError(
            f"tasks with fewer than {MIN_AGENT_SEEDS} rollouts: {under_seeded}; a "
            "single-rollout agent score is not a result."
        )

    per_task = {}
    for task, runs in by_task.items():
        outcomes = [1.0 if r["outcome"] == "success" else 0.0 for r in runs]
        per_task[task] = {
            "n_rollouts": len(runs),
            "success_rate_mean": statistics.mean(outcomes),
            "success_rate_std": statistics.pstdev(outcomes) if len(outcomes) > 1 else 0.0,
            "steps_mean": statistics.mean(r["n_steps"] for r in runs),
        }

    all_outcomes = [1.0 if t["outcome"] == "success" else 0.0 for t in transcripts]
    # `seed` is excluded from the identity check: it is expected, required
    # disclosure (REQUIRED_HARNESS_FIELDS) that legitimately differs across
    # rollouts of the *same* harness run for variance measurement. Every other
    # field differing means the runs are not actually comparable.
    harness_configs = {
        json.dumps({k: v for k, v in t["harness"].items() if k != "seed"}, sort_keys=True)
        for t in transcripts
    }

    report = {
        "eval_type": "agent",
        "generated_at": now_iso(),
        "n_transcripts": len(transcripts),
        "n_tasks": len(by_task),
        "harness_configs_seen": len(harness_configs),
        "harness": (
            transcripts[0]["harness"] if len(harness_configs) == 1 else "VARIES — see per-transcript"
        ),
        "per_task": per_task,
        "overall_success_rate": bootstrap_ci(all_outcomes),
        "baseline": require_baseline(args.baseline_name, args.baseline_value, args.baseline_source),
        "caveats": CAVEATS["agent"],
    }
    if len(harness_configs) > 1:
        report["warning"] = (
            "transcripts were produced under more than one harness configuration; the "
            "aggregate above mixes runs that are not directly comparable to each other. "
            "Report per-configuration or re-run under one harness."
        )
    write_report(report, args.out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _add_baseline_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--baseline-name", required=True)
    p.add_argument("--baseline-value", required=True)
    p.add_argument(
        "--baseline-source",
        required=True,
        help="where the baseline came from: a runs/ entry, a random-choice "
        "calculation, another checkpoint, etc.",
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_ppl = sub.add_parser("perplexity", help="perplexity on a held-out token stream")
    p_ppl.add_argument("--ckpt", type=Path, required=True)
    p_ppl.add_argument(
        "--tokenizer", type=Path, required=True, help="HF tokenizers JSON; identity is recorded"
    )
    p_ppl.add_argument("--data", type=Path, required=True, help="uint16 token stream, e.g. val.bin")
    p_ppl.add_argument("--context-length", type=int, default=None)
    p_ppl.add_argument("--stride", type=int, default=None)
    p_ppl.add_argument("--limit-windows", type=int, default=None)
    p_ppl.add_argument("--batch", type=int, default=8)
    p_ppl.add_argument("--device", default="cuda")
    p_ppl.add_argument("--out", type=Path, default=Path("runs/perplexity-report.json"))
    _add_baseline_args(p_ppl)
    p_ppl.set_defaults(func=cmd_perplexity)

    p_tasks = sub.add_parser("tasks", help="small task suite with seed-measured variance")
    p_tasks.add_argument("--ckpt", type=Path, required=True)
    p_tasks.add_argument("--tokenizer", type=Path, required=True)
    p_tasks.add_argument("--suite", type=Path, required=True, help="JSONL, see module docstring")
    p_tasks.add_argument("--context-length", type=int, default=None)
    p_tasks.add_argument(
        "--seeds",
        type=int,
        default=None,
        help=f"required (>= {MIN_TASK_SEEDS}) if the suite has any 'generate' tasks",
    )
    p_tasks.add_argument("--device", default="cuda")
    p_tasks.add_argument("--out", type=Path, default=Path("runs/task-suite-report.json"))
    _add_baseline_args(p_tasks)
    p_tasks.set_defaults(func=cmd_tasks)

    p_agent = sub.add_parser("agent-report", help="aggregate harness-disclosed agent transcripts")
    p_agent.add_argument(
        "--transcripts", type=Path, required=True, help="directory of *.json transcripts, or one JSONL"
    )
    p_agent.add_argument("--out", type=Path, default=Path("runs/agent-report.json"))
    _add_baseline_args(p_agent)
    p_agent.set_defaults(func=cmd_agent_report)

    return ap


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
