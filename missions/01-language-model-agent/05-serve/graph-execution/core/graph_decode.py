"""Capture one decode step into a CUDA graph, and measure what that is worth.

[Stage 05's engine](../../core/engine.py)
generates at a flat rate no matter how long the sequence gets, and that
chapter explains the flatness as "a fixed per-step cost". This file tests that
explanation and then acts on it.

`profile` answers the diagnostic question. The comparison that settles it is
the profiler's own `Self CPU time total` against its `Self CUDA time total`:
when the host spends longer issuing work than the device spends doing it, the
GPU is idle waiting for Python and the bottleneck is *launches*, not
arithmetic and not bandwidth. Do not sum `self_device_time_total` across
`key_averages()` to get the CUDA figure — every kernel is counted twice there,
once under its `aten::` operator and once under its own row, and the answer
comes out half as bad as it is.

`bench` acts on the diagnosis. A CUDA graph records a sequence of kernel
launches once and replays the whole thing with a single call, so 500 launches
become 1. Recording requires the step to be *replayable*, which the engine's
decode step is not, for three reasons this file has to fix:

1. **`int(logits.argmax())` copies to the host** to build a Python integer,
   which is a synchronisation point in the middle of every step. The next
   token has to stay a device tensor.
2. **The position is a Python integer**, so `cache[..., pos:pos+1] = k` bakes
   a different slice into every step. It becomes a device tensor addressed
   with `index_copy_`.
3. **The attention shape grows with the sequence.** A graph records fixed
   shapes, so the step attends over the *whole* preallocated cache every time
   and masks the positions it has not reached yet.

Fix 3 is the interesting one, because it makes the model do strictly more
arithmetic: at position 70 it attends over 1,024 keys instead of 70. That is
the trade the whole technique rests on. On a launch-bound step, buying fewer
launches with more arithmetic is a good deal, and `bench` is what says whether
it actually was.

Usage:
    python graph_decode.py profile --checkpoint <ckpt.pt>
    python graph_decode.py bench   --checkpoint <ckpt.pt> --max-new-tokens 512
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "missions/01-language-model-agent/05-serve/core"))
sys.path.insert(0, str(ROOT / "missions/01-language-model-agent/02-pretrain/core"))
from engine import KVCache, _forward_with_cache, load_model
from model import apply_rope, build_rope_cache

# --------------------------------------------------------------------------
# The graph-safe decode step
# --------------------------------------------------------------------------


class GraphedDecoder:
    """One decode step, recorded once and replayed.

    Every buffer below is allocated once and never reallocated, because a
    replayed graph writes to the exact memory addresses it was recorded
    against. Handing it a fresh tensor on the second step would replay the
    kernels against the first step's memory and silently produce garbage.
    """

    def __init__(self, model, cfg, max_len: int, device: str):
        self.model, self.cfg, self.max_len, self.device = model, cfg, max_len, device
        self.cos, self.sin = build_rope_cache(max_len, cfg.d_head, cfg.rope_theta, device)
        self.cache = KVCache(cfg, max_len, device)

        # Static I/O. The graph reads `tok` and `pos`, and writes `tok`, `pos`
        # and `generated` — so a replay is a complete step with no host in it.
        self.tok = torch.zeros((1, 1), dtype=torch.long, device=device)
        self.pos = torch.zeros((1,), dtype=torch.long, device=device)
        self.step_idx = torch.zeros((1,), dtype=torch.long, device=device)
        self.generated = torch.zeros((max_len,), dtype=torch.long, device=device)
        self.positions = torch.arange(max_len, device=device)
        self.graph: torch.cuda.CUDAGraph | None = None

    def _attention(self, attn, x, cos, sin, layer_idx, mask):
        cfg = self.cfg
        q = attn.q(x).view(1, 1, cfg.n_head, cfg.d_head).transpose(1, 2)
        k = attn.k(x).view(1, 1, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
        v = attn.v(x).view(1, 1, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

        # index_copy_ with a device index, rather than buf[..., pos] = k with a
        # Python int: the destination has to be chosen at replay time, not
        # baked in at record time.
        self.cache.buf[layer_idx, 0].index_copy_(1, self.pos, k[0])
        self.cache.buf[layer_idx, 1].index_copy_(1, self.pos, v[0])

        # The whole preallocated cache, every step: constant shape, and the
        # mask hides the positions generation has not reached.
        k_full = self.cache.buf[layer_idx, 0].unsqueeze(0)
        v_full = self.cache.buf[layer_idx, 1].unsqueeze(0)
        n_rep = cfg.n_head // cfg.n_kv_head
        if n_rep > 1:
            k_full = k_full.repeat_interleave(n_rep, dim=1)
            v_full = v_full.repeat_interleave(n_rep, dim=1)

        out = F.scaled_dot_product_attention(q, k_full, v_full, attn_mask=mask)
        return attn.o(out.transpose(1, 2).contiguous().view(1, 1, -1))

    def _step(self) -> None:
        """A full decode step in tensor operations only — no Python branch on a
        device value, no `.item()`, no shape that depends on `pos`."""
        model = self.model
        cos = self.cos.index_select(0, self.pos)
        sin = self.sin.index_select(0, self.pos)
        mask = (self.positions <= self.pos).view(1, 1, 1, self.max_len)

        x = model.tok(self.tok)
        for layer_idx, block in enumerate(model.blocks):
            x = x + self._attention(block.attn, block.n1(x), cos, sin, layer_idx, mask)
            x = x + block.mlp(block.n2(x))
        logits = model.head(model.norm(x))

        # Greedy selection stays on the device, and the chosen token is stored
        # into a buffer rather than returned, so N steps cost one transfer at
        # the end instead of N transfers during.
        nxt = logits[0, -1].argmax().view(1)
        self.generated.index_copy_(0, self.step_idx, nxt)
        self.tok.copy_(nxt.view(1, 1))
        self.pos.add_(1)
        self.step_idx.add_(1)

    @torch.no_grad()
    def prefill(self, prompt_ids: list[int]) -> None:
        """Prefill runs eagerly. It processes the whole prompt in one pass, so
        it is compute-bound and has nothing to gain from fewer launches — and
        its shape depends on the prompt, which a graph cannot accept anyway."""
        idx = torch.tensor([prompt_ids], device=self.device)
        logits = _forward_with_cache(
            self.model, self.cfg, idx, self.cache, 0, self.cos, self.sin
        )
        self.tok.copy_(logits[0, -1].argmax().view(1, 1))
        self.pos.fill_(len(prompt_ids))
        self.step_idx.zero_()

    @torch.no_grad()
    def capture(self) -> None:
        """Record the step. The warm-up on a side stream is required, not
        superstition: cuBLAS and the caching allocator lazily initialise state
        on first use, and capturing that initialisation would bake one-time
        setup into every replay."""
        # The warm-up really executes, so it advances every piece of state the
        # step owns -- including `tok`. Rewinding the two counters and leaving
        # `tok` three tokens down a throwaway continuation is a bug that costs
        # nothing in speed and every token in correctness, which is why
        # `bench` checks the output before it times anything.
        saved = (self.tok.clone(), self.pos.clone(), self.step_idx.clone())
        side = torch.cuda.Stream()
        side.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(side):
            for _ in range(3):
                self._step()
        torch.cuda.current_stream().wait_stream(side)
        self._restore(saved)

        self.graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(self.graph):
            self._step()
        # Capture records without executing, so state is untouched here -- but
        # restore anyway rather than depend on that.
        self._restore(saved)

    def _restore(self, saved) -> None:
        tok, pos, idx = saved
        self.tok.copy_(tok)
        self.pos.copy_(pos)
        self.step_idx.copy_(idx)

    @torch.no_grad()
    def generate(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        self.prefill(prompt_ids)
        if self.graph is None:
            self.capture()
        graph = self.graph
        assert graph is not None
        for _ in range(max_new_tokens):
            graph.replay()
        # One transfer for the whole generation, rather than one per step.
        return self.generated[:max_new_tokens].tolist()


# --------------------------------------------------------------------------
# Eager baselines, for the comparison
# --------------------------------------------------------------------------


@torch.no_grad()
def prefill_eager(model, cfg, cos, sin, prompt_ids, device):
    """Prefill, returned as resumable state so a profiler can be pointed at the
    decode loop alone. Prefill is one wide compute-bound pass with a launch
    count of its own; averaging it into 50 decode steps moves the per-step
    figures by a few percent and makes the two configurations below
    incomparable, since only one of them graphs anything."""
    cache = KVCache(cfg, cos.size(0), device)
    idx = torch.tensor([prompt_ids], device=device)
    logits = _forward_with_cache(model, cfg, idx, cache, 0, cos, sin)
    return cache, logits[0, -1].argmax().view(1, 1), len(prompt_ids)


@torch.no_grad()
def decode_steps_eager(model, cfg, cos, sin, state, max_new_tokens, device, host_sync=True):
    """The engine's own decode loop, resumed from `state`, returning the ids.

    `host_sync=False` removes only the `int(argmax)` round-trip, which isolates
    that one cost from everything else the graph changes."""
    cache, nxt, pos = state
    out = []
    for _ in range(max_new_tokens):
        logits = _forward_with_cache(model, cfg, nxt, cache, pos, cos, sin)
        if host_sync:
            token = int(logits[0, -1].argmax())
            out.append(token)
            nxt = torch.tensor([[token]], device=device)
        else:
            nxt = logits[0, -1].argmax().view(1, 1)
            out.append(nxt)
        pos += 1
    return [int(t) for t in out]


@torch.no_grad()
def decode_eager(model, cfg, cos, sin, prompt_ids, max_new_tokens, device, host_sync=True):
    """Prefill plus decode, which is what `bench` should time: a caller wants
    tokens from a prompt, not tokens from a warm cache."""
    state = prefill_eager(model, cfg, cos, sin, prompt_ids, device)
    return decode_steps_eager(model, cfg, cos, sin, state, max_new_tokens, device, host_sync)


def _time(fn, *, warmup: int, repeat: int, tokens: int) -> list[float]:
    """Throughput per round, not one averaged number.

    A single timed window on a shared desktop cannot tell a real 5% difference
    from a background process, so each configuration is measured `repeat` times
    and the caller reports the median and the spread. Anything narrower than
    that spread is not a result."""
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    out = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        torch.cuda.synchronize()
        out.append(tokens / (time.perf_counter() - t0))
    return out


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def _profile_totals(prof) -> tuple[float, float, list]:
    ka = prof.key_averages()
    # Device time is summed over kernel rows only. Summing it over every entry
    # counts each kernel twice — once under its `aten::` operator, which
    # carries the device time of its children, and once under the kernel's own
    # row — and reports the host/device imbalance as half what it is.
    cpu_ms = sum(e.self_cpu_time_total for e in ka) / 1000
    cuda_ms = sum(e.self_device_time_total for e in ka if e.device_type.name == "CUDA") / 1000
    return cpu_ms, cuda_ms, ka


def _report(label: str, cpu_ms: float, cuda_ms: float, ka, steps: int) -> None:
    launches = next((e for e in ka if e.key == "cudaLaunchKernel"), None)
    print(f"\n{label}")
    print(f"  self CPU time total   {cpu_ms:9.1f} ms   ({cpu_ms / steps:6.3f} ms/step)")
    print(f"  self CUDA time total  {cuda_ms:9.1f} ms   ({cuda_ms / steps:6.3f} ms/step)")
    print(f"  host / device         {cpu_ms / max(cuda_ms, 1e-9):9.2f}x")
    if launches is not None:
        ms = launches.self_cpu_time_total / 1000
        print(f"  cudaLaunchKernel      {launches.count:9,} calls "
              f"({launches.count / steps:.0f}/step, "
              f"{launches.self_cpu_time_total / max(launches.count, 1):.2f}us each)")
        print(f"  time in launches      {ms:9.1f} ms  ({ms / cpu_ms * 100:.1f}% of host time)")
    else:
        print("  cudaLaunchKernel            none — the whole step is one graph replay")
    # A ratio near 1 is the interesting third case: neither side is starving
    # the other, so the next win has to come from the kernels themselves rather
    # than from how they are issued. Calling that "launch-bound" because the
    # host is a hair ahead would point the next chapter at the wrong thing.
    ratio = cpu_ms / max(cuda_ms, 1e-9)
    verdict = ("LAUNCH-BOUND — the host cannot feed the device" if ratio > 1.2
               else "device-bound — the host is keeping up" if ratio < 0.83
               else "balanced — host and device cost about the same")
    print(f"  verdict: {verdict}")


def cmd_profile(args) -> None:
    from torch.profiler import ProfilerActivity, profile

    model, cfg = load_model(args.checkpoint, args.device)
    cos, sin = build_rope_cache(args.max_len, cfg.d_head, cfg.rope_theta, args.device)
    prompt = list(range(args.prompt_len))
    steps = args.steps
    acts = [ProfilerActivity.CPU, ProfilerActivity.CUDA]

    print(f"{steps} decode steps, prompt {args.prompt_len}, batch 1, cache {args.max_len}")

    # Prefill and warm-up outside the window, so every number below is
    # per decode step and nothing else.
    decode_eager(model, cfg, cos, sin, prompt, 20, args.device)
    state = prefill_eager(model, cfg, cos, sin, prompt, args.device)
    torch.cuda.synchronize()
    with profile(activities=acts) as prof:
        decode_steps_eager(model, cfg, cos, sin, state, steps, args.device)
        torch.cuda.synchronize()
    cpu_ms, cuda_ms, ka = _profile_totals(prof)
    _report("eager (engine.py)", cpu_ms, cuda_ms, ka, steps)

    # The same measurement after the fix. The device figure is expected to go
    # *up*, not down: a replayed step attends over the whole preallocated cache
    # rather than the tokens generated so far, which is real extra arithmetic.
    # What the comparison shows is whether trading it for fewer launches moved
    # the constraint.
    dec = GraphedDecoder(model, cfg, args.max_len, args.device)
    dec.generate(prompt, 20)  # prefill and capture, both outside the window
    graph = dec.graph
    assert graph is not None
    torch.cuda.synchronize()
    with profile(activities=acts) as prof_g:
        for _ in range(steps):
            graph.replay()
        torch.cuda.synchronize()
    g_cpu, g_cuda, g_ka = _profile_totals(prof_g)
    _report("CUDA graph replay", g_cpu, g_cuda, g_ka, steps)

    print("\nwhere the eager host time goes\n")
    print(prof.key_averages().table(sort_by="self_cpu_time_total", row_limit=args.rows))
    if args.trace:
        prof.export_chrome_trace(str(args.trace))
        print(f"trace written to {args.trace}")


def cmd_bench(args) -> None:
    model, cfg = load_model(args.checkpoint, args.device)
    cos, sin = build_rope_cache(args.max_len, cfg.d_head, cfg.rope_theta, args.device)
    prompt = list(range(args.prompt_len))
    n = args.max_new_tokens

    # Correctness before speed. The graph path changed how attention is masked,
    # where the position lives, and how the token is selected; any one of those
    # could be wrong in a way that still runs fast. Greedy decoding is
    # deterministic, so the two paths must emit the same ids -- and if they do
    # not, the speedup below is meaningless and the run stops here.
    ref = decode_eager(model, cfg, cos, sin, prompt, args.verify_tokens, args.device)
    got = GraphedDecoder(model, cfg, args.max_len, args.device).generate(
        prompt, args.verify_tokens
    )
    if ref != got:
        first = next(i for i, (a, b) in enumerate(zip(ref, got)) if a != b)
        raise SystemExit(
            f"graph and eager disagree at token {first}: "
            f"eager {ref[first]} vs graph {got[first]}\n"
            f"  eager {ref[:12]}\n  graph {got[:12]}"
        )
    print(f"identity check: {args.verify_tokens}/{args.verify_tokens} tokens match eager\n")

    dec = GraphedDecoder(model, cfg, args.max_len, args.device)
    dec.generate(prompt, 8)  # forces capture outside the timed region

    configs = [
        ("eager (engine.py)",
         lambda: decode_eager(model, cfg, cos, sin, prompt, n, args.device, True)),
        ("eager, device-side argmax",
         lambda: decode_eager(model, cfg, cos, sin, prompt, n, args.device, False)),
        ("CUDA graph replay",
         lambda: dec.generate(prompt, n)),
    ]
    rows = [(name, _time(fn, warmup=1, repeat=args.repeat, tokens=n))
            for name, fn in configs]

    base = _median(rows[0][1])
    print(f"prompt {args.prompt_len}, {n} new tokens, batch 1, "
          f"cache sized {args.max_len}, {args.repeat} rounds each")
    print(f"{'configuration':<28}{'tok/s':>10}{'ms/token':>11}{'round spread':>15}{'vs eager':>10}")
    for name, tps in rows:
        med = _median(tps)
        print(f"{name:<28}{med:10.1f}{1000 / med:11.3f}"
              f"{min(tps):7.1f}-{max(tps):<7.1f}{med / base:9.2f}x")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("profile", "bench"):
        p = sub.add_parser(name)
        p.add_argument("--checkpoint", type=Path, default=None)
        p.add_argument("--device", default="cuda")
        p.add_argument("--prompt-len", type=int, default=64)
        p.add_argument("--max-len", type=int, default=1024)
        if name == "profile":
            p.add_argument("--steps", type=int, default=50)
            p.add_argument("--rows", type=int, default=12)
            p.add_argument("--trace", type=Path, default=None)
        else:
            p.add_argument("--max-new-tokens", type=int, default=512)
            p.add_argument("--repeat", type=int, default=5)
            p.add_argument("--verify-tokens", type=int, default=64)
    args = ap.parse_args()
    (cmd_profile if args.cmd == "profile" else cmd_bench)(args)


if __name__ == "__main__":
    main()
