"""Turn a trained dense checkpoint into a mixture-of-experts model that starts
at exactly the loss it was trained to, then keep training it.

Five hours produced the 88M checkpoint in
[stage 02](../../../../missions/01-language-model-agent/02-pretrain/). Throwing
that away to try a different feed-forward design is not the only option: the
tokenizer has not changed, so every row of the embedding table still means what
it meant, and every tensor downstream of it is still interpretable. That is the
whole precondition for surgery, and it is why this works between architectures
that share an embedding space and does not work between ones that do not.

What transfers, and what has to be invented:

| Tensor | What happens |
|---|---|
| embedding, tied head, every norm, every attention matrix | copied verbatim |
| `mlp.{gate,up,down}` | copied into **every** routed expert, identically |
| router | random, small |
| shared expert `down` (when present) | **zero** |

The two initialization choices are what make this safe rather than hopeful.
Top-k routing renormalises its weights to sum to one, so if every expert
computes the same function `F`, the block computes `w1*F(x) + w2*F(x) = F(x)` —
bit for bit the dense output. Zeroing a shared expert's output projection stops
it adding a second copy of the same thing.

So the upcycled model is *functionally identical to its parent at step 0*, and
that gives a hard acceptance test of the same species as stage 02's
`ln(vocab_size)` check: **the upcycled model must start at its parent's
validation loss, not at the untrained floor.** Any mistake in the remap shows
up there immediately. `verify` proves it on logits; `--val` proves it on the
real held-out data.

The model then diverges from step 1, because the random router sends different
tokens to different experts and each expert receives a different gradient. At
step 0 exactly, the router's own gradient is zero — identical experts make the
routing weights irrelevant to the output — and it becomes non-zero as soon as
the experts differ. That is a real property of the method, not an oversight.

What upcycling does *not* give you for free is compute. Activating two experts
of the parent's width means twice the feed-forward FLOPs per token. This file
prints active parameters next to total for that reason, and the comparison the
run record makes is against continuing to train the dense model, because that
is what the same GPU-hours would otherwise buy.

Usage:
    python upcycle.py convert ckpt.pt out.pt --experts 4 --active 2
    python upcycle.py verify out.pt --parent ckpt.pt
    python upcycle.py verify out.pt --parent ckpt.pt --data ~/tokens
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import torch


# Two files in this repository are both called `model.py` — the mission's dense
# reference and the ablation lesson's variant-configurable sibling — and this
# script needs both at once. Loading them by path under distinct names is the
# only way to hold both, and it is also the honest statement of what is
# happening: two independent implementations, compared against each other.
def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[4]
mission_model = _load(
    "mission_model", ROOT / "missions/01-language-model-agent/02-pretrain/core/model.py"
)
variants = _load("variant_model", ROOT / "missions/01-language-model-agent/02-pretrain/architecture-ablations/core/model.py")
VariantTransformer = variants.Transformer
VariantConfig = variants.VariantConfig
active_params = variants.active_params
real_params = variants.real_params


def variant_config_from(parent: dict, n_routed: int, n_active: int, n_shared: int) -> VariantConfig:
    """The MoE config that matches the parent everywhere except the FFN."""
    cfg = parent["config"]
    return VariantConfig(
        vocab_size=cfg["vocab_size"], n_layer=cfg["n_layer"], n_head=cfg["n_head"],
        n_kv_head=cfg["n_kv_head"], d_model=cfg["d_model"], d_ff=cfg["d_ff"],
        block_size=cfg["block_size"], rope_theta=cfg["rope_theta"],
        norm="rmsnorm", pos_scheme="rope", activation="swiglu",
        ffn="moe", n_routed_expert=n_routed, n_active_expert=n_active,
        n_shared_expert=n_shared, expert_d_ff=cfg["d_ff"],
    )


def remap(state: dict, cfg: VariantConfig, router_std: float,
          experts: str = "replicate", shared_down: str = "zero") -> dict:
    """Rename the parent's tensors into the MoE model's layout.

    Everything outside the feed-forward is a rename with no change of value.
    The feed-forward is a replication: one dense MLP becomes `n_routed_expert`
    identical experts. Nothing is averaged, interpolated, or resized — if a
    tensor's meaning would have to change, it is not copied at all.

    `experts` and `shared_down` exist so the two initialization choices can be
    turned off and the damage measured. They are not options anyone should use;
    they are the controls that prove the defaults are doing something. See the
    `ablate` subcommand.
    """
    out = {"tok.weight": state["tok.weight"], "norm.weight": state["norm.weight"]}
    generator = torch.Generator().manual_seed(0)
    for i in range(cfg.n_layer):
        src = f"blocks.{i}."
        for name in ("n1.weight", "n2.weight",
                     "attn.q.weight", "attn.k.weight", "attn.v.weight", "attn.o.weight"):
            out[src + name] = state[src + name]

        for e in range(cfg.n_routed_expert):
            for part in ("gate", "up", "down"):
                parent = state[f"{src}mlp.{part}.weight"]
                copied = experts == "replicate" or (experts == "first-only" and e == 0)
                out[f"{src}mlp.experts.{e}.{part}.weight"] = (
                    parent.clone() if copied
                    else torch.randn(parent.shape, generator=generator) * 0.02
                )
        for s in range(cfg.n_shared_expert):
            for part in ("gate", "up"):
                out[f"{src}mlp.shared.{s}.{part}.weight"] = state[f"{src}mlp.{part}.weight"].clone()
            # Zero, so the shared expert contributes nothing until it learns to.
            down = state[f"{src}mlp.down.weight"]
            out[f"{src}mlp.shared.{s}.down.weight"] = (
                torch.zeros_like(down) if shared_down == "zero" else down.clone()
            )

        out[f"{src}mlp.router.weight"] = torch.randn(
            cfg.n_routed_expert, cfg.d_model, generator=generator
        ) * router_std
        out[f"{src}mlp.bias"] = torch.zeros(cfg.n_routed_expert)
        out[f"{src}mlp.load"] = torch.zeros(cfg.n_routed_expert)
    return out


def load_parent(path: Path):
    parent = torch.load(path, map_location="cpu", weights_only=False)
    dense = mission_model.Transformer(mission_model.Config(**parent["config"]))
    dense.load_state_dict(parent["model"])
    return parent, dense


def convert(checkpoint: Path, out: Path, n_routed: int, n_active: int, n_shared: int,
            router_std: float) -> None:
    parent, _ = load_parent(checkpoint)
    cfg = variant_config_from(parent, n_routed, n_active, n_shared)
    state = remap(parent["model"], cfg, router_std)

    moe = VariantTransformer(cfg)
    missing, unexpected = moe.load_state_dict(state, strict=False)
    # `head.weight` is tied to `tok.weight`, so it is legitimately absent.
    assert [m for m in missing if m != "head.weight"] == [], f"missing tensors: {missing}"
    assert unexpected == [], f"unexpected tensors: {unexpected}"

    torch.save({"config": cfg.__dict__, "model": moe.state_dict(),
                "parent": str(checkpoint), "parent_step": parent.get("step"),
                "parent_tokens": parent.get("tokens_seen")}, out)

    dense_total = sum(p.numel() for p in mission_model.Transformer(
        mission_model.Config(**parent["config"])).parameters())
    print(f"parent   {dense_total:>12,} total {dense_total:>12,} active")
    print(f"upcycled {real_params(cfg):>12,} total {active_params(cfg):>12,} active"
          f"  ({active_params(cfg) / dense_total:.2f}x the compute per token)")
    print(f"wrote {out}")


def verify(upcycled: Path, parent_path: Path, data: Path | None, device: str,
           batch: int, iters: int) -> None:
    """Prove the surgery preserved the function, on logits and then on data."""
    _, dense = load_parent(parent_path)
    blob = torch.load(upcycled, map_location="cpu", weights_only=False)
    cfg = VariantConfig(**blob["config"])
    moe = VariantTransformer(cfg)
    moe.load_state_dict(blob["model"], strict=False)

    dense, moe = dense.to(device).eval(), moe.to(device).eval()
    torch.manual_seed(0)
    ids = torch.randint(0, cfg.vocab_size, (2, 128), device=device)
    with torch.no_grad():
        dense_logits, _ = dense(ids)
        moe_logits, _ = moe(ids)
    gap = (dense_logits - moe_logits).abs().max().item()
    print(f"max |logit difference| dense vs upcycled: {gap:.3e}")
    print("PASS: the upcycled model computes the parent's function"
          if gap < 1e-3 else "FAIL: the remap changed the model")

    if data is None:
        return
    val = np.memmap(data / "val.bin", dtype=np.uint16, mode="r")
    rng = np.random.default_rng(0)
    totals = {"parent": 0.0, "upcycled": 0.0}
    for _ in range(iters):
        starts = rng.integers(0, len(val) - cfg.block_size - 1, size=batch)
        x = torch.from_numpy(np.stack([val[s : s + cfg.block_size].astype(np.int64)
                                       for s in starts])).to(device)
        y = torch.from_numpy(np.stack([val[s + 1 : s + 1 + cfg.block_size].astype(np.int64)
                                       for s in starts])).to(device)
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            totals["parent"] += dense(x, y)[1].item()
            totals["upcycled"] += moe(x, y)[1].item()
    print(f"\nvalidation loss over {iters} batches of {batch}x{cfg.block_size} tokens")
    print(f"  parent   {totals['parent'] / iters:.4f}")
    print(f"  upcycled {totals['upcycled'] / iters:.4f}")
    print(f"  untrained floor would be ln({cfg.vocab_size}) = "
          f"{float(np.log(cfg.vocab_size)):.4f}")


@torch.no_grad()
def _val_loss(model, val, cfg, device: str, batch: int, iters: int) -> float:
    rng = np.random.default_rng(0)
    total = 0.0
    for _ in range(iters):
        starts = rng.integers(0, len(val) - cfg.block_size - 1, size=batch)
        x = torch.from_numpy(np.stack([val[s : s + cfg.block_size].astype(np.int64)
                                       for s in starts])).to(device)
        y = torch.from_numpy(np.stack([val[s + 1 : s + 1 + cfg.block_size].astype(np.int64)
                                       for s in starts])).to(device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            total += model(x, y)[1].item()
    return total / iters


# Each control turns off one initialization choice and keeps everything else.
# A control that scores near the parent was not load-bearing; one that scores
# near the untrained floor was.
CONTROLS = [
    ("replicate experts, zero shared", "replicate", "zero", 0.02),
    ("replicate experts, router zeroed", "replicate", "zero", 0.0),
    ("copy shared expert instead of zeroing", "replicate", "copy", 0.02),
    ("first expert copied, rest random", "first-only", "zero", 0.02),
    ("all experts random", "random", "zero", 0.02),
]


def ablate(parent_path: Path, data: Path, device: str, batch: int, iters: int,
           n_routed: int, n_active: int, n_shared: int) -> None:
    """Measure what each initialization choice is worth, by removing it.

    The README claims replication and the zeroed shared expert are what make
    the surgery exact. That claim is only worth making if the alternatives were
    tried, so this tries them and prints the damage.
    """
    parent, dense = load_parent(parent_path)
    val = np.memmap(data / "val.bin", dtype=np.uint16, mode="r")
    cfg = variant_config_from(parent, n_routed, n_active, n_shared)

    dense = dense.to(device).eval()
    floor = float(np.log(cfg.vocab_size))
    parent_loss = _val_loss(dense, val, cfg, device, batch, iters)
    print(f"{'parent (dense)':<42} {parent_loss:>8.4f}")

    for label, experts, shared_down, router_std in CONTROLS:
        shaped = cfg if shared_down == "zero" and n_shared else variant_config_from(
            parent, n_routed, n_active, max(n_shared, 1) if shared_down == "copy" else n_shared
        )
        moe = VariantTransformer(shaped)
        moe.load_state_dict(
            remap(parent["model"], shaped, router_std, experts, shared_down), strict=False
        )
        loss = _val_loss(moe.to(device).eval(), val, shaped, device, batch, iters)
        print(f"{label:<42} {loss:>8.4f}   {loss - parent_loss:+.4f} vs parent")
        del moe
        torch.cuda.empty_cache()

    print(f"{'untrained floor, ln(vocab)':<42} {floor:>8.4f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    conv = sub.add_parser("convert", help="dense checkpoint to MoE checkpoint")
    conv.add_argument("checkpoint", type=Path)
    conv.add_argument("out", type=Path)
    conv.add_argument("--experts", type=int, default=4)
    conv.add_argument("--active", type=int, default=2)
    conv.add_argument("--shared", type=int, default=0)
    conv.add_argument("--router-std", type=float, default=0.02)

    ver = sub.add_parser("verify", help="prove the surgery preserved the function")
    ver.add_argument("upcycled", type=Path)
    ver.add_argument("--parent", type=Path, required=True)
    ver.add_argument("--data", type=Path, default=None)
    ver.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ver.add_argument("--batch", type=int, default=8)
    ver.add_argument("--iters", type=int, default=20)

    abl = sub.add_parser("ablate", help="measure what each initialization choice is worth")
    abl.add_argument("--parent", type=Path, required=True)
    abl.add_argument("--data", type=Path, required=True)
    abl.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    abl.add_argument("--batch", type=int, default=8)
    abl.add_argument("--iters", type=int, default=20)
    abl.add_argument("--experts", type=int, default=4)
    abl.add_argument("--active", type=int, default=2)
    abl.add_argument("--shared", type=int, default=0)

    args = ap.parse_args()
    if args.command == "convert":
        convert(args.checkpoint, args.out, args.experts, args.active, args.shared,
                args.router_std)
    elif args.command == "ablate":
        ablate(args.parent, args.data, args.device, args.batch, args.iters,
               args.experts, args.active, args.shared)
    else:
        verify(args.upcycled, args.parent, args.data, args.device, args.batch, args.iters)


if __name__ == "__main__":
    main()
