"""A small from-scratch classifier over character-level SMILES, reusing this
repository's own RoPE/RMSNorm/SwiGLU/GQA decoder blocks -- the same
`Config`/`Block`/`RMSNorm` missions 05, 07, and 08 already reuse unmodified
from [mission 01's pretraining core](../../../01-language-model/02-pretrain/core/model.py)
for a non-text vocabulary.

Those three missions import the *whole* `Transformer`, next-token head
included, because their task is autoregressive prediction over a learned
token vocabulary (image patches, audio codes, video codes) -- the same job
mission 01's language model does, just with a different alphabet. This
stage's task is different in kind: Tox21 is binary sequence classification,
one label per whole SMILES string, not next-token prediction. Importing
`Transformer` and its tied LM head would build a next-character predictor and
then bolt a classifier onto an object trained for the wrong objective. So
this file imports the reusable *architecture primitives* only --
`Config`, `Block` (RoPE attention + SwiGLU, GQA), `RMSNorm` -- unmodified, and
composes them into a purpose-built classifier head: embed, run the causal
blocks, take the hidden state at each sequence's last real (non-pad) token --
which, under causal attention, has already attended to every real token
before it and none of the padding after it -- and pass that through one
linear layer to a single logit.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

CORE_DIR = Path(__file__).resolve().parents[3] / "01-language-model" / "02-pretrain" / "core"
sys.path.insert(0, str(CORE_DIR))
from metrics import roc_auc
from model import Block, Config, RMSNorm, build_rope_cache
from smiles_tokenizer import build_vocab, load_split

MAX_LEN = 128


class SmilesClassifier(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.tok = nn.Embedding(cfg.vocab_size, cfg.d_model, padding_idx=0)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.norm = RMSNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, 1)

    def forward(self, ids: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        cos, sin = build_rope_cache(ids.shape[1], self.cfg.d_head, self.cfg.rope_theta, ids.device)
        x = self.tok(ids)
        for block in self.blocks:
            x = block(x, cos, sin)
        x = self.norm(x)
        last_idx = (lengths - 1).clamp(min=0)
        pooled = x[torch.arange(x.shape[0]), last_idx]
        return self.head(pooled).squeeze(-1)


def to_tensors(ids_list, len_list, labels):
    return (
        torch.tensor(ids_list, dtype=torch.long),
        torch.tensor(len_list, dtype=torch.long),
        torch.tensor(labels, dtype=torch.float32),
    )


def train_and_eval(train_csv: Path, test_csv: Path, seed: int, steps: int = 600, lr: float = 3e-4) -> dict:
    t0 = time.time()
    torch.manual_seed(seed)
    vocab = build_vocab(train_csv)

    train_ids, train_lens, train_y, train_trunc = load_split(train_csv, vocab, MAX_LEN)
    test_ids, test_lens, test_y, test_trunc = load_split(test_csv, vocab, MAX_LEN)
    train_ids_t, train_lens_t, train_y_t = to_tensors(train_ids, train_lens, train_y)
    test_ids_t, test_lens_t, _test_y_t = to_tensors(test_ids, test_lens, test_y)

    cfg = Config(vocab_size=vocab.size, n_layer=4, n_head=4, n_kv_head=2, d_model=128, d_ff=320, block_size=MAX_LEN)
    model = SmilesClassifier(cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)

    # Positive class is a minority (14.8% in this exact split, per stage 00) --
    # weight the loss by the train set's own imbalance so the model is not
    # rewarded for a constant-negative shortcut.
    pos_weight = torch.tensor([(train_y_t == 0).sum().item() / max((train_y_t == 1).sum().item(), 1)])

    n = train_ids_t.shape[0]
    model.train()
    for step in range(steps):
        idx = torch.randint(0, n, (64,))
        logits = model(train_ids_t[idx], train_lens_t[idx])
        loss = F.binary_cross_entropy_with_logits(logits, train_y_t[idx], pos_weight=pos_weight)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % 100 == 0:
            print(f"step {step}: loss={loss.item():.4f}", flush=True)

    model.eval()
    with torch.no_grad():
        test_logits = model(test_ids_t, test_lens_t)
    test_scores = torch.sigmoid(test_logits).numpy()
    auc = roc_auc(np.array(test_y), test_scores)

    return {
        "seed": seed,
        "n_train": len(train_y),
        "n_test": len(test_y),
        "n_train_truncated_over_maxlen": train_trunc,
        "n_test_truncated_over_maxlen": test_trunc,
        "vocab_size": vocab.size,
        "max_len": MAX_LEN,
        "n_params": sum(p.numel() for p in model.parameters()),
        "steps": steps,
        "test_roc_auc": float(auc),
        "wall_clock_seconds": time.time() - t0,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="../../00-dataset-and-property/data/train.csv")
    ap.add_argument("--test", default="../../00-dataset-and-property/data/test.csv")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--out", default="../runs")
    args = ap.parse_args()

    result = train_and_eval(Path(args.train), Path(args.test), args.seed, args.steps)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"model-seed{args.seed}.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
