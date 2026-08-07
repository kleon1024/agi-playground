"""Run the speedrun checkpoint through EleutherAI's lm-evaluation-harness.

`core/evaluate.py` scores this stage's own tasks with a hand-rolled loop; this
file instead wraps the same checkpoint in the interface a standard harness
expects, and asks what the standard tool gives you that a hand-rolled loop
should not bother re-implementing.

**What lm-evaluation-harness gives you.** A task is a declarative spec (dataset
+ prompt template + scoring rule: exact match, or log-likelihood comparison
for multiple choice) rather than a hand-written scoring loop, which is what
makes it possible to run hundreds of community-maintained static benchmarks
against a new model by writing an adapter once — not one scoring function per
benchmark. It handles few-shot prompt construction, stderr computation, and
result aggregation across tasks for you, and results are directly comparable
to every other model anyone has run through the same harness version and task
revision (subject to this stage's harness-disclosure caveat below).

**Where it stops.** It scores one static task at a time: a fixed prompt in, a
score out, no notion of a multi-turn trajectory, no tool calls, no environment
state that changes between steps. It has no built-in concept of "the harness
is part of the score" — that argument, and the transcript-level aggregation it
implies, is what `core/evaluate.py agent-report` exists for. Running a model
through lm-eval-harness tells you nothing about how it behaves as an agent.

**The adapter below.** lm-eval-harness assumes a model that can score arbitrary
(context, continuation) pairs and generate until a stop string; `HFLM` does
this against a HuggingFace model. `SpeedrunLM` implements the same three
methods against `02-pretrain/core/model.py`'s `Transformer` instead, so
standard loglikelihood-scored tasks (cloze completion, multiple choice) can run
against the exact checkpoint `core/evaluate.py` measures perplexity on — not a
re-exported or re-converted copy of it. It is intentionally unbatched: no
shared-prefix KV-cache reuse across continuations, correctness over speed,
matching this repo's `core/`-vs-`prod/` split (the third-party dependency
carries the engineering; ours stays simple enough to read end to end). That is
fine at the small `--limit` values an 88M from-scratch model is evaluated at —
most tasks tuned for frontier models will floor at chance for a model this
size regardless of harness quality, so pick tasks accordingly (see the README).

Requires `lm-eval` (`pip install lm-eval`), a prod/-only dependency:
core/evaluate.py has no dependency on this package or file.

Run:
    python lm_eval.py --ckpt ../02-pretrain/ckpt/ckpt.pt \\
        --tokenizer ../01-tokenizer/tokenizer_hf.json \\
        --tasks lambada_openai --limit 200 --out lm_eval_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

# This file is named lm_eval.py, the same name as the third-party package it
# imports below -- Python puts this script's own directory at the front of
# sys.path, which shadows the real package with this file. Drop it before
# importing anything, or `import lm_eval` below silently imports itself.
_here = str(Path(__file__).resolve().parent)
sys.path = [p for p in sys.path if p not in ("", _here)]

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02-pretrain" / "core"))
from model import Config, Transformer

try:
    import lm_eval
    from lm_eval.api.instance import Instance
    from lm_eval.api.model import LM
    from lm_eval.api.registry import register_model
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SystemExit(
        "lm-evaluation-harness is not installed (prod/-only dependency): "
        "pip install lm-eval"
    ) from exc

from tokenizers import Tokenizer


def load_checkpoint(ckpt_path: Path, device: str) -> tuple[Transformer, dict]:
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    cfg = ckpt["config"]
    model = Transformer(Config(**cfg)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, cfg


@register_model("speedrun-transformer")
class SpeedrunLM(LM):
    """Adapter from our from-scratch Transformer to lm-eval-harness's LM interface.

    Implements the three methods every lm-eval-harness task type needs:
    `loglikelihood` (multiple choice / cloze scoring), `loglikelihood_rolling`
    (whole-string log-likelihood, used by perplexity-style tasks), and
    `generate_until` (greedy generation to a stop string, used by exact-match
    tasks). See `docs/model_guide.md` in lm-evaluation-harness for the
    contract this is implementing against.
    """

    def __init__(self, ckpt: Path, tokenizer: Path, device: str = "cuda", batch_size: int = 1):
        super().__init__()
        self.model, self.config = load_checkpoint(ckpt, device)
        self.tok = Tokenizer.from_file(str(tokenizer))
        # LM.device is a read-only property backed by _device in the
        # installed lm-eval-harness version -- self.device = device raises.
        self._device = device
        self.block_size = self.config["block_size"]
        self._batch_size = batch_size

    @property
    def batch_size(self) -> int:
        return self._batch_size

    @property
    def eot_token_id(self) -> int:
        # No dedicated end-of-text token was trained. The document separator
        # (see 02-pretrain/core/prepare_data.py) is the closest analogue and is
        # only consulted by the harness to pad loglikelihood_rolling windows.
        return self.config["vocab_size"] - 1

    def tok_encode(self, text: str) -> list[int]:
        return self.tok.encode(text).ids

    def _score(self, context: str, continuation: str) -> tuple[float, bool]:
        """Summed log-probability the model assigns `continuation` given `context`."""
        ctx_ids, cont_ids = self.tok_encode(context), self.tok_encode(continuation)
        ids = (ctx_ids + cont_ids)[-self.block_size :]
        n_cont = min(len(cont_ids), len(ids) - 1)
        if n_cont <= 0:
            return float("-inf"), False
        idx = torch.tensor([ids], device=self.device)
        with torch.no_grad():
            logits, _ = self.model(idx)
        logprobs = torch.log_softmax(logits[0, :-1].float(), dim=-1)
        target = idx[0, 1:]
        token_lp = logprobs.gather(-1, target.unsqueeze(-1)).squeeze(-1)
        cont_lp = token_lp[-n_cont:]
        is_greedy = bool((logprobs[-n_cont:].argmax(-1) == target[-n_cont:]).all().item())
        return cont_lp.sum().item(), is_greedy

    def loglikelihood(self, requests: list[Instance]) -> list[tuple[float, bool]]:
        return [self._score(*req.args) for req in requests]

    def loglikelihood_rolling(self, requests: list[Instance]) -> list[tuple[float, bool]]:
        # No held-out context: score each full string against an empty prefix.
        return [self._score("", req.args[0]) for req in requests]

    def generate_until(self, requests: list[Instance]) -> list[str]:
        out = []
        for req in requests:
            context, gen_kwargs = req.args
            until = gen_kwargs.get("until", [])
            max_new = gen_kwargs.get("max_gen_toks", 64)
            ids = self.tok_encode(context)[-self.block_size :]
            idx = torch.tensor([ids], device=self.device)
            text = ""
            with torch.no_grad():
                for _ in range(max_new):
                    logits, _ = self.model(idx[:, -self.block_size :])
                    next_id = int(logits[0, -1].argmax())
                    idx = torch.cat(
                        [idx, torch.tensor([[next_id]], device=self.device)], dim=1
                    )
                    text = self.tok.decode(idx[0, len(ids) :].tolist())
                    if any(u in text for u in until):
                        break
            for u in until:
                text = text.split(u)[0]
            out.append(text)
        return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--ckpt", type=Path, required=True)
    ap.add_argument("--tokenizer", type=Path, required=True)
    ap.add_argument(
        "--tasks",
        nargs="+",
        required=True,
        help="e.g. lambada_openai hellaswag arc_easy — pick tasks an 88M base model "
        "can do above chance; most instruction or multi-step reasoning tasks will "
        "floor at random for a model this size regardless of harness quality",
    )
    ap.add_argument(
        "--limit", type=int, default=None, help="cap examples per task; unset runs the full task"
    )
    ap.add_argument("--num-fewshot", type=int, default=0)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", type=Path, default=Path("lm_eval_report.json"))
    args = ap.parse_args()

    lm = SpeedrunLM(args.ckpt, args.tokenizer, device=args.device)
    results = lm_eval.simple_evaluate(
        model=lm,
        tasks=args.tasks,
        num_fewshot=args.num_fewshot,
        limit=args.limit,
        log_samples=False,
    )

    report = {
        "harness": "lm-evaluation-harness",
        "harness_stops_at": (
            "static, single-turn tasks scored by log-likelihood or exact-match "
            "generation. No agent loop, no tool use, no multi-turn trajectory "
            "scoring — see core/evaluate.py agent-report for that half of the eval."
        ),
        "checkpoint": str(args.ckpt),
        "tokenizer": str(args.tokenizer),
        "tasks": args.tasks,
        "num_fewshot": args.num_fewshot,
        "limit": args.limit,
        "results": results["results"],
        "versions": results.get("versions", {}),
        "n-samples": results.get("n-samples", {}),
    }
    args.out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report["results"], indent=2, default=str))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
