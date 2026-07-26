"""The smallest complete pretraining loop: text in, trained GPT out.

One readable file, nothing imported from a framework — the attention, the
block, the training loop, and the sampler are all written out. Roughly 34
seconds on a 24GB GPU, 1.65GB of VRAM.

See the lesson README for what the numbers mean, and `runs/` for a recorded
execution.
"""

import math
import time
import urllib.request
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

# ---------------------------------------------------------------- config
BLOCK = 256          # context length in tokens
BATCH = 64           # sequences per step
N_LAYER, N_HEAD, N_EMB = 6, 6, 384
LR = 1e-3
ITERS = 2000
EVAL_EVERY = 250
DEVICE = "cuda"
torch.manual_seed(1337)

# ---------------------------------------------------------------- data
# Tiny Shakespeare: ~1.1MB of text. Small enough that the whole corpus is a
# single tensor, which keeps the data path out of the way of the model code.
data_path = Path("shakespeare.txt")
if not data_path.exists():
    url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
    urllib.request.urlretrieve(url, data_path)
text = data_path.read_text()

# Character-level "tokenizer" — the simplest possible one. Lesson 01 of the
# pretraining track replaces exactly this with a real BPE.
chars = sorted(set(text))
VOCAB = len(chars)
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for c, i in stoi.items()}
encode = lambda s: [stoi[c] for c in s]
decode = lambda ids: "".join(itos[i] for i in ids)

data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]


def get_batch(split):
    d = train_data if split == "train" else val_data
    ix = torch.randint(len(d) - BLOCK - 1, (BATCH,))
    x = torch.stack([d[i : i + BLOCK] for i in ix])
    y = torch.stack([d[i + 1 : i + BLOCK + 1] for i in ix])
    return x.pin_memory().to(DEVICE, non_blocking=True), y.pin_memory().to(DEVICE, non_blocking=True)


# ---------------------------------------------------------------- model
class CausalSelfAttention(nn.Module):
    def __init__(self):
        super().__init__()
        self.qkv = nn.Linear(N_EMB, 3 * N_EMB, bias=False)
        self.proj = nn.Linear(N_EMB, N_EMB, bias=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(N_EMB, dim=2)
        # (B, n_head, T, head_dim) — heads become a batch dimension
        q = q.view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        k = k.view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        v = v.view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        # is_causal=True builds the mask internally; this dispatches to
        # FlashAttention, which is why memory stays flat in sequence length.
        out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.proj(out.transpose(1, 2).contiguous().view(B, T, C))


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(N_EMB), nn.LayerNorm(N_EMB)
        self.attn = CausalSelfAttention()
        self.mlp = nn.Sequential(
            nn.Linear(N_EMB, 4 * N_EMB, bias=False),
            nn.GELU(),
            nn.Linear(4 * N_EMB, N_EMB, bias=False),
        )

    def forward(self, x):
        # Pre-norm residual stream: the +x paths are the gradient highway.
        x = x + self.attn(self.ln1(x))
        return x + self.mlp(self.ln2(x))


class GPT(nn.Module):
    def __init__(self):
        super().__init__()
        self.tok = nn.Embedding(VOCAB, N_EMB)
        self.pos = nn.Embedding(BLOCK, N_EMB)
        self.blocks = nn.Sequential(*[Block() for _ in range(N_LAYER)])
        self.ln_f = nn.LayerNorm(N_EMB)
        self.head = nn.Linear(N_EMB, VOCAB, bias=False)
        self.tok.weight = self.head.weight  # weight tying

    def forward(self, idx, targets=None):
        _, T = idx.shape
        x = self.tok(idx) + self.pos(torch.arange(T, device=idx.device))
        x = self.ln_f(self.blocks(x))
        logits = self.head(x)
        if targets is None:
            return logits, None
        loss = F.cross_entropy(logits.view(-1, VOCAB), targets.reshape(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=0.8):
        for _ in range(max_new_tokens):
            logits, _ = self(idx[:, -BLOCK:])
            probs = F.softmax(logits[:, -1, :] / temperature, dim=-1)
            idx = torch.cat([idx, torch.multinomial(probs, 1)], dim=1)
        return idx


@torch.no_grad()
def estimate_loss(model):
    model.eval()
    out = {}
    for split in ("train", "val"):
        losses = torch.zeros(20)
        for k in range(20):
            with torch.autocast("cuda", dtype=torch.bfloat16):
                _, loss = model(*get_batch(split))
            losses[k] = loss.item()
        out[split] = losses.mean().item()
    model.train()
    return out


# ---------------------------------------------------------------- train
model = GPT().to(DEVICE)
params = sum(p.numel() for p in model.parameters())
print(f"vocab={VOCAB}  params={params/1e6:.2f}M  device={torch.cuda.get_device_name(0)}", flush=True)

opt = torch.optim.AdamW(model.parameters(), lr=LR, betas=(0.9, 0.95), weight_decay=0.1)
sched = torch.optim.lr_scheduler.LambdaLR(
    opt, lambda i: min((i + 1) / 100, 0.5 * (1 + math.cos(math.pi * i / ITERS)))
)

t0 = time.time()
tokens_seen = 0
for it in range(ITERS + 1):
    if it % EVAL_EVERY == 0:
        L = estimate_loss(model)
        el = time.time() - t0
        tps = tokens_seen / el if el > 0 else 0
        print(
            f"iter {it:>5}  train {L['train']:.4f}  val {L['val']:.4f}  "
            f"{el:6.1f}s  {tps/1e3:7.1f}k tok/s",
            flush=True,
        )
    x, y = get_batch("train")
    with torch.autocast("cuda", dtype=torch.bfloat16):
        _, loss = model(x, y)
    opt.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    sched.step()
    tokens_seen += BATCH * BLOCK

print(f"\npeak VRAM: {torch.cuda.max_memory_allocated()/1e9:.2f} GB", flush=True)
print("\n=== SAMPLE ===", flush=True)
ctx = torch.zeros((1, 1), dtype=torch.long, device=DEVICE)
print(decode(model.generate(ctx, 400)[0].tolist()), flush=True)
