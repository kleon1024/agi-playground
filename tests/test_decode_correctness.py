"""A cached decode step must produce the logits a full recompute would.

That is the whole contract of a KV cache: it is an optimisation, so feeding
token `t` with `t-1` tokens already cached has to land on exactly the row
`model.forward(seq)` puts at position `t`. Both engines in
[`serve`](../01-language-model/serve/core/engine.py) are
checked against that, prefill and decode alike.

The comparison is on **logits**, not on generated token ids, and the reason is
worth stating because the obvious test does not work. A randomly initialised
model decodes greedily into the same token forever -- the untrained head favours
whatever is in the residual stream, which is the token just fed in. So an
id-level comparison passes with the attention math completely broken, because
both paths repeat. Logits have no such blind spot.

This guards a bug that shipped and stayed invisible for exactly that reason:
`scaled_dot_product_attention(..., is_causal=True)` builds its mask top-left, as
`tril` of a `(T_q, T_k)` matrix. Prefill has `T_q == T_k`, so it was correct.
Every *decode* step has `T_q == 1` against `T_k == pos + 1`, where top-left
alignment leaves exactly one key unmasked: position 0. The engine loaded, ran,
and benchmarked at full speed while attending to the first token of the prompt
and nothing else. `causal_lower_right` is the alignment a decode step needs.

CPU-only and about a second: the bug lives in the masking geometry, not in the
scale, so two layers over a 64-token vocabulary reproduce it exactly.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SERVE = ROOT / "01-language-model/serve/core"
PRETRAIN = ROOT / "01-language-model/pretrain/core"

torch = pytest.importorskip("torch", reason="needs torch; run `uv run --group torch pytest`")
for _p in (str(SERVE), str(PRETRAIN)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from engine import (
    KVCache,
    PagedKVCache,
    _forward_with_cache,
    _forward_with_cache_paged,
)
from model import Config, Transformer, build_rope_cache

PREFILL = 6
TOTAL = 21  # 15 decode steps, enough to cross several paged block boundaries
BLOCK_SIZE = 4
MAX_LEN = 64
TOL = 2e-5  # cached and recomputed attention reduce in different orders


@pytest.fixture(scope="module")
def fixture():
    torch.manual_seed(0)
    cfg = Config(
        vocab_size=64, n_layer=2, n_head=4, n_kv_head=2,
        d_model=32, d_ff=64, block_size=MAX_LEN,
    )
    model = Transformer(cfg).eval()
    seq = torch.randint(0, cfg.vocab_size, (1, TOTAL)).tolist()[0]
    cos, sin = build_rope_cache(MAX_LEN, cfg.d_head, cfg.rope_theta, "cpu")
    with torch.no_grad():
        reference, _ = model(torch.tensor([seq]))
    return model, cfg, seq, cos, sin, reference


def _worst_gap(got, reference, positions):
    """Largest absolute logit error over the checked positions, and where."""
    worst, at = 0.0, -1
    for step_logits, pos in zip(got, positions):
        gap = float((step_logits - reference[0, pos]).abs().max())
        if gap > worst:
            worst, at = gap, pos
    return worst, at


@torch.no_grad()
def test_kv_cache_logits_match_full_recompute(fixture):
    model, cfg, seq, cos, sin, reference = fixture
    cache = KVCache(cfg, MAX_LEN, "cpu")

    got = [_forward_with_cache(
        model, cfg, torch.tensor([seq[:PREFILL]]), cache, 0, cos, sin
    )[0, -1]]
    for pos in range(PREFILL, TOTAL):
        got.append(_forward_with_cache(
            model, cfg, torch.tensor([[seq[pos]]]), cache, pos, cos, sin
        )[0, -1])

    positions = [PREFILL - 1, *range(PREFILL, TOTAL)]
    gap, at = _worst_gap(got, reference, positions)
    assert gap < TOL, f"cached decode diverges from recompute by {gap:.4g} at position {at}"


@torch.no_grad()
def test_paged_cache_logits_match_full_recompute(fixture):
    model, cfg, seq, cos, sin, reference = fixture
    cache = PagedKVCache(cfg, num_blocks=32, block_size=BLOCK_SIZE, device="cpu")
    # One contiguous block table is enough: the gather being tested walks the
    # table either way, and correctness does not depend on the blocks being
    # scattered.
    table = list(range(32))

    got = [_forward_with_cache_paged(
        model, cfg, torch.tensor([seq[:PREFILL]]), cache, table, 0, cos, sin
    )[0, -1]]
    for pos in range(PREFILL, TOTAL):
        got.append(_forward_with_cache_paged(
            model, cfg, torch.tensor([[seq[pos]]]), cache, table, pos, cos, sin
        )[0, -1])

    positions = [PREFILL - 1, *range(PREFILL, TOTAL)]
    gap, at = _worst_gap(got, reference, positions)
    assert gap < TOL, f"paged decode diverges from recompute by {gap:.4g} at position {at}"
