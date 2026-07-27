"""The same ladder, through a production model library instead of hand-rolled
`nn.Module`s.

`core/model.py` turns RMSNorm, RoPE, SwiGLU, GQA, and depth-vs-width into
fields on one config class, because it is one hand-written block and every
field is a branch inside it. HuggingFace `transformers`' `LlamaConfig` already
ships RMSNorm, RoPE, SwiGLU, and `num_key_value_heads` (GQA) as first-class,
independently settable fields on a real, widely-deployed architecture — so the
`gqa` and `depth-width` rungs below are one-line config changes, not a
reimplementation.

The `norm`, `position`, and `activation` rungs expose the gap `core/` does not
have: no shipped HuggingFace config lets you keep everything else fixed and
flip only the norm, only the position scheme, or only the activation.
`LlamaConfig` always uses RMSNorm + RoPE + SwiGLU; a config with LayerNorm +
learned absolute positions + a GELU MLP is a different model family
(`GPT2Config`), not a different field. So this script's honest stand-in for
those three rungs is `LlamaForCausalLM` against `GPT2LMHeadModel`, matched by
parameter count with `transformers`' own `num_parameters()` — the real-tool
equivalent of comparing two named points in architecture space, not a clean
per-variable toggle. That gap is itself worth reporting: a from-scratch file
can isolate one variable because it is one file; a library that offers several
named, battle-tested architectures cannot always offer the same isolation
without becoming a sixth architecture nobody deploys.

Requires: `transformers` (not in this repo's base dependency group — install
separately, e.g. `uv run --with transformers python hf_ladder.py`).

Run:  uv run --with transformers python hf_ladder.py --rung gqa
"""

from __future__ import annotations

import argparse

from transformers import (
    AutoModelForCausalLM,
    GPT2Config,
    LlamaConfig,
)

RUNGS = ("norm-position-activation", "gqa", "depth-width")

# Sized to land in the same few-million-parameter range as core/model.py's
# control config, so the two files are describing comparably small models.
VOCAB = 1024
D_MODEL = 256
N_LAYER = 4
N_HEAD = 8
BLOCK_SIZE = 128


def llama_arm(**overrides) -> LlamaConfig:
    cfg = {
        "vocab_size": VOCAB,
        "hidden_size": D_MODEL,
        "intermediate_size": round(D_MODEL * 4 * 2 / 3),  # SwiGLU's 2/3 convention
        "num_hidden_layers": N_LAYER,
        "num_attention_heads": N_HEAD,
        "num_key_value_heads": N_HEAD,
        "max_position_embeddings": BLOCK_SIZE,
        "tie_word_embeddings": True,
    }
    cfg.update(overrides)
    return LlamaConfig(**cfg)


def gpt2_arm(**overrides) -> GPT2Config:
    cfg = {
        "vocab_size": VOCAB,
        "n_embd": D_MODEL,
        "n_layer": N_LAYER,
        "n_head": N_HEAD,
        "n_positions": BLOCK_SIZE,
        "tie_word_embeddings": True,
    }
    cfg.update(overrides)
    return GPT2Config(**cfg)


def param_count(config) -> int:
    return AutoModelForCausalLM.from_config(config).num_parameters()


def run_norm_position_activation() -> None:
    """RMSNorm+RoPE+SwiGLU vs LayerNorm+learned+GELU — the model-family gap.

    Neither config's parameter count is tuned to match the other by hand; both
    are built from the same (vocab, d_model, n_layer, n_head, block_size)
    inputs and left to land wherever their respective architectures put them.
    Reporting that gap, rather than hiding it behind a forced match, is the
    point: it is what "the real tool doesn't expose this as one flag" costs.
    """
    llama, gpt2 = llama_arm(), gpt2_arm()
    n_llama, n_gpt2 = param_count(llama), param_count(gpt2)
    print(f"llama  (rmsnorm, rope, swiglu):   {n_llama:,} params")
    print(f"gpt2   (layernorm, learned, gelu): {n_gpt2:,} params")
    print(f"delta: {n_llama - n_gpt2:+,} ({abs(n_llama - n_gpt2) / n_gpt2:.1%} of gpt2)")


def run_gqa() -> None:
    """A one-field ladder: `num_key_value_heads` at several group sizes."""
    for kv in sorted({N_HEAD, N_HEAD // 2, N_HEAD // 4, 1}):
        n = param_count(llama_arm(num_key_value_heads=kv))
        print(f"kv{kv}: {n:,} params")


def run_depth_width() -> None:
    """Depth vs width, matched to the control's parameter count.

    `core/model.py`'s `depth_width_arms` searches for the matching width by
    hand because it has no framework to ask. Here the search loop is the
    same idea, just against `LlamaConfig` instead of a hand-written formula —
    the arithmetic a production config still needs is unchanged, only the
    model construction is not hand-rolled.
    """
    target = param_count(llama_arm())
    for n_layer in (max(1, N_LAYER // 2), N_LAYER, N_LAYER * 2):
        best_hidden, best_gap = D_MODEL, None
        for hidden in range(64, 1025, 8):
            if hidden % (2 * N_HEAD) != 0:
                continue
            n = param_count(llama_arm(num_hidden_layers=n_layer, hidden_size=hidden))
            gap = abs(n - target)
            if best_gap is None or gap < best_gap:
                best_gap, best_hidden = gap, hidden
        n = param_count(llama_arm(num_hidden_layers=n_layer, hidden_size=best_hidden))
        print(f"L{n_layer}-d{best_hidden}: {n:,} params (delta {n - target:+,})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rung", choices=RUNGS, default="gqa")
    args = ap.parse_args()

    if args.rung == "norm-position-activation":
        run_norm_position_activation()
    elif args.rung == "gqa":
        run_gqa()
    elif args.rung == "depth-width":
        run_depth_width()


if __name__ == "__main__":
    main()
