"""Rewrite a chat dataset's answers with a teacher model, keeping the prompts.

Sequence-level distillation is SFT where a model wrote the assistant turn. The
question this file exists to make answerable is whether that is better than SFT
where a human wrote it -- and the usual way of asking it is confounded, because
swapping `no_robots` for a model-generated corpus changes the prompts, the task
mix, the length distribution and the answer author all at once, then attributes
the difference to the author.

So the prompts are held fixed. Every arm trains on the same questions in the
same order; only who answered them changes:

    human       no_robots' own assistant turns
    teacher-S   a small instruct model's answers to those prompts
    teacher-L   a large instruct model's answers to those prompts

`--human` writes the first arm by filtering the source dataset and nothing
else, so all three files pass through the same filter and the comparison is not
quietly taken over subsets of different sizes.

Only single-turn rows are kept. In a multi-turn conversation the earlier
assistant turns would stay human-written while the last one was regenerated,
which is neither arm.

The endpoint is any OpenAI-compatible server -- vLLM on the local lane, in
practice. Nothing here is Anthropic-specific and nothing here needs logits;
this is the path available when the teacher is a black box, which is nearly
always.

Usage:
    python generate_traces.py --human --out human.jsonl
    python generate_traces.py --base-url http://localhost:8000/v1 \
        --model Qwen/Qwen2.5-0.5B-Instruct --out teacher-small.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_DATASET = "HuggingFaceH4/no_robots"


def single_turn_rows(dataset: str, split: str, limit: int | None):
    """Rows shaped exactly [user, assistant], optionally behind a system turn.

    Returns (prompt_turns, reference_answer) pairs. The reference is kept so
    `--human` can write the identically-filtered baseline arm from the same
    pass, rather than from a second filter that might drift.
    """
    from datasets import load_dataset

    rows = load_dataset(dataset, split=split)
    kept = []
    for row in rows:
        turns = row["messages"]
        roles = [t["role"] for t in turns]
        if roles in (["user", "assistant"], ["system", "user", "assistant"]):
            kept.append((turns[:-1], turns[-1]["content"]))
        if limit and len(kept) >= limit:
            break
    return kept


def complete(base_url: str, model: str, turns: list[dict], max_tokens: int, timeout: float) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": turns,
            "max_tokens": max_tokens,
            # Greedy. A distillation corpus is not a place to introduce a
            # sampling seed nobody recorded -- the arms have to differ by
            # teacher, not by temperature.
            "temperature": 0.0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read())
    return body["choices"][0]["message"]["content"]


def generate_one(args, item: tuple[list[dict], str]) -> dict | None:
    prompt_turns, _reference = item
    for attempt in range(3):
        try:
            answer = complete(args.base_url, args.model, prompt_turns, args.max_tokens, args.timeout)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == 2:
                return None
            time.sleep(2 * (attempt + 1))
            continue
        if not answer or not answer.strip():
            # An empty completion is a dropped row, not a row with an empty
            # answer. Training on blank assistant turns teaches silence.
            return None
        return {"messages": [*prompt_turns, {"role": "assistant", "content": answer.strip()}]}
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default=DEFAULT_DATASET)
    ap.add_argument("--split", default="train")
    ap.add_argument("--limit", type=int, help="cap rows kept after filtering")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--human", action="store_true", help="write the source answers unchanged")
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--model", help="teacher model id, as the endpoint names it")
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--concurrency", type=int, default=32)
    args = ap.parse_args()

    if not args.human and not args.model:
        raise SystemExit("--model is required unless --human")

    items = single_turn_rows(args.dataset, args.split, args.limit)
    print(f"{args.dataset}/{args.split}: {len(items)} single-turn rows kept", flush=True)

    started = time.perf_counter()
    if args.human:
        written = [
            {"messages": [*turns, {"role": "assistant", "content": reference}]}
            for turns, reference in items
        ]
        dropped = 0
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            results = list(pool.map(lambda it: generate_one(args, it), items))
        written = [r for r in results if r is not None]
        dropped = len(results) - len(written)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as fh:
        for row in written:
            fh.write(json.dumps(row) + "\n")

    elapsed = time.perf_counter() - started
    source = "human (source answers)" if args.human else f"{args.model}"
    print(f"wrote {len(written)} rows to {args.out}  source={source}", flush=True)
    if dropped:
        print(f"dropped {dropped} row(s) that failed or came back empty", flush=True)
    print(f"elapsed {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
