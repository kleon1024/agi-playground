"""Call the same hosted VLM API stage 02 used, on stage 03's real-photo eval
set instead of stage 00's synthetic one. Reuses stage 02's `png_encode.py`
unchanged (it is a generic row-major-RGB-to-PNG encoder, not specific to
synthetic images) and the identical model/endpoint/retry logic.

Run:
    export OPENROUTER_API_KEY=...
    uv run python call_hosted_api.py --resume
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

STAGE02_CORE = Path(__file__).resolve().parents[2] / "02-report" / "core"
sys.path.insert(0, str(STAGE02_CORE))
from png_encode import encode_png

DATA_DIR = Path(__file__).resolve().parents[2] / "03-real-photo-task" / "data" / "raw"
OUT_PATH = Path(__file__).resolve().parent.parent / "runs" / "hosted-api-raw.jsonl"
MODEL = "openai/gpt-4o-mini"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 4


def load_eval_rows() -> list[dict]:
    eval_raw = [json.loads(line) for line in (DATA_DIR / "eval.jsonl").read_text().splitlines() if line]
    rows = []
    for ex_idx, ex in enumerate(eval_raw):
        for qa_idx, qa in enumerate(ex["qa"]):
            rows.append(
                {
                    "row_id": f"{ex_idx}-{qa_idx}",
                    "pixels_rgb": ex["pixels_rgb"],
                    "width": ex["width"],
                    "height": ex["height"],
                    "type": qa["type"],
                    "question": qa["question"],
                    "answer": qa["answer"],
                }
            )
    return rows


def call_api(row: dict, api_key: str) -> dict:
    pixels = [tuple(p) for p in row["pixels_rgb"]]
    png = encode_png(pixels, row["width"], row["height"])
    import base64

    b64 = base64.b64encode(png).decode()
    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": row["question"] + " Answer with a single word or number only, no punctuation.",
                    },
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
                ],
            }
        ],
        "usage": {"include": True},
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_error = e
            time.sleep(2**attempt)
    raise RuntimeError(f"row {row['row_id']} failed after {MAX_RETRIES} attempts: {last_error}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true", help="skip row_ids already present in the output file")
    ap.add_argument("--limit", type=int, default=None, help="stop after N new calls (for a pilot run)")
    args = ap.parse_args()

    api_key = os.environ["OPENROUTER_API_KEY"]
    rows = load_eval_rows()

    done_ids: set[str] = set()
    if args.resume and OUT_PATH.exists():
        for line in OUT_PATH.read_text().splitlines():
            if line:
                done_ids.add(json.loads(line)["row_id"])
        print(f"resuming: {len(done_ids)} rows already done")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    todo = [r for r in rows if r["row_id"] not in done_ids]
    if args.limit:
        todo = todo[: args.limit]
    print(f"total eval rows: {len(rows)}  to call now: {len(todo)}")

    t0 = time.perf_counter()
    with OUT_PATH.open("a") as out:
        for i, row in enumerate(todo):
            resp = call_api(row, api_key)
            pred_raw = resp["choices"][0]["message"]["content"]
            record = {
                "row_id": row["row_id"],
                "type": row["type"],
                "question": row["question"],
                "answer": row["answer"],
                "pred_raw": pred_raw,
                "cost_usd": resp["usage"]["cost"],
                "prompt_tokens": resp["usage"]["prompt_tokens"],
                "completion_tokens": resp["usage"]["completion_tokens"],
                "model": MODEL,
            }
            out.write(json.dumps(record) + "\n")
            out.flush()
            if (i + 1) % 50 == 0 or i == len(todo) - 1:
                elapsed = time.perf_counter() - t0
                print(f"  {i + 1}/{len(todo)} done, {elapsed:.0f}s elapsed")

    print(f"wrote results to {OUT_PATH}")


if __name__ == "__main__":
    main()
