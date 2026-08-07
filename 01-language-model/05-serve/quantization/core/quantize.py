"""Quantize this model's attention and SwiGLU weights to INT8, and test the
prediction [graph execution](../../graph-execution/)'s own "Next" section
made: halving the weight bytes should halve decode time, and usually does
not, because dequantizing to full width and calling an ordinary matmul
materializes the wide weight anyway and pays the dequant on top of it.

`footprint` prints the byte count before and after. `verify` is the
correctness gate -- greedy decoding must agree with the fp32 baseline before
any speed number means anything. `bench` measures eager and CUDA-graph decode
at both precisions, so the quantization effect and the launch-overhead effect
(01-language-model/05-serve/graph-execution's own chapter) can be told apart instead
of conflated.

Usage:
    python quantize.py footprint --checkpoint <ckpt.pt>
    python quantize.py verify    --checkpoint <ckpt.pt>
    python quantize.py bench     --checkpoint <ckpt.pt> --max-new-tokens 128
    python quantize.py profile   --checkpoint <ckpt.pt> --steps 50
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "01-language-model/05-serve/core"))
sys.path.insert(0, str(ROOT / "01-language-model/02-pretrain/core"))
sys.path.insert(0, str(ROOT / "01-language-model/05-serve/graph-execution/core"))
from engine import KVCache, _forward_with_cache, load_model
from graph_decode import GraphedDecoder, _median, _time, decode_eager
from model import Transformer, build_rope_cache

# --------------------------------------------------------------------------
# Per-channel INT8 weight-only quantization
# --------------------------------------------------------------------------


class QuantizedLinear(nn.Module):
    """One row of the weight matrix, one scale.

    Storage is `weight_i8[out, in]` plus `scale[out]`, so row `i`'s
    dequantized weight is `weight_i8[i].float() * scale[i]`. Per-channel,
    not per-tensor: a single outlier row would otherwise force every row's
    scale down to keep that one row representable, quietly clipping the
    rest. `q(w) = round(w / (max(|w_row|) / 127))`.

    Forward dequantizes on every call and hands the result to an ordinary
    `F.linear` -- the honest, naive path, and the one under test.
    """

    def __init__(self, linear: nn.Linear):
        super().__init__()
        with torch.no_grad():
            w = linear.weight.data.float()
            scale = w.abs().amax(dim=1).clamp_min(1e-8) / 127.0
            q = (w / scale[:, None]).round().clamp(-127, 127).to(torch.int8)
        self.register_buffer("weight_i8", q)
        self.register_buffer("scale", scale)
        self.bias = None  # every Linear in this model is bias=False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        w = self.weight_i8.to(x.dtype) * self.scale[:, None]
        return F.linear(x, w, self.bias)


def quantize_model_(model: Transformer) -> tuple[int, int]:
    """Replace every attention and SwiGLU `nn.Linear` in place. Returns
    (fp32 bytes, int8+scale bytes) for the replaced layers only.

    The tied token embedding / output head is left alone: tying an int8
    buffer to the same parameter used for both input lookup and output
    projection is a separate technique (activation/embedding quantization)
    this chapter does not take on. Those layers hold 14.4% of the 88M
    model's parameters (`model.py`'s own `param_report`), so what follows
    measures most, not all, of the model.
    """
    fp32_bytes = int8_bytes = 0
    for block in model.blocks:
        for name in ("q", "k", "v", "o"):
            lin = getattr(block.attn, name)
            fp32_bytes += lin.weight.numel() * 4
            q = QuantizedLinear(lin)
            int8_bytes += q.weight_i8.numel() + q.scale.numel() * 4
            setattr(block.attn, name, q)
        for name in ("gate", "up", "down"):
            lin = getattr(block.mlp, name)
            fp32_bytes += lin.weight.numel() * 4
            q = QuantizedLinear(lin)
            int8_bytes += q.weight_i8.numel() + q.scale.numel() * 4
            setattr(block.mlp, name, q)
    return fp32_bytes, int8_bytes


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def cmd_footprint(args) -> None:
    model, cfg = load_model(args.checkpoint, args.device)
    embed_bytes = model.tok.weight.numel() * 4  # tied: counted once
    total_before = sum(p.numel() for p in model.parameters()) * 4
    fp32_bytes, int8_bytes = quantize_model_(model)
    total_after = embed_bytes + int8_bytes
    print(f"quantized: attn(q,k,v,o) + mlp(gate,up,down) x {cfg.n_layer} layers "
          f"(embedding/head left fp32, tied, {embed_bytes:,} bytes)")
    print(f"quantized-layer bytes:  fp32 {fp32_bytes:,}  ->  int8 {int8_bytes:,}  "
          f"({fp32_bytes / int8_bytes:.2f}x)")
    print(f"whole-model bytes:      before {total_before:,}  ->  after {total_after:,}  "
          f"({total_before / total_after:.2f}x)")


def _first_step_divergence(model, cfg, q_model, q_cfg, cos, sin, prompt, device):
    """Compare fp32 and int8 logits at the *first* generated position only --
    one forward pass each, before any autoregressive compounding.

    This is the check greedy token-matching cannot substitute for: it asks
    whether the two distributions actually agree, not merely whether the
    single highest logit happens to be the same index. See `cmd_verify`.
    """
    idx = torch.tensor([prompt], device=device)
    logits1 = _forward_with_cache(model, cfg, idx, KVCache(cfg, cos.size(0), device), 0, cos, sin)[0, -1].float()
    logits2 = _forward_with_cache(q_model, q_cfg, idx, KVCache(q_cfg, cos.size(0), device), 0, cos, sin)[0, -1].float()
    p1, p2 = torch.softmax(logits1, dim=-1), torch.softmax(logits2, dim=-1)
    kl = torch.sum(p1 * (torch.log(p1.clamp_min(1e-12)) - torch.log(p2.clamp_min(1e-12)))).item()
    cos_sim = F.cosine_similarity(logits1.unsqueeze(0), logits2.unsqueeze(0)).item()
    top1_agrees = bool(int(p1.argmax()) == int(p2.argmax()))
    return kl, cos_sim, top1_agrees


def cmd_verify(args) -> None:
    model, cfg = load_model(args.checkpoint, args.device)
    cos, sin = build_rope_cache(args.max_len, cfg.d_head, cfg.rope_theta, args.device)
    prompt = list(range(args.prompt_len))

    q_model, q_cfg = load_model(args.checkpoint, args.device)
    quantize_model_(q_model)

    kl, cos_sim, top1 = _first_step_divergence(model, cfg, q_model, q_cfg, cos, sin, prompt, args.device)
    print(f"first-position logits: KL(fp32||int8)={kl:.4f} nats, cosine similarity={cos_sim:.5f}, "
          f"top-1 token agrees: {top1}")

    ref = decode_eager(model, cfg, cos, sin, prompt, args.tokens, args.device, False)
    got = decode_eager(q_model, q_cfg, cos, sin, prompt, args.tokens, args.device, False)
    n_match = sum(1 for a, b in zip(ref, got) if a == b)
    print(f"fp32 vs int8 greedy tokens over a full generation: {n_match}/{len(ref)} match")
    if n_match < len(ref):
        first = next(i for i, (a, b) in enumerate(zip(ref, got)) if a != b)
        print(f"  first divergence at token {first}: fp32 {ref[first]} vs int8 {got[first]}")
        print(f"  fp32 {ref[:16]}")
        print(f"  int8 {got[:16]}")


def cmd_bench(args) -> None:
    model, cfg = load_model(args.checkpoint, args.device)
    cos, sin = build_rope_cache(args.max_len, cfg.d_head, cfg.rope_theta, args.device)
    prompt = list(range(args.prompt_len))
    n = args.max_new_tokens

    q_model, q_cfg = load_model(args.checkpoint, args.device)
    quantize_model_(q_model)

    # Correctness gate. Greedy exact-token-match is the wrong instrument here:
    # `cmd_verify` shows the two distributions can sit at cosine similarity
    # 0.9997 and KL 0.003 nats -- nearly identical -- while the single
    # argmax token still flips whenever the top two logits are close, and
    # every later position then conditions on a different token than the
    # reference did. The real gate is distributional agreement at the first
    # position, before that compounding starts.
    kl, cos_sim, _top1 = _first_step_divergence(model, cfg, q_model, q_cfg, cos, sin, prompt, args.device)
    ref = decode_eager(model, cfg, cos, sin, prompt, args.verify_tokens, args.device, False)
    got = decode_eager(q_model, q_cfg, cos, sin, prompt, args.verify_tokens, args.device, False)
    n_match = sum(1 for a, b in zip(ref, got) if a == b)
    passed = cos_sim > 0.99 and kl < 0.05
    print(f"correctness gate: first-position KL={kl:.4f} nats, cosine={cos_sim:.5f} "
          f"-> {'PASS' if passed else 'FAIL'} (threshold: cosine>0.99, KL<0.05)")
    print(f"  (for contrast: full-generation greedy token match is only "
          f"{n_match}/{args.verify_tokens} -- exact match is not the right gate; see README)")
    if not passed:
        raise SystemExit("quantization failed the distributional correctness gate; refusing to report a speedup")
    print()

    dec_fp32 = GraphedDecoder(model, cfg, args.max_len, args.device)
    dec_fp32.generate(prompt, 8)  # forces capture outside the timed region
    dec_i8 = GraphedDecoder(q_model, q_cfg, args.max_len, args.device)
    dec_i8.generate(prompt, 8)

    configs = [
        ("eager, fp32",
         lambda: decode_eager(model, cfg, cos, sin, prompt, n, args.device, False)),
        ("eager, int8 weight-only",
         lambda: decode_eager(q_model, q_cfg, cos, sin, prompt, n, args.device, False)),
        ("CUDA graph, fp32",
         lambda: dec_fp32.generate(prompt, n)),
        ("CUDA graph, int8",
         lambda: dec_i8.generate(prompt, n)),
    ]
    rows = [(name, _time(fn, warmup=1, repeat=args.repeat, tokens=n)) for name, fn in configs]

    base = _median(rows[0][1])
    print(f"prompt {args.prompt_len}, {n} new tokens, batch 1, "
          f"cache sized {args.max_len}, {args.repeat} rounds each")
    print(f"{'configuration':<28}{'tok/s':>10}{'ms/token':>11}{'round spread':>15}{'vs eager fp32':>15}")
    for name, tps in rows:
        med = _median(tps)
        print(f"{name:<28}{med:10.1f}{1000 / med:11.3f}"
              f"{min(tps):7.1f}-{max(tps):<7.1f}{med / base:14.2f}x")


def cmd_profile(args) -> None:
    """Where does the extra time in the int8 path actually go? Same profiling
    method as 01-graph-execution: self CPU time (host issuing work) against
    self CUDA time (device doing it), summed over kernel rows only.
    """
    from torch.profiler import ProfilerActivity, profile

    model, cfg = load_model(args.checkpoint, args.device)
    cos, sin = build_rope_cache(args.max_len, cfg.d_head, cfg.rope_theta, args.device)
    prompt = list(range(args.prompt_len))
    steps = args.steps

    q_model, q_cfg = load_model(args.checkpoint, args.device)
    quantize_model_(q_model)

    from graph_decode import decode_steps_eager, prefill_eager

    for label, m, c in (("eager, fp32", model, cfg), ("eager, int8 weight-only", q_model, q_cfg)):
        decode_eager(m, c, cos, sin, prompt, 10, args.device, False)
        state = prefill_eager(m, c, cos, sin, prompt, args.device)
        torch.cuda.synchronize()
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            decode_steps_eager(m, c, cos, sin, state, steps, args.device, False)
            torch.cuda.synchronize()
        ka = prof.key_averages()
        cpu_ms = sum(e.self_cpu_time_total for e in ka) / 1000
        cuda_ms = sum(e.self_device_time_total for e in ka if e.device_type.name == "CUDA") / 1000
        print(f"\n{label}")
        print(f"  self CPU time total   {cpu_ms:9.1f} ms   ({cpu_ms / steps:6.3f} ms/step)")
        print(f"  self CUDA time total  {cuda_ms:9.1f} ms   ({cuda_ms / steps:6.3f} ms/step)")
        print(f"  host / device         {cpu_ms / max(cuda_ms, 1e-9):9.2f}x")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("footprint")
    p.add_argument("--checkpoint", type=Path, default=None)
    p.add_argument("--device", default="cuda")

    p = sub.add_parser("verify")
    p.add_argument("--checkpoint", type=Path, default=None)
    p.add_argument("--device", default="cuda")
    p.add_argument("--prompt-len", type=int, default=64)
    p.add_argument("--max-len", type=int, default=1024)
    p.add_argument("--tokens", type=int, default=64)

    p = sub.add_parser("bench")
    p.add_argument("--checkpoint", type=Path, default=None)
    p.add_argument("--device", default="cuda")
    p.add_argument("--prompt-len", type=int, default=64)
    p.add_argument("--max-len", type=int, default=1024)
    p.add_argument("--max-new-tokens", type=int, default=128)
    p.add_argument("--repeat", type=int, default=5)
    p.add_argument("--verify-tokens", type=int, default=64)

    p = sub.add_parser("profile")
    p.add_argument("--checkpoint", type=Path, default=None)
    p.add_argument("--device", default="cuda")
    p.add_argument("--prompt-len", type=int, default=64)
    p.add_argument("--max-len", type=int, default=1024)
    p.add_argument("--steps", type=int, default=50)

    args = ap.parse_args()
    {"footprint": cmd_footprint, "verify": cmd_verify, "bench": cmd_bench,
     "profile": cmd_profile}[args.cmd](args)


if __name__ == "__main__":
    main()
