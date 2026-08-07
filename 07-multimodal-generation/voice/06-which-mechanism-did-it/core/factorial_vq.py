"""One quantizer, two independent switches, so the confound stage 05 avoided
can be measured instead of dodged.

Stage 05 tested dead-code reset alone and said why it stopped there: adding
EMA-updated codebook embeddings on top "would confound which mechanism did
the work." That is true of a two-arm comparison. It stops being true the
moment all four cells exist, because with reset in {off, on} crossed against
EMA in {off, on}, each mechanism's effect is the difference between two
cells that differ in that mechanism alone -- twice over, once at each level
of the other switch. If those two differences disagree, the mechanisms
interact, and that is itself the answer rather than a spoiled experiment.

The two mechanisms are genuinely different things, which is why they can be
crossed at all:

- **Dead-code reset** changes *which* codebook entries exist. Every
  `reset_every` steps, any entry whose EMA usage count has fallen below
  `dead_threshold` is reinitialized to a random encoder output from the
  current batch. It is a rescue for entries the encoder has abandoned.
- **EMA codebook update** changes *how* the surviving entries move. Instead
  of the optimizer pulling `codebook.weight` toward the encoder outputs via
  the commitment loss, each entry is set to a decayed running average of the
  encoder outputs currently assigned to it -- van den Oord et al.'s original
  alternative to the gradient update, carried into VQ-VAE-2.

They are not alternatives. Reset decides membership; EMA decides position.

## The loss term that has to move with the switch

With the EMA update on, the codebook is no longer a gradient-trained
parameter, so the half of the commitment loss that pulls the *codebook*
toward the encoder (`F.mse_loss(z_q, z.detach())`) has no parameter left to
update and must be dropped -- keeping it would leave a term whose gradient
lands on a tensor the EMA rule overwrites moments later. Only the half that
pulls the *encoder* toward the codebook survives. This is not a tuning
choice; it is what makes the EMA arm the mechanism it claims to be, and
`arm_a_matches_stage_00` below checks that the (off, off) corner is still
bit-for-bit stage 00's plain quantizer.
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
from codec import CodecConfig, Decoder, Encoder, VectorQuantizer


@dataclass(frozen=True)
class ArmConfig:
    """One cell of the 2x2. `label` is what the run record calls it."""

    dead_code_reset: bool
    ema_codebook: bool
    reset_every: int = 50
    dead_threshold: float = 1.0
    ema_decay: float = 0.99
    noise_std: float = 0.01
    epsilon: float = 1e-5  # Laplace smoothing on the EMA cluster sizes

    @property
    def label(self) -> str:
        if self.dead_code_reset and self.ema_codebook:
            return "reset+ema"
        if self.dead_code_reset:
            return "reset-only"
        if self.ema_codebook:
            return "ema-only"
        return "plain"


ARMS = (
    ArmConfig(dead_code_reset=False, ema_codebook=False),
    ArmConfig(dead_code_reset=True, ema_codebook=False),
    ArmConfig(dead_code_reset=False, ema_codebook=True),
    ArmConfig(dead_code_reset=True, ema_codebook=True),
)


class FactorialVectorQuantizer(nn.Module):
    """Stage 00's straight-through VQ with each mechanism behind its own flag."""

    def __init__(self, cfg: CodecConfig, arm: ArmConfig):
        super().__init__()
        self.arm = arm
        self.codebook = nn.Embedding(cfg.codebook_size, cfg.latent_dim)
        self.codebook.weight.data.uniform_(-1.0 / cfg.codebook_size, 1.0 / cfg.codebook_size)
        if arm.ema_codebook:
            # An EMA-updated codebook is state, not a parameter -- handing it
            # to the optimizer as well would apply two competing update rules
            # to the same tensor.
            self.codebook.weight.requires_grad_(False)
        self.register_buffer("ema_cluster_size", torch.ones(cfg.codebook_size))
        self.register_buffer("ema_weight_sum", self.codebook.weight.data.clone())
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

        if self.arm.ema_codebook:
            # Only the encoder-side pull survives; see the module docstring.
            commitment_loss = F.mse_loss(z_q.detach(), z)
        else:
            commitment_loss = F.mse_loss(z_q.detach(), z) + F.mse_loss(z_q, z.detach())

        z_q_st = z + (z_q - z).detach()  # straight-through, both arms

        if self.training:
            with torch.no_grad():
                counts = torch.bincount(tokens, minlength=self.codebook.num_embeddings).float()
                self.ema_cluster_size.mul_(self.arm.ema_decay).add_(
                    counts, alpha=1 - self.arm.ema_decay
                )
                if self.arm.ema_codebook:
                    self._ema_update(flat, tokens)
                self.step += 1
                if self.arm.dead_code_reset and self.step % self.arm.reset_every == 0:
                    self._reset_dead_codes(flat)

        return z_q_st, tokens.view(z.shape[0], z.shape[1]), commitment_loss

    def _ema_update(self, flat: torch.Tensor, tokens: torch.Tensor) -> None:
        """Each entry becomes the decayed mean of the encoder outputs assigned
        to it. Laplace smoothing keeps an entry with zero current assignments
        from dividing by zero -- it holds position instead of exploding."""
        onehot = F.one_hot(tokens, self.codebook.num_embeddings).float()  # (N, K)
        batch_sum = onehot.t() @ flat  # (K, D)
        self.ema_weight_sum.mul_(self.arm.ema_decay).add_(batch_sum, alpha=1 - self.arm.ema_decay)

        n = self.ema_cluster_size.sum()
        k = self.codebook.num_embeddings
        smoothed = (self.ema_cluster_size + self.arm.epsilon) / (n + k * self.arm.epsilon) * n
        self.codebook.weight.data.copy_(self.ema_weight_sum / smoothed.unsqueeze(1))

    def _reset_dead_codes(self, flat_batch: torch.Tensor) -> None:
        dead = (self.ema_cluster_size < self.arm.dead_threshold).nonzero(as_tuple=True)[0]
        if dead.numel() == 0:
            return
        replacement_idx = torch.randint(0, flat_batch.shape[0], (dead.numel(),))
        replacements = flat_batch[replacement_idx] + self.arm.noise_std * torch.randn(
            dead.numel(), flat_batch.shape[1]
        )
        self.codebook.weight.data[dead] = replacements
        self.ema_cluster_size[dead] = 1.0
        if self.arm.ema_codebook:
            # A revived entry's running sum has to be restated against its new
            # position, or the next EMA step drags it straight back to where
            # the encoder had already stopped sending anything.
            self.ema_weight_sum[dead] = replacements
        self.resets_performed += int(dead.numel())
        self.reset_log.append({"step": self.step, "n_reset": int(dead.numel())})


