"""Serve the same checkpoint `02-pretrain` trained, with vLLM instead of
`../core/engine.py`.

`model.py`'s `Transformer` is, module for module, a Llama decoder: RMSNorm,
split-half RoPE (`x1, x2 = x.chunk(2, dim=-1)`, which is exactly the
`rotate_half` convention transformers' `apply_rotary_pos_emb` uses — *not*
Meta's original interleaved layout, which is why this conversion needs no
permutation trick; that trick only exists to undo the interleaved-vs-split
mismatch between Meta's original checkpoints and the HF format), SwiGLU, GQA.
vLLM does not run arbitrary `nn.Module`s; it runs a small set of registered
architectures against transformers' config/weight-naming convention. So
"serving with vLLM" is two steps, not one:

1. `convert` — rename our checkpoint's tensors into `LlamaForCausalLM`'s
   naming, write a matching `config.json` + weights to a local HF-format
   checkpoint directory. No weights change value; only names and layout do.
2. `serve` — point vLLM's `LLM` (or the `vllm serve` CLI, for the real
   OpenAI-compatible HTTP server) at that directory.

What vLLM adds beyond `../core/engine.py`, once the checkpoint is in that
directory:
- a fused, CUDA-kernel PagedAttention implementation of the same idea
  `core/engine.py`'s `PagedKVCache`/`BlockAllocator` hand-roll in Python and
  eager PyTorch, including prefix caching and copy-on-write across requests
  that share a prompt prefix — not just a per-request Python loop;
- a real continuous-batching scheduler with priority, preemption, and
  chunked prefill (interleaving a long prompt's prefill with other requests'
  decode steps), not the toy admit-then-loop `ContinuousBatchingEngine` does;
- CUDA graphs, tensor parallelism across GPUs, weight quantization
  (GPTQ/AWQ/FP8/...), and optional speculative decoding — none of which the
  toy engine attempts;
- an OpenAI-compatible HTTP server (`vllm serve <model_dir>`) instead of a
  Python function call returning token ids.

Requires: `pip install vllm transformers safetensors` and a CUDA GPU for the
`serve` step; `convert` needs only `torch`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02-pretrain" / "core"))
from model import Config


def convert_to_hf(checkpoint: Path, out_dir: Path) -> None:
    """Rename `../core/engine.py`'s checkpoint tensors into transformers'
    `LlamaForCausalLM` naming and write a `config.json` + weight file vLLM
    (via transformers) can load directly. Every renamed tensor is copied
    unchanged — this is a relabeling, not a re-derivation.
    """
    ckpt = torch.load(checkpoint, map_location="cpu")
    cfg = Config(**ckpt["config"])
    state = ckpt["model"]

    hf_state: dict[str, torch.Tensor] = {"model.embed_tokens.weight": state["tok.weight"]}
    for i in range(cfg.n_layer):
        src, dst = f"blocks.{i}.", f"model.layers.{i}."
        hf_state[dst + "input_layernorm.weight"] = state[src + "n1.weight"]
        hf_state[dst + "self_attn.q_proj.weight"] = state[src + "attn.q.weight"]
        hf_state[dst + "self_attn.k_proj.weight"] = state[src + "attn.k.weight"]
        hf_state[dst + "self_attn.v_proj.weight"] = state[src + "attn.v.weight"]
        hf_state[dst + "self_attn.o_proj.weight"] = state[src + "attn.o.weight"]
        hf_state[dst + "post_attention_layernorm.weight"] = state[src + "n2.weight"]
        hf_state[dst + "mlp.gate_proj.weight"] = state[src + "mlp.gate.weight"]
        hf_state[dst + "mlp.up_proj.weight"] = state[src + "mlp.up.weight"]
        hf_state[dst + "mlp.down_proj.weight"] = state[src + "mlp.down.weight"]
    hf_state["model.norm.weight"] = state["norm.weight"]
    # `head.weight` is tied to `tok.weight` in model.py
    # (`self.tok.weight = self.head.weight`); transformers ties the same way
    # under `tie_word_embeddings=True` and does not expect a separate
    # `lm_head.weight` tensor in that case, so it is deliberately omitted.

    hf_config = {
        "architectures": ["LlamaForCausalLM"],
        "model_type": "llama",
        "vocab_size": cfg.vocab_size,
        "hidden_size": cfg.d_model,
        "intermediate_size": cfg.d_ff,
        "num_hidden_layers": cfg.n_layer,
        "num_attention_heads": cfg.n_head,
        "num_key_value_heads": cfg.n_kv_head,  # the GQA setting that shrinks vLLM's cache too
        "max_position_embeddings": cfg.block_size,
        "rope_theta": cfg.rope_theta,
        "rms_norm_eps": 1e-6,
        "hidden_act": "silu",
        "tie_word_embeddings": True,
        "attention_bias": False,
        "mlp_bias": False,
        "torch_dtype": "bfloat16",
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "config.json").write_text(json.dumps(hf_config, indent=2))
    try:
        from safetensors.torch import save_file

        save_file(hf_state, out_dir / "model.safetensors")
    except ImportError:
        torch.save(hf_state, out_dir / "pytorch_model.bin")
    print(f"wrote HF-format checkpoint to {out_dir}")
    print(
        "note: this directory still needs a tokenizer to be loadable by name — "
        "export one with ../../01-tokenizer/prod/hf_tokenizer.py and copy "
        "tokenizer.json alongside config.json here."
    )


def serve(model_dir: Path, prompts: list[str]) -> None:
    """Offline generation via vLLM's `LLM` class — the quickest way to check
    the conversion worked. For an actual server, run the CLI instead:

        vllm serve <model_dir> --port 8000

    which exposes the OpenAI-compatible `/v1/completions` and `/v1/chat/completions`
    endpoints backed by the same engine this function drives directly.
    """
    try:
        from vllm import LLM, SamplingParams
    except ImportError as e:
        raise SystemExit(
            "vLLM is not installed (`pip install vllm`), or no CUDA GPU is available. "
            "This step, unlike `convert`, needs both."
        ) from e

    llm = LLM(model=str(model_dir), dtype="bfloat16")
    sampling = SamplingParams(temperature=0.0, max_tokens=64)
    for out in llm.generate(prompts, sampling):
        print(out.prompt, "->", out.outputs[0].text)


def bench(model_dir: Path, prompt_len: int, max_new_tokens: int, counts: list[int], eager: bool) -> None:
    """Run `../core/engine.py bench`'s concurrency sweep against vLLM, with
    every parameter held identical so the two tables can be read side by side.

    The core engine's `paged + continuous` arm measures flat aggregate
    throughput from 1 to 16 concurrent requests and blames the missing fused
    kernel. That is an explanation, not a measurement, until the same sweep
    runs against an engine that *has* one. This is that sweep.

    Two things are deliberately switched off, because leaving them on would
    answer a different question:

    - **Prefix caching.** Every request here sends the identical prompt
      `range(prompt_len)`, exactly as the core bench does. vLLM would notice
      and serve 15 of 16 prefills from cache, which is a real feature and a
      completely different effect from batching. The core engine has no such
      cache, so comparing against it with prefix caching on would credit the
      kernel for a saving the kernel did not make.
    - **EOS.** `ignore_eos=True` forces every request to emit exactly
      `max_new_tokens`, matching the core engine's unconditional loop. Without
      it, an early stop would shorten a request and inflate tokens/second.
    - **The tokenizer.** Prompts go in as token ids and results come out as
      token ids, exactly as in `core/engine.py`. `skip_tokenizer_init=True`
      keeps detokenization out of the measured interval so both tables are
      timing the same work.

    `eager` selects whether CUDA graphs are allowed. Running the sweep both
    ways separates two things that are easy to conflate: batching many
    sequences into one kernel, and removing per-launch overhead from the
    kernels themselves.
    """
    try:
        from vllm import LLM, SamplingParams
        from vllm.inputs import TokensPrompt
    except ImportError as e:
        raise SystemExit("vLLM is not installed (`pip install vllm`), or no CUDA GPU is available.") from e

    llm = LLM(
        model=str(model_dir),
        dtype="bfloat16",
        enable_prefix_caching=False,
        skip_tokenizer_init=True,
        enforce_eager=eager,
        gpu_memory_utilization=0.6,
        max_model_len=prompt_len + max_new_tokens + 8,
    )
    sampling = SamplingParams(temperature=0.0, max_tokens=max_new_tokens, ignore_eos=True)
    prompt = TokensPrompt(prompt_token_ids=list(range(prompt_len)))

    llm.generate([prompt], sampling, use_tqdm=False)  # warm up compilation and allocation

    print(f"\nvLLM, {'eager' if eager else 'CUDA graphs'}, prefix caching off")
    print(f"{'requests':>10}{'aggregate tok/s':>18}{'wall-clock':>14}")
    for n in counts:
        t0 = time.perf_counter()
        outputs = llm.generate([prompt] * n, sampling, use_tqdm=False)
        elapsed = time.perf_counter() - t0
        emitted = sum(len(o.outputs[0].token_ids) for o in outputs)
        print(f"{n:>10}{emitted / elapsed:>18.1f}{elapsed:>13.3f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    conv = sub.add_parser("convert", help="convert a stage-02 checkpoint to an HF Llama checkpoint dir")
    conv.add_argument("checkpoint", type=Path, help="e.g. ../../02-pretrain/ckpt/ckpt.pt")
    conv.add_argument("out_dir", type=Path)

    srv = sub.add_parser("serve", help="load the converted checkpoint into vLLM and generate")
    srv.add_argument("model_dir", type=Path)
    srv.add_argument("--prompt", action="append", dest="prompts", default=None)

    bch = sub.add_parser("bench", help="run core/engine.py's concurrency sweep against vLLM")
    bch.add_argument("model_dir", type=Path)
    bch.add_argument("--prompt-len", type=int, default=64)
    bch.add_argument("--max-new-tokens", type=int, default=128)
    bch.add_argument("--requests", type=int, nargs="+", default=[1, 2, 4, 8, 16])
    bch.add_argument("--eager", action="store_true", help="disable CUDA graphs")

    args = ap.parse_args()
    if args.command == "convert":
        convert_to_hf(args.checkpoint, args.out_dir)
    elif args.command == "serve":
        serve(args.model_dir, args.prompts or ["Once upon a time"])
    elif args.command == "bench":
        bench(args.model_dir, args.prompt_len, args.max_new_tokens, args.requests, args.eager)


if __name__ == "__main__":
    main()
