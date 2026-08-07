"""Does a standard dead-code-reset fix stage 04's seed-dependent codebook
utilization (18-63 of 64 codes used across seeds at 10 speakers, versus a
tight 51-63 at 1-2 speakers)?

Reuses `Codec`/`CodecConfig`/`Encoder`/`Decoder` from stage 00 unchanged --
only the `VectorQuantizer` is replaced with `ResetVectorQuantizer` below,
which tracks an EMA cluster-size estimate per codebook entry and, every
`reset_every` steps, reinitializes any entry whose EMA count has fallen
below `dead_threshold` to a random encoder output from the current batch
(plus small noise) -- the same dead-code-revival mechanism VQ-VAE-2
(Razavi, van den Oord & Vinyals, 2019, NeurIPS) uses for its EMA codebook
update, applied here to this mission's straight-through VQ instead of a
full EMA-updated codebook, since only the dead-code-reset piece is under
test -- adding EMA embedding updates too would confound which mechanism did
the work.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

CODEC_DIR = Path(__file__).resolve().parents[2] / "00-audio-codec" / "core"
sys.path.insert(0, str(CODEC_DIR))
from codec import CodecConfig, Decoder, Encoder


@dataclass
class ResetConfig:
    reset_every: int = 50
    dead_threshold: float = 1.0
    ema_decay: float = 0.99
    noise_std: float = 0.01


class ResetVectorQuantizer(nn.Module):
    """Same straight-through VQ as stage 00, plus an EMA dead-code counter
    and periodic reinitialization of codes that have gone unused."""

    def __init__(self, cfg: CodecConfig, reset_cfg: ResetConfig):
        super().__init__()
        self.codebook = nn.Embedding(cfg.codebook_size, cfg.latent_dim)
        self.codebook.weight.data.uniform_(-1.0 / cfg.codebook_size, 1.0 / cfg.codebook_size)
        self.reset_cfg = reset_cfg
        self.register_buffer("ema_cluster_size", torch.ones(cfg.codebook_size))
        self.step = 0
        self.resets_performed = 0
        self.reset_log: list[dict] = []

    def forward(self, z: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        flat = z.reshape(-1, z.shape[-1])
        dist = (
            flat.pow(2).sum(1, keepdim=True)
            - 2 * flat @ self.codebook.weight.t()
            + self.codebook.weight.pow(2).sum(1)
        )
        tokens = dist.argmin(1)
        z_q = self.codebook(tokens).view_as(z)

        commitment_loss = F.mse_loss(z_q.detach(), z) + F.mse_loss(z_q, z.detach())
        z_q_st = z + (z_q - z).detach()

        if self.training:
            with torch.no_grad():
                counts = torch.bincount(tokens, minlength=self.codebook.num_embeddings).float()
                self.ema_cluster_size.mul_(self.reset_cfg.ema_decay).add_(
                    counts, alpha=1 - self.reset_cfg.ema_decay
                )
                self.step += 1
                if self.step % self.reset_cfg.reset_every == 0:
                    self._reset_dead_codes(flat)

        return z_q_st, tokens.view(z.shape[0], z.shape[1]), commitment_loss

    def _reset_dead_codes(self, flat_batch: torch.Tensor) -> None:
        dead = (self.ema_cluster_size < self.reset_cfg.dead_threshold).nonzero(as_tuple=True)[0]
        if dead.numel() == 0:
            return
        n_batch = flat_batch.shape[0]
        replacement_idx = torch.randint(0, n_batch, (dead.numel(),))
        replacements = flat_batch[replacement_idx] + self.reset_cfg.noise_std * torch.randn(
            dead.numel(), flat_batch.shape[1]
        )
        self.codebook.weight.data[dead] = replacements
        self.ema_cluster_size[dead] = 1.0
        self.resets_performed += int(dead.numel())
        self.reset_log.append({"step": self.step, "n_reset": int(dead.numel())})


class ResetCodec(nn.Module):
    """Same encoder/decoder as stage 00's `Codec`, with `ResetVectorQuantizer`
    swapped in for the plain `VectorQuantizer`."""

    def __init__(self, cfg: CodecConfig | None = None, reset_cfg: ResetConfig | None = None):
        super().__init__()
        self.cfg = cfg or CodecConfig()
        self.reset_cfg = reset_cfg or ResetConfig()
        self.encoder = Encoder(self.cfg)
        self.vq = ResetVectorQuantizer(self.cfg, self.reset_cfg)
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
