"""A small decoder whose forward pass can be driven by embeddings, not only ids.

Every other model in this repository takes token ids and looks them up. That is
the right interface until the moment you want the model's *own* output to be
its next input without passing through the vocabulary, which is exactly what a
continuous thought is. So this one splits the two halves apart:

    embed(ids) -> vectors        the lookup, on its own
    forward(vectors) -> hidden, logits    the network, on its own

With those separated, a latent step is three lines: run the network, take the
last hidden state, write it into the next input slot. Nothing else changes —
same blocks, same attention, same objective. The mechanism this chapter is
about is a plumbing change, and keeping the model this plain is what makes that
visible.

Deliberately smaller and simpler than the rest of the curriculum's models:
learned absolute positions rather than RoPE, LayerNorm rather than RMSNorm, no
GQA. None of those choices interact with the question being asked, and every
one of them removes a paragraph the reader would have to hold in their head.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F


@dataclass(frozen=True)
class Config:
    vocab_size: int = 51
    n_layer: int = 6
    n_head: int = 4
    d_model: int = 128
    block_size: int = 256
    dropout: float = 0.0


class Block(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.n1 = nn.LayerNorm(cfg.d_model)
        self.attn = nn.MultiheadAttention(
            cfg.d_model, cfg.n_head, dropout=cfg.dropout, batch_first=True
        )
        self.n2 = nn.LayerNorm(cfg.d_model)
        self.mlp = nn.Sequential(
            nn.Linear(cfg.d_model, 4 * cfg.d_model),
            nn.GELU(),
            nn.Linear(4 * cfg.d_model, cfg.d_model),
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        h = self.n1(x)
        attended, _ = self.attn(h, h, h, attn_mask=mask, need_weights=False)
        x = x + attended
        return x + self.mlp(self.n2(x))


class Reasoner(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.tok = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.pos = nn.Embedding(cfg.block_size, cfg.d_model)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.norm = nn.LayerNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        self.apply(self._init)

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.zeros_(m.bias)

    def embed(self, ids: torch.Tensor) -> torch.Tensor:
        """Token ids to vectors. Separated out so a caller can build an input
        sequence that is partly looked-up and partly computed."""
        return self.tok(ids)

    def forward(self, embeds: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Run the network over an already-embedded sequence.

        Returns `(hidden, logits)`. `hidden` is what a latent step feeds back;
        `logits` is what a token step samples from. A continuous thought is the
        first of those without the second, and the whole idea of this chapter is
        that the two are separable.
        """
        _, T, _ = embeds.shape
        x = embeds + self.pos(torch.arange(T, device=embeds.device))[None, :, :]
        mask = torch.full((T, T), float("-inf"), device=embeds.device).triu(1)
        for block in self.blocks:
            x = block(x, mask)
        hidden = self.norm(x)
        return hidden, self.head(hidden)


def masked_loss(logits: torch.Tensor, tokens: torch.Tensor, supervised: torch.Tensor):
    """Next-token cross-entropy at the positions the mask selects.

    Shifted by one as usual: position `i`'s logits predict token `i+1`, so a
    mask entry at `i+1` selects the prediction made at `i`. The arms differ in
    what they are given and are scored on exactly the same answer tokens, which
    is what makes their losses comparable at all.
    """
    predicted = logits[:, :-1]
    target = tokens[:, 1:]
    keep = supervised[:, 1:].bool()
    if keep.sum() == 0:
        return logits.sum() * 0.0
    return F.cross_entropy(predicted[keep], target[keep])


def parameter_count(cfg: Config) -> int:
    return sum(p.numel() for p in Reasoner(cfg).parameters())


if __name__ == "__main__":
    cfg = Config()
    print(f"{parameter_count(cfg):,} parameters at d_model={cfg.d_model}, {cfg.n_layer} layers")
    model = Reasoner(cfg)
    ids = torch.randint(0, cfg.vocab_size, (2, 32))
    hidden, logits = model(model.embed(ids))
    print(f"hidden {tuple(hidden.shape)}, logits {tuple(logits.shape)}")
    print(f"untrained loss should be near ln(vocab) = {math.log(cfg.vocab_size):.3f}")
