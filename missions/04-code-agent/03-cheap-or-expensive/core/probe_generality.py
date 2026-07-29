"""Does a patch that passes the test hold outside the shape the test makes?

A test written from one observed failure teaches a fix to cover that failure.
Nothing makes it cover the neighbouring case, and the resolve rate cannot tell
the difference -- both patches are green.

This probe asks one specific version of that question about the causal-masking
task. `tests/test_decode_correctness.py` runs a prefill and then single-token
decode steps, so the cached attention is only ever exercised with `T_q == 1`
against a longer cache. Chunked prefill, speculative-decode verification, and
prefix-cache reuse all send `T_q > 1` against a cache that is already
populated. A patch that switches masking off whenever the query is shorter than
the cache is right for `T_q == 1` and wrong here -- queries inside the block
attend to keys later in the same block, which is precisely the thing a causal
mask exists to prevent.

Both shapes are checked, because a probe that only tests the untested case
cannot distinguish "wrong here" from "wrong everywhere".

Usage:
    uv run --group torch python probe_generality.py <path/to/engine.py>
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import torch

MAX_LEN = 64
TOTAL = 10
SPLIT = 6  # cache holds 6, then a 4-token query arrives
TOL = 2e-5  # the target test's own tolerance


def load_engine(path: Path):
    """Import an engine.py and the model it needs, by path.

    Each patched copy lives in its own materialized task, so this is called
    once per variant with a different tree each time.
    """
    serve = path.parent
    pretrain = serve.parents[1] / "02-pretrain/core"
    for p in (str(serve), str(pretrain)):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("engine", path)
    assert spec is not None and spec.loader is not None
    engine = importlib.util.module_from_spec(spec)
    sys.modules["engine"] = engine
    spec.loader.exec_module(engine)
    return engine


def probe(path: Path) -> tuple[float, float]:
    """Returns (single-token gap, multi-token-on-live-cache gap)."""
    engine = load_engine(path)
    from model import Config, Transformer, build_rope_cache

    torch.manual_seed(0)
    cfg = Config(
        vocab_size=64, n_layer=2, n_head=4, n_kv_head=2, d_model=32, d_ff=64, block_size=MAX_LEN
    )
    model = Transformer(cfg).eval()
    seq = torch.randint(0, cfg.vocab_size, (1, TOTAL))
    cos, sin = build_rope_cache(MAX_LEN, cfg.d_head, cfg.rope_theta, "cpu")

    with torch.no_grad():
        reference, _ = model(seq)

        # The shape the test checks: one token against a live cache.
        cache = engine.KVCache(cfg, MAX_LEN, "cpu")
        engine._forward_with_cache(model, cfg, seq[:, :SPLIT], cache, 0, cos, sin)
        step = engine._forward_with_cache(
            model, cfg, seq[:, SPLIT : SPLIT + 1], cache, SPLIT, cos, sin
        )

        # The shape it never makes: four tokens against the same cache.
        cache = engine.KVCache(cfg, MAX_LEN, "cpu")
        engine._forward_with_cache(model, cfg, seq[:, :SPLIT], cache, 0, cos, sin)
        chunk = engine._forward_with_cache(model, cfg, seq[:, SPLIT:], cache, SPLIT, cos, sin)

    return (
        (step[0, -1] - reference[0, SPLIT]).abs().max().item(),
        (chunk[0, -1] - reference[0, -1]).abs().max().item(),
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    tested, untested = probe(Path(sys.argv[1]).resolve())
    print(f"single-token decode (the test's shape)  max gap {tested:.3e}  "
          f"{'ok' if tested < TOL else 'FAIL'}")
    print(f"4-token query on a live cache           max gap {untested:.3e}  "
          f"{'ok' if untested < TOL else 'WRONG'}")
    raise SystemExit(0 if tested < TOL and untested < TOL else 1)


if __name__ == "__main__":
    main()
