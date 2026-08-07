"""Write a random-initialized checkpoint, for SFT with no pretraining.

`core/sft.py` always loads a base checkpoint, and the model-size chapter needs
the "no pretraining" control: the same architecture and SFT recipe, started
from random weights instead of a trained base. This script writes the
`{"model": state_dict, ...}` shape sft.py loads, with `tokens_seen` absent so
the loaded-base banner reports zero pretraining tokens.

Run:
    uv run --group torch python init_random_ckpt.py --out /tmp/shakespeare/rand/ckpt.pt \
        --n-layer 4 --n-head 4 --n-kv-head 4 --d-model 192 --d-ff 512
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "02-pretrain" / "core"))

from model import Config, Transformer


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("ckpt.pt"))
    ap.add_argument("--n-layer", type=int, default=12)
    ap.add_argument("--n-head", type=int, default=12)
    ap.add_argument("--n-kv-head", type=int, default=4)
    ap.add_argument("--d-model", type=int, default=768)
    ap.add_argument("--d-ff", type=int, default=2048)
    ap.add_argument("--block-size", type=int, default=1024)
    args = ap.parse_args()

    cfg = Config(
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_kv_head=args.n_kv_head,
        d_model=args.d_model,
        d_ff=args.d_ff,
        block_size=args.block_size,
    )
    model = Transformer(cfg)
    n_params = sum(p.numel() for p in model.parameters())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "step": 0}, args.out)
    print(f"wrote random-init checkpoint ({n_params:,} params) -> {args.out}")


if __name__ == "__main__":
    main()
