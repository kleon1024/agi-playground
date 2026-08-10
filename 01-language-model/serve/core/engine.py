"""A minimal inference engine, built in three layers, each benchmarkable
against the one before it: naive generation -> KV cache -> paged blocks with
continuous batching.

This file does not import [`02-pretrain`'s `Transformer`](../../02-pretrain/core/model.py)
forward pass for anything past embedding and per-block submodules. Its
`forward()` has no cache path — adding one there would mean threading a
`past_kv` argument through every call site that trains the model, for a
capability training never needs. Instead this file re-implements the block
loop and the attention math with a cache, reusing the *trained weights*
(`block.attn.q/k/v/o`, `block.mlp`, `block.n1/n2`, `model.norm`, `model.head`
are all still the original `nn.Module`s) but never calling `model.forward()`
or `Attention.forward()` once a cache is in play. `model.py` is untouched.

The three engines, in the order this file builds them:

1. `generate_naive` — the reference. Every decode step feeds the *entire*
   sequence so far through a full forward pass, recomputing K/V for every
   token it has already seen. Correct, and quadratic in total work across a
   generation.
2. `KVCacheEngine` — one sequence, one contiguous preallocated buffer per
   layer. Prefill writes K/V for the whole prompt once; each decode step
   computes K/V for only the *new* token and reads the rest from the cache.
   Linear total work, but the buffer is sized for `max_len` regardless of how
   long generation actually runs — the fragmentation paging exists to fix.
3. `ContinuousBatchingEngine` — the cache is cut into fixed-size physical
   blocks, addressed per-sequence through a block table (`BlockAllocator`,
   `PagedKVCache`), so memory is claimed on demand and released the instant a
   sequence finishes. Wrapped in a scheduler (`step()`) that admits waiting
   requests and evicts finished ones between every forward pass, so the
   batch's composition — not its size — changes on every iteration.

See `../README.md` for the memory-bandwidth argument, the KV cache formula,
and why GQA and paging matter, worked out against this model's own dimensions.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import torch
from torch.nn import functional as F
from torch.nn.attention.bias import causal_lower_right

# The model these engines serve lives two directories over, in the pretrain
# stage. Importing it rather than duplicating it means the engine always
# serves exactly the architecture that was trained — see the module docstring
# for why the forward pass is nonetheless re-implemented here, not imported.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pretrain" / "core"))
from model import Config, Transformer, apply_rope, build_rope_cache


def load_model(checkpoint: Path | None, device: str) -> tuple[Transformer, Config]:
    """Load a trained checkpoint, or a freshly initialized model of the same
    shape when none is given. Random weights produce nonsense text but the
    exact same tensor shapes and memory footprint as trained ones, so the
    benchmark below is meaningful with or without a real checkpoint — useful
    on a machine with no GPU and no completed training run yet.
    """
    cfg = Config()
    if checkpoint is not None:
        ckpt = torch.load(checkpoint, map_location=device)
        cfg = Config(**ckpt["config"])
        model = Transformer(cfg)
        model.load_state_dict(ckpt["model"])
    else:
        model = Transformer(cfg)
    model.to(device).eval()
    return model, cfg


# --------------------------------------------------------------------------
# Layer 0: naive generation — the reference every other layer is measured against
# --------------------------------------------------------------------------


@torch.no_grad()
def generate_naive(model: Transformer, prompt_ids: list[int], max_new_tokens: int, device: str) -> list[int]:
    """Recompute everything, every step. This is how autoregressive sampling
    is usually first explained, and it is correct: token n+1 only needs
    attention over tokens 1..n, and feeding the whole growing sequence through
    `model.forward()` every time recovers that trivially. The cost is
    quadratic total work across a generation, because step t recomputes K/V
    for all t prior tokens instead of reusing them.
    """
    idx = torch.tensor([prompt_ids], device=device)
    for _ in range(max_new_tokens):
        logits, _ = model(idx)
        next_id = int(logits[0, -1].argmax())
        idx = torch.cat([idx, torch.tensor([[next_id]], device=device)], dim=1)
    return idx[0].tolist()


# --------------------------------------------------------------------------
# Layer 1: KV cache — one sequence, one contiguous buffer
# --------------------------------------------------------------------------


class KVCache:
    """A single sequence's cache: one preallocated buffer per layer, sized
    for `max_len` tokens up front.

    Shape: `(n_layer, 2, max_len, n_kv_head, d_head)`. Note this stores the
    *unrepeated* KV heads — `n_kv_head`, not `n_head` — which is exactly the
    GQA saving `model.py`'s `param_report()` prints: the cache this class
    holds is `n_head / n_kv_head` times smaller than it would be under plain
    multi-head attention, for identical model quality.

    This is deliberately not memory-efficient: every sequence reserves the
    full `max_len` regardless of how many tokens it actually generates. That
    reservation-up-front waste is exactly what `PagedKVCache` (layer 2 below)
    fixes; this class exists to isolate the *recompute -> cache* win on its
    own, before paging is introduced.
    """

    def __init__(self, cfg: Config, max_len: int, device: str, dtype: torch.dtype = torch.float32):
        # (n_layer, {k,v}, n_kv_head, max_len, d_head) — kv-head-major so a
        # write/read is a plain slice against k/v's own (n_kv_head, T, d_head)
        # layout, no transpose needed on either side.
        self.buf = torch.zeros(
            (cfg.n_layer, 2, cfg.n_kv_head, max_len, cfg.d_head), device=device, dtype=dtype
        )

    def write(self, layer: int, k: torch.Tensor, v: torch.Tensor, pos: int) -> None:
        # k, v: (n_kv_head, n_tokens, d_head)
        n = k.size(1)
        self.buf[layer, 0, :, pos : pos + n] = k
        self.buf[layer, 1, :, pos : pos + n] = v

    def read(self, layer: int, upto: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.buf[layer, 0, :, :upto], self.buf[layer, 1, :, :upto]


def _cached_attention(attn, cfg: Config, x, cos, sin, cache: KVCache, layer_idx: int, start_pos: int):
    """Re-implementation of `Attention.forward` (model.py) with a cache.

    Differences from the original, and why each exists:
    - `cos`/`sin` are the slice for *this call's* absolute positions
      (`start_pos .. start_pos+T`), not always `0..T` — RoPE's angle depends
      on true position, and a decode step's one new token sits at whatever
      position generation has reached, not position 0.
    - the new token's K/V are written into the cache before reading, and
      attention runs against the cache's full contents (`start_pos + T`
      tokens) rather than only the T tokens in `x` — the entire point.
    - `is_causal=True` is **wrong** here and the mask has to be given
      explicitly. PyTorch builds its causal mask top-left — `tril` of a
      `(T_q, T_k)` matrix — so with one query against N cached keys the only
      key row that survives is key 0. A decode step needs the opposite,
      bottom-right alignment, where the last query sees every key. The two
      coincide exactly when `T_q == T_k`, which is why prefill was correct and
      every decode step silently attended to the first token alone.
      `causal_lower_right` is that alignment, and it reduces to `is_causal`
      when the shapes are square.
    """
    _, T, _ = x.shape
    q = attn.q(x).view(1, T, cfg.n_head, cfg.d_head).transpose(1, 2)
    k = attn.k(x).view(1, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
    v = attn.v(x).view(1, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
    q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

    cache.write(layer_idx, k[0], v[0], start_pos)
    k_full, v_full = cache.read(layer_idx, start_pos + T)
    k_full, v_full = k_full.unsqueeze(0), v_full.unsqueeze(0)

    n_rep = cfg.n_head // cfg.n_kv_head
    if n_rep > 1:
        k_full = k_full.repeat_interleave(n_rep, dim=1)
        v_full = v_full.repeat_interleave(n_rep, dim=1)

    out = F.scaled_dot_product_attention(
        q, k_full, v_full, attn_mask=causal_lower_right(T, start_pos + T)
    )
    return attn.o(out.transpose(1, 2).contiguous().view(1, T, -1))


def _forward_with_cache(model: Transformer, cfg: Config, idx, cache: KVCache, start_pos: int, cos_full, sin_full):
    """Re-implementation of `Transformer.forward` with a cache: same block
    loop, cache-aware attention, logits only (no loss — this is inference).
    """
    T = idx.shape[1]
    cos, sin = cos_full[start_pos : start_pos + T], sin_full[start_pos : start_pos + T]
    x = model.tok(idx)
    for layer_idx, block in enumerate(model.blocks):
        x = x + _cached_attention(block.attn, cfg, block.n1(x), cos, sin, cache, layer_idx, start_pos)
        x = x + block.mlp(block.n2(x))
    return model.head(model.norm(x))


class KVCacheEngine:
    """Single-sequence generation with a KV cache: prefill once, then one
    new-token forward pass per decode step instead of recomputing the whole
    sequence.
    """

    def __init__(self, model: Transformer, cfg: Config, max_len: int, device: str):
        self.model, self.cfg, self.device = model, cfg, device
        self.cos_full, self.sin_full = build_rope_cache(max_len, cfg.d_head, cfg.rope_theta, device)

    @torch.no_grad()
    def generate(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        cache = KVCache(self.cfg, self.cos_full.size(0), self.device)
        idx = torch.tensor([prompt_ids], device=self.device)
        logits = _forward_with_cache(self.model, self.cfg, idx, cache, 0, self.cos_full, self.sin_full)
        next_id = int(logits[0, -1].argmax())
        out, pos = [*prompt_ids, next_id], len(prompt_ids)
        for _ in range(max_new_tokens - 1):
            step = torch.tensor([[next_id]], device=self.device)
            logits = _forward_with_cache(self.model, self.cfg, step, cache, pos, self.cos_full, self.sin_full)
            next_id = int(logits[0, -1].argmax())
            out.append(next_id)
            pos += 1
        return out


# --------------------------------------------------------------------------
# Layer 2/3: paged blocks + continuous batching
# --------------------------------------------------------------------------

BLOCK_SIZE = 16  # tokens per physical block — vLLM's original default


class BlockAllocator:
    """A page allocator for KV cache blocks: a free list of physical block
    ids, handed out on request and returned on release.

    The fragmentation this fixes: `KVCacheEngine` above reserves `max_len`
    tokens per sequence up front. A sequence that finishes after 20 tokens
    but was sized for 1024 wastes the other 1004 slots for as long as it
    lives — *internal* fragmentation. Two sequences sized differently can't
    reuse each other's unused space even when memory is free between them —
    *external* fragmentation. Production systems reported 60-80% of KV cache
    memory lost this way before PagedAttention.

    Fixed-size blocks fix both, the same way OS virtual memory does: every
    allocation is one small, identically-sized chunk, so any free block can
    satisfy any request regardless of which sequence held it last, and a
    finished sequence's blocks go straight back to the free list instead of
    sitting reserved for tokens that were never generated.
    """

    def __init__(self, num_blocks: int):
        self.free: list[int] = list(range(num_blocks))

    def alloc(self) -> int:
        if not self.free:
            raise RuntimeError("out of KV cache blocks")
        return self.free.pop()

    def free_blocks(self, block_ids: list[int]) -> None:
        self.free.extend(block_ids)


class PagedKVCache:
    """The same idea as `KVCache`, but the buffer is `num_blocks` fixed-size
    chunks instead of one `max_len`-sized reservation per sequence, and each
    sequence is addressed through a block table — a list mapping its logical
    block index to a physical block id — instead of a direct offset. That
    indirection is the entire mechanism: physical storage is shared and
    non-contiguous; each sequence just remembers which chunks are its own.
    """

    def __init__(self, cfg: Config, num_blocks: int, block_size: int, device: str, dtype: torch.dtype = torch.float32):
        self.block_size = block_size
        self.buf = torch.zeros(
            (cfg.n_layer, 2, num_blocks, block_size, cfg.n_kv_head, cfg.d_head), device=device, dtype=dtype
        )

    def write(self, layer: int, block_table: list[int], pos: int, k: torch.Tensor, v: torch.Tensor) -> None:
        # k, v: (n_kv_head, n_tokens, d_head). Written token-range-first,
        # splitting at block boundaries wherever the range crosses one.
        n, written = k.size(1), 0
        while written < n:
            logical = (pos + written) // self.block_size
            offset = (pos + written) % self.block_size
            physical = block_table[logical]
            take = min(self.block_size - offset, n - written)
            self.buf[layer, 0, physical, offset : offset + take] = k[:, written : written + take].transpose(0, 1)
            self.buf[layer, 1, physical, offset : offset + take] = v[:, written : written + take].transpose(0, 1)
            written += take

    def read(self, layer: int, block_table: list[int], length: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Gather this sequence's cached K/V into one contiguous
        `(n_kv_head, length, d_head)` tensor by walking its block table.

        This gather *is* PagedAttention's real cost: production kernels fuse
        it directly into the attention computation (reading blocks straight
        from the paged buffer, no intermediate copy). We materialize a
        contiguous copy here instead, because it lets attention stay the same
        `F.scaled_dot_product_attention` call `KVCache` used — trading some
        performance for a much shorter, more readable implementation.
        """
        n_full, rem = divmod(length, self.block_size)
        n_blocks = n_full + (1 if rem else 0)
        ks, vs = [], []
        for i in range(n_blocks):
            physical = block_table[i]
            take = self.block_size if i < n_full else rem
            ks.append(self.buf[layer, 0, physical, :take])
            vs.append(self.buf[layer, 1, physical, :take])
        return torch.cat(ks, dim=0).transpose(0, 1), torch.cat(vs, dim=0).transpose(0, 1)


