"""The same surgery on a real `safetensors` checkpoint, with no custom model.

`../core/` loads two of this repository's own model classes and moves tensors
between them. That is the clearest way to see the mechanism, and it invites the
wrong conclusion — that upcycling needs a bespoke implementation. It does not.
A checkpoint is a dictionary from names to tensors, and the surgery is a
rewrite of that dictionary plus a rewrite of the config JSON beside it.

This file does exactly that against a Hugging Face dense checkpoint, producing a
directory that a mixture-of-experts model class will load. It never instantiates
the parent model at all.

The precondition is the same one `../core/` states and it is worth repeating
because `safetensors` will not check it for you: **the tokenizer and
`hidden_size` must be unchanged.** Nothing here validates that the target
architecture agrees with the source about what token id 4,102 means. If it does
not, every tensor still loads and the model is silently wrong — which is why the
acceptance test is a loss comparison against the parent and not a successful
load.

Expert tensor layouts differ between implementations, and getting this wrong is
the most likely mistake:

- `Qwen3MoeForCausalLM` and `MixtralForCausalLM` store one module per expert,
  `...mlp.experts.{i}.{gate,up,down}_proj.weight`, each `[d_ff, d_model]` or
  `[d_model, d_ff]` exactly as the dense model stored it. `--layout modules`.
- Newer fused implementations store a single stacked tensor per projection,
  `...mlp.experts.gate_up_proj` of shape `[n_expert, d_model, 2*d_ff]`, which
  is both transposed and interleaved relative to the dense weights.
  `--layout fused`.

Run `--inspect` against the target architecture's own randomly-initialised
checkpoint before trusting either. Reading the names it actually wants takes a
minute; debugging a model that loads and produces noise takes considerably
longer.

Requires: `pip install safetensors torch transformers`.

Usage:
    python upcycle_hf.py --inspect Qwen/Qwen3-30B-A3B
    python upcycle_hf.py --src HuggingFaceTB/SmolLM2-135M --out ./smol-moe \
        --experts 4 --active 2 --layout modules
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import torch


def load_state(src: str) -> dict[str, torch.Tensor]:
    """Every shard of a checkpoint, flattened into one dictionary."""
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file

    local = Path(src) if Path(src).exists() else Path(snapshot_download(src))
    shards = sorted(local.glob("*.safetensors"))
    if not shards:
        raise SystemExit(f"no safetensors in {local}")
    state: dict[str, torch.Tensor] = {}
    for shard in shards:
        state.update(load_file(str(shard)))
    return state


def inspect(src: str) -> None:
    """Print the expert tensor names a checkpoint actually uses.

    The point of this subcommand is that guessing is expensive and looking is
    cheap. Run it against the architecture you are targeting.
    """
    state = load_state(src)
    experts = {k for k in state if "expert" in k or "mlp" in k}
    for name in sorted(experts)[:24]:
        print(f"{name:<64} {tuple(state[name].shape)}")
    print(f"\n{len(experts)} feed-forward tensors, {len(state)} total")


def upcycle(state: dict[str, torch.Tensor], n_expert: int, layout: str,
            router_std: float, seed: int) -> dict[str, torch.Tensor]:
    """Replicate each dense MLP into `n_expert` identical experts.

    Identical is deliberate. Top-k routing renormalises its weights to sum to
    one, so identical experts reproduce the dense output exactly regardless of
    what the random router does, and the converted model starts at its parent's
    loss instead of somewhere unverifiable.
    """
    generator = torch.Generator().manual_seed(seed)
    pattern = re.compile(r"^(.*\.layers\.(\d+)\.mlp)\.(gate|up|down)_proj\.weight$")
    out: dict[str, torch.Tensor] = {}
    layers: dict[str, dict[str, torch.Tensor]] = {}

    for name, tensor in state.items():
        match = pattern.match(name)
        if match is None:
            out[name] = tensor
            continue
        layers.setdefault(match.group(1), {})[match.group(3)] = tensor

    for prefix, parts in layers.items():
        d_model = parts["gate"].shape[1]
        if layout == "modules":
            for e in range(n_expert):
                for part, tensor in parts.items():
                    out[f"{prefix}.experts.{e}.{part}_proj.weight"] = tensor.clone()
        else:
            # Fused: stacked over experts, and transposed relative to nn.Linear.
            gate_up = torch.cat([parts["gate"], parts["up"]], dim=0).t().contiguous()
            out[f"{prefix}.experts.gate_up_proj"] = gate_up.unsqueeze(0).repeat(n_expert, 1, 1)
            down = parts["down"].t().contiguous()
            out[f"{prefix}.experts.down_proj"] = down.unsqueeze(0).repeat(n_expert, 1, 1)

        out[f"{prefix}.gate.weight"] = torch.randn(
            n_expert, d_model, generator=generator, dtype=torch.float32
        ).to(parts["gate"].dtype) * router_std

    return out


def rewrite_config(src: str, out_dir: Path, n_expert: int, n_active: int) -> None:
    """The config has to describe the new shape, or the tensors will not load."""
    from transformers import AutoConfig

    cfg = AutoConfig.from_pretrained(src).to_dict()
    cfg["num_experts"] = cfg["num_local_experts"] = n_expert
    cfg["num_experts_per_tok"] = n_active
    # The experts keep the parent's width; capacity comes from their number.
    cfg["moe_intermediate_size"] = cfg["intermediate_size"]
    (out_dir / "config.json").write_text(json.dumps(cfg, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inspect", metavar="REPO", default=None,
                    help="print a checkpoint's expert tensor names and exit")
    ap.add_argument("--src", default=None, help="dense checkpoint repo or path")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--experts", type=int, default=4)
    ap.add_argument("--active", type=int, default=2)
    ap.add_argument("--layout", choices=["modules", "fused"], default="modules")
    ap.add_argument("--router-std", type=float, default=0.02)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if args.inspect:
        inspect(args.inspect)
        return
    if not args.src or not args.out:
        raise SystemExit("--src and --out are required unless --inspect is given")

    from safetensors.torch import save_file

    state = upcycle(load_state(args.src), args.experts, args.layout,
                    args.router_std, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    save_file(state, str(args.out / "model.safetensors"), metadata={"format": "pt"})
    rewrite_config(args.src, args.out, args.experts, args.active)

    total = sum(t.numel() for t in state.values())
    print(f"wrote {args.out}: {len(state)} tensors, {total:,} parameters")
    print(
        "\nThis wrote a checkpoint. It did not verify one. Before trusting it, "
        "score it on held-out data and confirm it matches the parent — an "
        "upcycled model that starts anywhere but its parent's loss has a "
        "tensor in the wrong place, and it will load without complaint."
    )


if __name__ == "__main__":
    main()
