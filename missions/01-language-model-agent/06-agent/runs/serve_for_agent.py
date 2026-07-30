"""Minimal stdlib-only OpenAI-chat-completions-compatible server for the
stage-06 agent harness, wrapping the stage-03 SFT checkpoint directly (no
vLLM: unavailable on this box, and stage 05 already covers that lane).

Reuses two pieces verbatim from this repo rather than reinventing them:
`Config`/`Transformer` from `02-pretrain/core/model.py`, and the ChatML
rendering + temperature/top-k sampling loop from `03-sft/core/sft.py`'s
`render_prompt`/`generate` (copied here, not imported, so this scratch
directory does not have to drag in `train.py`'s training-loop dependencies
just to sample from a checkpoint).

One deliberate deviation from the wire protocol: `harness.py`'s
`OpenAICompatibleBackend.generate` hardcodes `"temperature": 0` in every
request (see its line ~297) -- there is no way to get seed/temperature
variation across rollouts by honoring the request body. This server ignores
the client-supplied temperature and samples with the temperature/seed fixed
at process startup instead, exactly so a fresh seed per rollout is possible;
the effective values are logged and belong in the harness-disclosure block of
any transcript this server helped produce.

Run:
    python server.py --checkpoint <ckpt.pt> --tokenizer <tokenizer_hf.json> \\
        --seed 1001 --temperature 0.7 --port 8811
"""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import torch
from model import Config, Transformer
from tokenizers import Tokenizer
from torch.nn import functional as F

IM_START = 16385
IM_END = 16386


def render_prompt(turns: list[dict], tok: Tokenizer) -> list[int]:
    """Copied from `03-sft/core/sft.py`'s `render_prompt`/`render_and_mask`
    (labels dropped: this is inference, not training)."""
    ids: list[int] = []
    for turn in turns:
        header = tok.encode(f"{turn['role']}\n").ids
        body = tok.encode(turn["content"]).ids
        tail = tok.encode("\n").ids
        ids += [IM_START] + header + body + [IM_END] + tail
    ids += [IM_START] + tok.encode("assistant\n").ids
    return ids


@torch.no_grad()
def generate(
    model: Transformer,
    tok: Tokenizer,
    prompt_ids: list[int],
    max_new_tokens: int,
    device: str,
    block_size: int,
    temperature: float,
    top_k: int,
    stop_strings: list[str],
) -> str:
    """`03-sft/core/sft.py`'s `generate`, plus a stop-string check after every
    token -- the backend half of the grounding rule `harness.py` documents:
    stop generating at the boundary the caller asked for, cheaply, and let
    `enforce_grounding`'s unconditional truncation be the layer that actually
    guarantees it."""
    model.eval()
    ids = list(prompt_ids)
    vocab_size = tok.get_vocab_size()
    for _ in range(max_new_tokens):
        window = ids[-block_size:]
        x = torch.tensor([window], dtype=torch.long, device=device)
        logits, _ = model(x)
        logits = logits[0, -1] / max(temperature, 1e-6)
        if top_k:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits = logits.masked_fill(logits < v[-1], float("-inf"))
        probs = F.softmax(logits, dim=-1)
        next_id = int(torch.multinomial(probs, 1).item())
        ids.append(next_id)
        if next_id == IM_END:
            break
        text_so_far = tok.decode([t for t in ids[len(prompt_ids):] if t < vocab_size])
        for stop in stop_strings:
            idx = text_so_far.find(stop)
            if idx != -1:
                return text_so_far[:idx]
    return tok.decode([t for t in ids[len(prompt_ids):] if t < vocab_size])


def load_model(checkpoint: str, device: str) -> tuple[Transformer, Config]:
    ckpt = torch.load(checkpoint, map_location=device, weights_only=False)
    cfg = Config(**ckpt["config"])
    model = Transformer(cfg)
    model.load_state_dict(ckpt["model"])
    model.to(device).eval()
    return model, cfg


def make_handler(model, cfg, tok, device, temperature, top_k, max_new_tokens, model_name):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):
            print(f"[server] {fmt % a}", flush=True)

        def do_POST(self):
            if self.path.rstrip("/") != "/v1/chat/completions":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            messages = body["messages"]
            stop = body.get("stop") or []

            prompt_ids = render_prompt(messages, tok)
            t0 = time.time()
            content = generate(
                model, tok, prompt_ids, max_new_tokens, device, cfg.block_size,
                temperature, top_k, stop,
            )
            dt = time.time() - t0
            print(f"[server] generated {len(content)} chars in {dt:.2f}s", flush=True)

            response = {
                "id": "chatcmpl-stage06",
                "object": "chat.completion",
                "created": 0,
                "model": model_name,
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": content},
                     "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": len(prompt_ids), "completion_tokens": 0,
                          "total_tokens": len(prompt_ids)},
            }
            payload = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--port", type=int, default=8811)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--model-name", default="stage03-sft")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    tok = Tokenizer.from_file(args.tokenizer)
    model, cfg = load_model(args.checkpoint, args.device)
    print(
        f"[server] loaded {args.checkpoint} on {args.device}, seed={args.seed}, "
        f"temperature={args.temperature}, top_k={args.top_k}",
        flush=True,
    )

    handler = make_handler(
        model, cfg, tok, args.device, args.temperature, args.top_k,
        args.max_new_tokens, args.model_name,
    )
    httpd = HTTPServer(("localhost", args.port), handler)
    print(f"[server] listening on http://localhost:{args.port}/v1", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