class FactorialCodec(nn.Module):
    """Stage 00's encoder and decoder, unmodified, around the switched VQ."""

    def __init__(self, cfg: CodecConfig | None = None, arm: ArmConfig | None = None):
        super().__init__()
        self.cfg = cfg or CodecConfig()
        self.arm = arm or ARMS[0]
        self.encoder = Encoder(self.cfg)
        self.vq = FactorialVectorQuantizer(self.cfg, self.arm)
        self.decoder = Decoder(self.cfg)

    def forward(self, waveform: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        z = self.encoder(waveform)
        z_q, tokens, vq_loss = self.vq(z)
        recon = self.decoder(z_q)
        return recon, tokens, vq_loss


def arm_a_matches_stage_00(seed: int = 0, n_batch: int = 8) -> dict:
    """The (off, off) corner must be stage 00's quantizer, or the whole 2x2
    is measured against a baseline that is not the mission's own baseline.

    Checked by forward pass rather than by reading the code: same seed, same
    input, same initial codebook, and every output tensor compared exactly.
    """
    cfg = CodecConfig()

    torch.manual_seed(seed)
    reference = VectorQuantizer(cfg)
    torch.manual_seed(seed)
    candidate = FactorialVectorQuantizer(cfg, ARMS[0])
    candidate.train()
    reference.train()

    torch.manual_seed(seed + 1)
    z = torch.randn(n_batch, 16, cfg.latent_dim)

    ref_zq, ref_tokens, ref_loss = reference(z)
    cand_zq, cand_tokens, cand_loss = candidate(z)

    return {
        "codebook_init_identical": torch.equal(reference.codebook.weight, candidate.codebook.weight),
        "quantized_identical": torch.equal(ref_zq, cand_zq),
        "tokens_identical": torch.equal(ref_tokens, cand_tokens),
        "commitment_loss_identical": ref_loss.item() == cand_loss.item(),
        "reference_loss": ref_loss.item(),
        "candidate_loss": cand_loss.item(),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(arm_a_matches_stage_00(), indent=2))
