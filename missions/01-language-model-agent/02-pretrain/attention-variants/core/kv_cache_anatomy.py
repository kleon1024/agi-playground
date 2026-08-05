"""The KV-cache arithmetic behind the attention variants.

Every attention variant that followed the original multi-head design is a
bet on the same tax: keys and values held in memory so decoding does not
recompute them. This script computes that tax for MHA, GQA, MQA, and MLA on
the measured stage-02 configuration (d_model 768, 12 layers, 12 query heads,
4 KV heads, bf16), so the architecture comparison in the chapter is
arithmetic on one page rather than a table someone typed in.

The formulas:

- KV bytes per token = 2 (K and V) * n_layer * n_kv_head * d_head * bytes.
  MHA holds every head's K and V; GQA shares n_kv_head groups; MQA shares a
  single head; MLA (DeepSeek-V2, 2024) compresses K and V into a low-rank
  latent of width kv_latent and a small per-token part, so its cache is
  driven by kv_latent, not n_head.
- Attention parameters per layer = q + k + v + o projections. MLA replaces
  the separate k/v projections with one latent projection, which is why its
  parameter story and its cache story differ.

The repo's own 88M decoder is the GQA row (n_kv_head=4); the serving stage
measured what this arithmetic predicts — a small cache that stops paying off
at toy context lengths because the engine's fixed costs dominate
(runs/2026-07-29-engine-bench-corrected.md). This script supplies the
theoretical cache; the serving run supplies the measured wall-clock.

Run:
    uv run --group torch python core/kv_cache_anatomy.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Anatomy:
    name: str
    n_kv_head: int
    kv_latent: int | None
    kv_bytes_per_token: int
    attn_params_per_layer: int
    note: str


def kv_mb(row: Anatomy, context: int) -> float:
    return row.kv_bytes_per_token * context / (1024 * 1024)


def main() -> None:
    # Measured stage-02 configuration (runs/2026-07-28-pretrain-3b.md).
    d_model = 768
    n_layer = 12
    n_head = 12
    d_head = d_model // n_head  # 64
    bytes_per_value = 2  # bf16

    def kv_bytes(n_kv_head: int) -> int:
        return 2 * n_layer * n_kv_head * d_head * bytes_per_value

    # MLA: DeepSeek-V2 compresses K and V into one latent of width kv_latent
    # plus a small per-token component; 512 is the reported latent width.
    kv_latent = 512
    mla_kv_bytes = 2 * n_layer * kv_latent * bytes_per_value

    def attn_params(n_kv_head: int) -> int:
        # q: d_model*d_model; k,v: d_model*(n_kv_head*d_head); o: d_model*d_model
        return d_model * d_model + 2 * d_model * (n_kv_head * d_head) + d_model * d_model

    rows = [
        Anatomy(
            "MHA (12 heads)",
            n_head,
            None,
            kv_bytes(n_head),
            attn_params(n_head),
            "the original design: every head holds its own K and V",
        ),
        Anatomy(
            "GQA (4 KV heads)",
            4,
            None,
            kv_bytes(4),
            attn_params(4),
            "this repo's decoder: KV shared across 3 query heads each",
        ),
        Anatomy(
            "MQA (1 KV head)",
            1,
            None,
            kv_bytes(1),
            attn_params(1),
            "the extreme share: one KV head for all 12 query heads",
        ),
        Anatomy(
            "MLA (latent 512)",
            n_head,
            kv_latent,
            mla_kv_bytes,
            d_model * d_model + d_model * kv_latent + d_model * d_model,
            "DeepSeek-V2: K/V compressed into one shared latent, wider d_head",
        ),
    ]

    print(f"stage-02 config: d_model={d_model}, n_layer={n_layer}, n_head={n_head}, "
          f"d_head={d_head}, bf16 ({bytes_per_value}B/value)")
    print()
    print(f"{'variant':<22}{'KV B/tok':>10}{'KV @1k':>10}{'KV @8k':>10}{'KV @32k':>11}"
          f"{'attn p/layer':>14}{'vs MHA':>9}")
    mha_kv = rows[0].kv_bytes_per_token
    for row in rows:
        ratio = row.kv_bytes_per_token / mha_kv
        print(
            f"{row.name:<22}{row.kv_bytes_per_token:>10}{kv_mb(row, 1024):>10.1f}"
            f"{kv_mb(row, 8192):>10.1f}{kv_mb(row, 32768):>11.1f}"
            f"{row.attn_params_per_layer:>14,}{ratio:>8.2f}x"
        )

    print()
    print("notes:")
    for row in rows:
        print(f"  {row.name}: {row.note}")
    print(
        "  MLA decode: its compressed cache is small, but decoding behaves as "
        "MQA with a very wide d_head, so per-token compute is high — the K3 "
        "article's MTP tension, not visible in bytes alone."
    )


if __name__ == "__main__":
    main()