def _cached_attention_paged(attn, cfg: Config, x, cos, sin, cache: PagedKVCache, layer_idx: int,
                             block_table: list[int], start_pos: int):
    """`_cached_attention`, reading and writing through a block table instead
    of a direct offset into one contiguous buffer. The attention math is
    identical — including the bottom-right causal alignment, for the reason
    given there; only where K/V physically live has changed.
    """
    _, T, _ = x.shape
    q = attn.q(x).view(1, T, cfg.n_head, cfg.d_head).transpose(1, 2)
    k = attn.k(x).view(1, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
    v = attn.v(x).view(1, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
    q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

    cache.write(layer_idx, block_table, start_pos, k[0], v[0])
    k_full, v_full = cache.read(layer_idx, block_table, start_pos + T)
    k_full, v_full = k_full.unsqueeze(0), v_full.unsqueeze(0)

    n_rep = cfg.n_head // cfg.n_kv_head
    if n_rep > 1:
        k_full = k_full.repeat_interleave(n_rep, dim=1)
        v_full = v_full.repeat_interleave(n_rep, dim=1)

    out = F.scaled_dot_product_attention(
        q, k_full, v_full, attn_mask=causal_lower_right(T, start_pos + T)
    )
    return attn.o(out.transpose(1, 2).contiguous().view(1, T, -1))


def _forward_with_cache_paged(model: Transformer, cfg: Config, idx, cache: PagedKVCache, block_table: list[int],
                               start_pos: int, cos_full, sin_full):
    T = idx.shape[1]
    cos, sin = cos_full[start_pos : start_pos + T], sin_full[start_pos : start_pos + T]
    x = model.tok(idx)
    for layer_idx, block in enumerate(model.blocks):
        x = x + _cached_attention_paged(
            block.attn, cfg, block.n1(x), cos, sin, cache, layer_idx, block_table, start_pos
        )
        x = x + block.mlp(block.n2(x))
    return model.head(model.norm(x))


@dataclass
class Sequence:
    """One in-flight generation request, from the scheduler's point of view."""

    seq_id: int
    prompt: list[int]
    max_new_tokens: int
    generated: list[int] = field(default_factory=list)
    block_table: list[int] = field(default_factory=list)
    length: int = 0  # tokens already written into the cache
    done: bool = False


def _ensure_blocks(seq: Sequence, allocator: BlockAllocator, block_size: int, upto_len: int) -> None:
    """Grow a sequence's block table on demand, one block at a time, as
    generation reaches into a new one — 'allocated on demand', not reserved
    for the sequence's maximum possible length up front.
    """
    needed = (upto_len + block_size - 1) // block_size
    while len(seq.block_table) < needed:
        seq.block_table.append(allocator.alloc())


class ContinuousBatchingEngine:
    """Iteration-level scheduling over the paged cache.

    Each call to `step()` is one forward "tick": admit as many `waiting`
    requests as free blocks currently allow, run one prefill-or-decode step
    for every `running` request, evict anything that just finished (freeing
    its blocks immediately, back to the pool `_admit` draws from), and
    return. Nothing here holds a fixed batch — the set of active requests,
    and therefore the batch's *size and identity*, can differ on every call.
    That is what "continuous" means: a scheduling change, not a bigger batch
    size. A short request finishing early does not sit idle holding a slot
    until its neighbors catch up, the way static batching would leave it.

    Simplification, stated plainly: real engines fuse the per-request loop
    below into a single batched kernel call over ragged sequence lengths
    (vLLM/SGLang's fused paged-attention kernels, `prod/vllm_serve.py`'s
    subject). We loop over requests in Python, one at a time, because that
    is what stays readable at this scale — the scheduling decisions this
    class makes (admit, evict, free) are the same either way.
    """

    def __init__(self, model: Transformer, cfg: Config, num_blocks: int, block_size: int, device: str,
                 max_batch: int = 8):
        self.model, self.cfg, self.device = model, cfg, device
        self.block_size, self.max_batch = block_size, max_batch
        self.allocator = BlockAllocator(num_blocks)
        self.cache = PagedKVCache(cfg, num_blocks, block_size, device)
        max_len = num_blocks * block_size
        self.cos_full, self.sin_full = build_rope_cache(max_len, cfg.d_head, cfg.rope_theta, device)
        self.waiting: list[Sequence] = []
        self.running: list[Sequence] = []
        self.finished: list[Sequence] = []
        self._next_id = 0

    def submit(self, prompt_ids: list[int], max_new_tokens: int) -> int:
        seq = Sequence(seq_id=self._next_id, prompt=prompt_ids, max_new_tokens=max_new_tokens)
        self._next_id += 1
        self.waiting.append(seq)
        return seq.seq_id

    def _admit(self) -> None:
        while self.waiting and len(self.running) < self.max_batch:
            needed = (len(self.waiting[0].prompt) + self.block_size - 1) // self.block_size
            if needed > len(self.allocator.free):
                break  # not enough free memory to admit this request right now
            self.running.append(self.waiting.pop(0))

    @torch.no_grad()
    def step(self) -> bool:
        """Run one iteration. Returns True while there is still work pending."""
        self._admit()
        still_running = []
        for seq in self.running:
            idx = (
                torch.tensor([seq.prompt], device=self.device)
                if seq.length == 0
                else torch.tensor([[seq.generated[-1]]], device=self.device)
            )
            _ensure_blocks(seq, self.allocator, self.block_size, seq.length + idx.size(1))
            logits = _forward_with_cache_paged(
                self.model, self.cfg, idx, self.cache, seq.block_table, seq.length, self.cos_full, self.sin_full
            )
            next_id = int(logits[0, -1].argmax())
            seq.length += idx.size(1)
            seq.generated.append(next_id)
            if len(seq.generated) >= seq.max_new_tokens:
                seq.done = True
                self.allocator.free_blocks(seq.block_table)
                self.finished.append(seq)
            else:
                still_running.append(seq)
        self.running = still_running
        return bool(self.running or self.waiting)

    def run_to_completion(self) -> dict[int, list[int]]:
        while self.step():
            pass
        return {seq.seq_id: seq.prompt + seq.generated for seq in self.finished}


# --------------------------------------------------------------------------
# Benchmark: naive vs KV cache vs paged+continuous
# --------------------------------------------------------------------------


def _peak_memory_bytes(device: str) -> int:
    if device == "cuda":
        return torch.cuda.max_memory_allocated()
    # No portable peak-RSS-since-reset API on CPU/MPS; report 0 and let the
    # caller know this number is CUDA-only rather than print a fake one.
    return 0


def _bench_naive(model, cfg, device, prompt_len, max_new_tokens):
    prompt = list(range(prompt_len))
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    generate_naive(model, prompt, max_new_tokens, device)
    elapsed = time.perf_counter() - t0
    return elapsed, _peak_memory_bytes(device)


def _bench_kvcache(model, cfg, device, prompt_len, max_new_tokens):
    prompt = list(range(prompt_len))
    engine = KVCacheEngine(model, cfg, max_len=cfg.block_size, device=device)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    engine.generate(prompt, max_new_tokens)
    elapsed = time.perf_counter() - t0
    return elapsed, _peak_memory_bytes(device)


def _bench_paged(model, cfg, device, prompt_len, max_new_tokens, num_requests):
    num_blocks = (num_requests * (prompt_len + max_new_tokens) // BLOCK_SIZE) + num_requests + 4
    engine = ContinuousBatchingEngine(model, cfg, num_blocks=num_blocks, block_size=BLOCK_SIZE, device=device)
    for _ in range(num_requests):
        engine.submit(list(range(prompt_len)), max_new_tokens)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    engine.run_to_completion()
    elapsed = time.perf_counter() - t0
    total_tokens = num_requests * max_new_tokens
    return elapsed, _peak_memory_bytes(device), total_tokens


def run_benchmark(checkpoint: Path | None, device: str, prompt_len: int, max_new_tokens: int, num_requests: int):
    model, cfg = load_model(checkpoint, device)

    print(f"{'engine':<24}{'tokens/sec':>14}{'wall-clock s':>16}{'peak mem':>16}")
    print("-" * 70)

    elapsed, mem = _bench_naive(model, cfg, device, prompt_len, max_new_tokens)
    print(f"{'naive (no cache)':<24}{max_new_tokens / elapsed:>14.1f}{elapsed:>16.3f}{mem / 1e6:>13.1f}MB")

    elapsed, mem = _bench_kvcache(model, cfg, device, prompt_len, max_new_tokens)
    print(f"{'KV cache':<24}{max_new_tokens / elapsed:>14.1f}{elapsed:>16.3f}{mem / 1e6:>13.1f}MB")

    elapsed, mem, total_tokens = _bench_paged(model, cfg, device, prompt_len, max_new_tokens, num_requests)
    print(f"{'paged + continuous':<24}{total_tokens / elapsed:>14.1f}{elapsed:>16.3f}{mem / 1e6:>13.1f}MB")
    print(f"\n(paged+continuous ran {num_requests} concurrent requests; the other two ran 1)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    bench = sub.add_parser("bench", help="benchmark naive vs KV cache vs paged+continuous")
    bench.add_argument("--checkpoint", type=Path, default=None, help="path to a ckpt.pt; random init if omitted")
    bench.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    bench.add_argument("--prompt-len", type=int, default=64)
    bench.add_argument("--max-new-tokens", type=int, default=64)
    bench.add_argument("--num-requests", type=int, default=8, help="concurrent requests for the paged+continuous run")

    gen = sub.add_parser("generate", help="generate from a prompt with the KV cache engine")
    gen.add_argument("--checkpoint", type=Path, default=None)
    gen.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    gen.add_argument("--prompt-ids", type=int, nargs="+", required=True)
    gen.add_argument("--max-new-tokens", type=int, default=32)

    args = ap.parse_args()

    if args.command == "bench":
        run_benchmark(args.checkpoint, args.device, args.prompt_len, args.max_new_tokens, args.num_requests)
    elif args.command == "generate":
        model, cfg = load_model(args.checkpoint, args.device)
        engine = KVCacheEngine(model, cfg, max_len=cfg.block_size, device=args.device)
        out = engine.generate(args.prompt_ids, args.max_new_tokens)
        print(out)


if __name__ == "__main__":
    main()
