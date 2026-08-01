"""A causal Transformer over the video codec's own token vocabulary --
mission 08's actual feasibility test: `mission.yaml` frames the decision this
mission makes as "is a video tokenizer paired with a small autoregressive
model buildable and trainable inside this repository's real-run,
declared-compute-lane discipline at all," and this is the stage where that
gets answered on real hardware.

`Config` and `Transformer` are imported directly, unmodified, from mission
01's pretraining core -- the exact same classes mission 05's vision fusion
and mission 07's audio LM already reuse for a non-text vocabulary, just with
`vocab_size` set to this codec's 65-symbol alphabet (64 codes plus one `BOS`
marker, the same convention mission 07 stage 01 uses) instead of a BPE
tokenizer's or an audio codec's. No line of `model.py` is changed.

The video codec itself is retrained in-process, deterministically, with
stage 01's exact official recipe -- the same "retrain, do not checkpoint and
load" convention mission 07 stage 01 uses for its audio codec, since stage
01 never saved model weights, only its result JSON and example frames.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

import torch

CODEC_CORE = Path(__file__).resolve().parents[2] / "01-video-tokenizer" / "core"
sys.path.insert(0, str(CODEC_CORE))
from train_video_codec import DATA_DIR, load_clips
from train_video_codec import train as train_codec
from video_codec import N_FRAMES, VideoCodec

MODEL_CORE = (
    Path(__file__).resolve().parents[3] / "01-language-model-agent" / "02-pretrain" / "core"
)
sys.path.insert(0, str(MODEL_CORE))
from model import Config, Transformer

CODEBOOK_SIZE = 64  # matches 01-video-tokenizer's CodecConfig().codebook_size
BOS_TOKEN = CODEBOOK_SIZE
VOCAB_SIZE = CODEBOOK_SIZE + 1


@dataclass
class CodecRecipe:
    """Stage 01's exact official training recipe, reused here so the LM sees
    the identical codec every run -- not a hyperparameter choice made fresh
    at this stage."""

    steps: int = 800
    batch_size: int = 16
    lr: float = 1e-3
    seed: int = 0


def retrain_codec(recipe: CodecRecipe | None = None) -> tuple[VideoCodec, torch.Tensor, torch.Tensor]:
    recipe = recipe or CodecRecipe()
    _result, model, eval_clips = train_codec(recipe.steps, recipe.batch_size, recipe.lr, recipe.seed)
    train_clips = load_clips(DATA_DIR / "train.jsonl")
    model.eval()
    return model, train_clips, eval_clips


def build_lm_dataset(codec: VideoCodec, train_clips: torch.Tensor, eval_clips: torch.Tensor):
    """clip pixels -> codec tokens -> BOS-prefixed sequence, (N, N_FRAMES + 1)."""
    with torch.no_grad():
        train_tokens = codec.encode(train_clips)
        eval_tokens = codec.encode(eval_clips)
    bos_train = torch.full((train_tokens.shape[0], 1), BOS_TOKEN, dtype=torch.long)
    bos_eval = torch.full((eval_tokens.shape[0], 1), BOS_TOKEN, dtype=torch.long)
    return torch.cat([bos_train, train_tokens], dim=1), torch.cat([bos_eval, eval_tokens], dim=1)


def build_lm_config(block_size: int) -> Config:
    return Config(
        vocab_size=VOCAB_SIZE,
        n_layer=4,
        n_head=4,
        n_kv_head=2,
        d_model=128,
        d_ff=320,
        block_size=block_size,
    )


def train_lm(
    train_seq: torch.Tensor, cfg: Config, steps: int, lr: float, batch_size: int, seed: int
) -> tuple[Transformer, float]:
    torch.manual_seed(seed)
    t0 = time.perf_counter()
    model = Transformer(cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    n = train_seq.shape[0]
    inp, tgt = train_seq[:, :-1], train_seq[:, 1:]
    for _ in range(steps):
        idx = torch.randint(0, n, (batch_size,))
        _logits, loss = model(inp[idx], tgt[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()
    model.eval()
    return model, time.perf_counter() - t0


@torch.no_grad()
def generate_greedy(model: Transformer, prompt: torch.Tensor, n_new: int) -> torch.Tensor:
    """Plain full-recompute autoregressive generation -- sequences here are
    at most `N_FRAMES + 1 = 9` tokens long, so there is no latency question
    to answer at this stage (mission 07 stage 01 already answered that
    question for this repository's KV-cache mechanism); this stage is about
    whether the model can be trained and whether its predictions are useful,
    not about decode speed."""
    ids = prompt
    for _ in range(n_new):
        logits, _ = model(ids)
        next_id = logits[:, -1, :].argmax(dim=-1, keepdim=True)
        ids = torch.cat([ids, next_id], dim=1)
    return ids


assert N_FRAMES >= 1  # build_lm_dataset/build_lm_config/train_lm/generate_greedy all
# read N_FRAMES (or a block_size derived from the actual tensor shape) dynamically --
# nothing here hardcodes 8. Stage 02's own numbers assume N_FRAMES == 8; stage 04
# reuses every function in this file unmodified at N_FRAMES == 16 by monkeypatching
# that default before import, per this repo's "record the change" convention.
