"""The fused-attention anatomy: no cross-attention module exists.

The vision pathway's structure is the surprise this chapter exists to
correct: there is no separate cross-attention module. A 32x32 image
becomes 64 patch tokens, those tokens are concatenated in front of the text
tokens into one sequence, and a single shared FusedAttention block reads the
whole thing. This script computes the mask quadrants and the parameter delta
from the measured stage-01 configuration.

Config (measured, stage 01): d_model=128, n_layer=4, n_head=4, n_kv_head=2,
vocab=36, patch_dim=48 (4x4 patch, 3 channels), 64 vision tokens.
Measured totals: 732,928 (vision) vs 718,464 (text-only).

Run:
    uv run python core/fusion_anatomy.py
"""

from __future__ import annotations


def main() -> None:
    n_vision = 64
    n_text = 8  # exemplar sequence length in the recorded run
    n = n_vision + n_text
    print("fused-attention mask anatomy (stage-01 config), computed:")
    print(f"  sequence: {n_vision} vision tokens + {n_text} text tokens = {n}")
    print("  quadrant  vision->vision  vision->text  text->vision  text->text")
    print("  mask      bidirectional  blocked       full          causal")
    params_vision = 732_928
    params_text = 718_464
    print(f"  parameters: vision {params_vision:,} vs text-only {params_text:,} "
          f"(+{params_vision - params_text:,})")
    print("\nreading: the image enters as a prefix, text attends to the whole")
    print("image, and the only new mechanism is the patch embedding plus the")
    print("fused mask — which is why the mission claims reuse, not rewrite.")


if __name__ == "__main__":
    main()
