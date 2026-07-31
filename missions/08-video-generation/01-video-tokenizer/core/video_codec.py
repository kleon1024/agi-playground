"""A per-frame VQ-VAE that turns an 8-frame clip into an 8-token discrete
sequence, one token per frame -- the smallest thing that answers stage 00's
open question: how do frames become a token sequence a decoder can attend
over?

The vector-quantization bottleneck (`VectorQuantizer`, the straight-through
nearest-codebook-entry mechanism) is imported directly, unmodified, from
mission 07's audio codec -- the same discrete-bottleneck code, generalized
from a per-chunk audio latent to a per-frame video latent by construction: it
already operates on generic `(B, N, D)` sequences, so nothing about it is
audio-specific. What is genuinely new here is the `Encoder`/`Decoder` pair:
2D strided convolutions instead of 1D, applied independently to each of a
clip's 8 frames (no cross-frame mixing inside the codec itself -- temporal
structure is left entirely to stage 02's sequence model, the same division
of labor mission 07 uses between its codec and its streaming-decode LM).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn

AUDIO_CODEC_CORE = (
    Path(__file__).resolve().parents[3] / "07-realtime-voice" / "00-audio-codec" / "core"
)
sys.path.insert(0, str(AUDIO_CODEC_CORE))
from codec import VectorQuantizer

DATASET_CORE = (
    Path(__file__).resolve().parents[3] / "08-video-generation" / "00-synthetic-video-dataset" / "core"
)
sys.path.insert(0, str(DATASET_CORE))
from generate_video_dataset import HEIGHT, N_FRAMES, WIDTH

LATENT_DIM = 32


@dataclass
class CodecConfig:
    codebook_size: int = 64
    latent_dim: int = LATENT_DIM
    hidden: int = 32


class Encoder(nn.Module):
    """(B, T, 3, 32, 32) -> (B, T, latent_dim). Each frame is downsampled
    independently: three stride-2 conv layers take 32x32 to 4x4, then a
    kernel-4 conv collapses the remaining 4x4 spatial grid to a single
    latent vector per frame -- 32 -> 16 -> 8 -> 4 -> 1."""

    def __init__(self, cfg: CodecConfig):
        super().__init__()
        h = cfg.hidden
        self.net = nn.Sequential(
            nn.Conv2d(3, h, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.Conv2d(h, h, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.Conv2d(h, h, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.Conv2d(h, cfg.latent_dim, kernel_size=4, stride=1, padding=0),
        )

    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        B, T = frames.shape[:2]
        x = frames.reshape(B * T, 3, HEIGHT, WIDTH)
        z = self.net(x)  # (B*T, latent_dim, 1, 1)
        return z.view(B, T, -1)


class Decoder(nn.Module):
    """(B, T, latent_dim) -> (B, T, 3, 32, 32), the exact mirror of Encoder:
    1 -> 4 -> 8 -> 16 -> 32.

    Deliberately no final `Tanh`, unlike mission 07's audio decoder. A pilot
    run of this codec with a `Tanh` output saturated within the first ~20-50
    steps -- background covers over 85% of every frame's pixels by
    construction, so the fastest way to reduce MSE is to push every output
    to the saturated +1 (white) tail, and once there `tanh`'s local gradient
    is near zero, so the decoder becomes numerically insensitive to which
    code it receives (max output difference between two very different
    codebook entries measured at 0.001) and training permanently plateaus at
    the background baseline, confirmed on both a full-dataset run and an
    8-clip overfit control (see `runs/`). Dropping the bounded activation
    removes the saturation trap entirely: MSE against a target already in
    [-1, 1] keeps a well-behaved gradient for an unbounded linear output, and
    the same 8-clip overfit control that plateaued at the baseline with
    `Tanh` reaches 0.059 (29% below the 0.083 baseline) and is still falling
    once `Tanh` is removed."""

    def __init__(self, cfg: CodecConfig):
        super().__init__()
        h = cfg.hidden
        self.net = nn.Sequential(
            nn.ConvTranspose2d(cfg.latent_dim, h, kernel_size=4, stride=1, padding=0),
            nn.GELU(),
            nn.ConvTranspose2d(h, h, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.ConvTranspose2d(h, h, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.ConvTranspose2d(h, 3, kernel_size=4, stride=2, padding=1),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        B, T, D = z.shape
        x = z.view(B * T, D, 1, 1)
        frames = self.net(x)  # (B*T, 3, 32, 32)
        return frames.view(B, T, 3, HEIGHT, WIDTH)


class VideoCodec(nn.Module):
    def __init__(self, cfg: CodecConfig | None = None):
        super().__init__()
        self.cfg = cfg or CodecConfig()
        self.encoder = Encoder(self.cfg)
        self.vq = VectorQuantizer(self.cfg)
        self.decoder = Decoder(self.cfg)

    def forward(self, clip: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # clip: (B, T, 3, H, W) in [-1, 1]
        z = self.encoder(clip)
        z_q, tokens, vq_loss = self.vq(z)
        recon = self.decoder(z_q)
        return recon, tokens, vq_loss

    @torch.no_grad()
    def encode(self, clip: torch.Tensor) -> torch.Tensor:
        z = self.encoder(clip)
        _, tokens, _ = self.vq(z)
        return tokens  # (B, T)

    @torch.no_grad()
    def decode(self, tokens: torch.Tensor) -> torch.Tensor:
        z_q = self.vq.codebook(tokens)
        return self.decoder(z_q)


assert N_FRAMES == 8  # this codec's Config/README numbers assume stage 00's clip length
