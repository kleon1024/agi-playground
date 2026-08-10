"""Train a causal Transformer language model over the audio codec's own
discrete token vocabulary -- the audio-token analogue of mission 01's
text-token pretraining, using the *identical* `Config`/`Transformer` classes
[`engine.py`](../../../01-language-model/serve/core/engine.py)
itself imports, not a reimplementation. Nothing in either class assumes
text: a token is just an integer id into an embedding table either way.
This is the model stage 01 hands to the KV-cache decode loop -- the object
being served changes (an audio-token LM instead of a text LM), the serving
mechanism does not.

Retrains stage 00's exact codec recipe in-process (same architecture, same
hyperparameters, same seed) rather than loading a saved checkpoint, since
stage 00 did not persist one -- 126s of CPU time to reproduce it is cheap
next to adding checkpoint I/O for a single consumer. See
[`00-audio-codec/runs/2026-07-31-codec-training.md`](../../00-audio-codec/runs/2026-07-31-codec-training.md)
for the original training curve this reproduces.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch
from torch.nn import functional as F

CODEC_DIR = Path(__file__).resolve().parents[2] / "00-audio-codec" / "core"
sys.path.insert(0, str(CODEC_DIR))
from audio_data import build_dataset
from codec import Codec, CodecConfig

ENGINE_DIR = Path(__file__).resolve().parents[4] / "01-language-model" / "05-serve" / "core"
sys.path.insert(0, str(ENGINE_DIR))
from engine import Config, Transformer

BOS_TOKEN = CodecConfig().codebook_size  # one id past the codec's own 64 codes
VOCAB_SIZE = CodecConfig().codebook_size + 1


def train_codec(seed: int, steps: int = 600, lr: float = 1e-3, n_train: int = 512, n_eval: int = 100):
    torch.manual_seed(seed)
    train_clips, eval_clips = build_dataset(n_train, n_eval, seed)
    train_wf = torch.stack([c.waveform for c in train_clips])
    eval_wf = torch.stack([c.waveform for c in eval_clips])

    model = Codec(CodecConfig())
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    for step in range(steps):
        idx = torch.randint(0, train_wf.shape[0], (32,))
        batch = train_wf[idx]
        recon, _tokens, vq_loss = model(batch)
        loss = F.mse_loss(recon, batch) + 0.25 * vq_loss
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    model.eval()
    return model, train_clips, eval_clips, train_wf, eval_wf


def build_lm_dataset(codec: Codec, train_wf: torch.Tensor, eval_wf: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Each clip's real codec tokens, prefixed with `BOS_TOKEN`: a length-65
    sequence `[BOS, t0, ..., t63]` whose input/target shift
    (`seq[:-1]`/`seq[1:]`) is the standard next-token teacher-forcing setup.
    """
    with torch.no_grad():
        train_tokens = codec.encode(train_wf)
        eval_tokens = codec.encode(eval_wf)
    bos_col = lambda n: torch.full((n, 1), BOS_TOKEN, dtype=torch.long)
    train_seq = torch.cat([bos_col(train_tokens.shape[0]), train_tokens], dim=1)
    eval_seq = torch.cat([bos_col(eval_tokens.shape[0]), eval_tokens], dim=1)
    return train_seq, eval_seq


def build_lm_config(block_size: int) -> Config:
    return Config(vocab_size=VOCAB_SIZE, n_layer=4, n_head=4, n_kv_head=2, d_model=128, d_ff=320, block_size=block_size)


def train_lm(train_seq: torch.Tensor, cfg: Config, steps: int, lr: float, batch_size: int, seed: int) -> Transformer:
    torch.manual_seed(seed + 1)  # distinct from the codec's own seed
    model = Transformer(cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    n = train_seq.shape[0]
    for step in range(steps):
        idx = torch.randint(0, n, (batch_size,))
        batch = train_seq[idx]
        inp, tgt = batch[:, :-1], batch[:, 1:]
        _logits, loss = model(inp, tgt)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % 50 == 0:
            print(f"lm step {step}: loss={loss.item():.4f}", flush=True)
    model.eval()
    return model
