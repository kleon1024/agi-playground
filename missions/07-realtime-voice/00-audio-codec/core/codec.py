"""The smallest thing that turns a waveform into a discrete token sequence
and back: a convolutional encoder, a vector-quantization bottleneck, and a
convolutional decoder. This is the mechanism a real neural audio codec
(EnCodec, SoundStream) uses, minus their multi-scale residual quantizers and
adversarial loss -- a single codebook and a reconstruction loss are enough to
test this mission's actual question, which is what stage 01 does with the
resulting token sequence, not how good the audio sounds.

`DOWNSAMPLE = 64` means a 4096-sample clip becomes a 64-token sequence --
deliberately close to a short text prompt's length, since stage 01 needs to
hand this sequence to the same KV-cache decode loop mission 01 built for
text tokens.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F

DOWNSAMPLE = 64
LATENT_DIM = 32


@dataclass
class CodecConfig:
    codebook_size: int = 64
    latent_dim: int = LATENT_DIM
    hidden: int = 64


class Encoder(nn.Module):
    """4 stride-4 conv layers: 4x4x4x4 = 256... too much. Use stride 2 x 6
    layers (2^6 = 64) to hit DOWNSAMPLE exactly with a gentler receptive
    field growth per layer than a single big stride."""

    def __init__(self, cfg: CodecConfig):
        super().__init__()
        h = cfg.hidden
        chans = [1, h, h, h, h, h, h]
        layers = []
        for i in range(6):
            layers.append(nn.Conv1d(chans[i], chans[i + 1], kernel_size=4, stride=2, padding=1))
            layers.append(nn.GELU())
        self.net = nn.Sequential(*layers)
        self.proj = nn.Conv1d(h, cfg.latent_dim, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T) -> (B, 1, T)
        z = self.net(x.unsqueeze(1))
        return self.proj(z).transpose(1, 2)  # (B, T/64, latent_dim)


class Decoder(nn.Module):
    def __init__(self, cfg: CodecConfig):
        super().__init__()
        h = cfg.hidden
        self.proj = nn.Conv1d(cfg.latent_dim, h, kernel_size=1)
        chans = [h, h, h, h, h, h, 1]
        layers = []
        for i in range(6):
            out_ch = chans[i + 1]
            act = nn.GELU() if i < 5 else nn.Tanh()
            layers.append(nn.ConvTranspose1d(chans[i], out_ch, kernel_size=4, stride=2, padding=1))
            layers.append(act)
        self.net = nn.Sequential(*layers)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        # z: (B, T/64, latent_dim) -> (B, T)
        x = self.proj(z.transpose(1, 2))
        return self.net(x).squeeze(1)


class VectorQuantizer(nn.Module):
    """Straight-through VQ: nearest codebook entry on the forward pass,
    gradient passed through unchanged on the backward pass (the same trick
    that lets a discrete choice sit inside a differentiable training loop).
    """

    def __init__(self, cfg: CodecConfig):
        super().__init__()
        self.codebook = nn.Embedding(cfg.codebook_size, cfg.latent_dim)
        self.codebook.weight.data.uniform_(-1.0 / cfg.codebook_size, 1.0 / cfg.codebook_size)

    def forward(self, z: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # z: (B, N, D)
        flat = z.reshape(-1, z.shape[-1])
        dist = (
            flat.pow(2).sum(1, keepdim=True)
            - 2 * flat @ self.codebook.weight.t()
            + self.codebook.weight.pow(2).sum(1)
        )
        tokens = dist.argmin(1)
        z_q = self.codebook(tokens).view_as(z)

        commitment_loss = F.mse_loss(z_q.detach(), z) + F.mse_loss(z_q, z.detach())
        z_q_st = z + (z_q - z).detach()  # straight-through
        return z_q_st, tokens.view(z.shape[0], z.shape[1]), commitment_loss


class Codec(nn.Module):
    def __init__(self, cfg: CodecConfig | None = None):
        super().__init__()
        self.cfg = cfg or CodecConfig()
        self.encoder = Encoder(self.cfg)
        self.vq = VectorQuantizer(self.cfg)
        self.decoder = Decoder(self.cfg)

    def forward(self, waveform: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        z = self.encoder(waveform)
        z_q, tokens, vq_loss = self.vq(z)
        recon = self.decoder(z_q)
        return recon, tokens, vq_loss

    @torch.no_grad()
    def encode(self, waveform: torch.Tensor) -> torch.Tensor:
        z = self.encoder(waveform)
        _, tokens, _ = self.vq(z)
        return tokens

    @torch.no_grad()
    def decode(self, tokens: torch.Tensor) -> torch.Tensor:
        z_q = self.vq.codebook(tokens)
        return self.decoder(z_q)
