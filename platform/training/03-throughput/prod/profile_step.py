"""Attribute a training step's time to individual CUDA kernels, with the
profiler that ships with PyTorch.

`../core/throughput.py` answers "did this flag help", one number per
configuration. It cannot answer "why", and when a rung disappoints, why is the
only question left. `torch.profiler` answers it by recording every kernel
launch and every host-side operator, so a step becomes a ranked table of where
the microseconds went rather than a single duration.

The two views worth reading, and they disagree usefully:

- **`self_cuda_time_total`** — time spent inside each kernel, excluding its
  children. This is the one that names the bottleneck. A step dominated by
  `elementwise_kernel` and `vectorized_layer_norm` is memory bound and is what
  `torch.compile` fixes by fusion; a step dominated by GEMMs is compute bound
  and no amount of fusion will help it.
- **`self_cpu_time_total`** — time the *host* spent, mostly issuing launches.
  When this exceeds the CUDA total, the GPU is idle waiting for Python, which
  is launch-bound rather than memory-bound, and the fix is CUDA graphs or
  larger batches rather than fusion.

Distinguishing those two is the entire diagnostic value of this file, and it
is why `../core/throughput.py`'s tokens/second column is not enough on its own.

Requires: `pip install torch` and a CUDA GPU. Chrome traces open at
`chrome://tracing` or https://ui.perfetto.dev.

Usage:
    python profile_step.py --compile --trace /tmp/step.json
    python profile_step.py --no-compile --sort self_cpu_time_total
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch.profiler import ProfilerActivity, profile

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "missions/01-language-model-agent/02-pretrain/core"))
from model import Config, Transformer


def profile_steps(compile_model: bool, micro_batch: int, sort_by: str, rows: int, trace: Path | None) -> None:
    torch.manual_seed(0)
    cfg = Config()
    model = Transformer(cfg).to("cuda")
    raw = model
    if compile_model:
        model = torch.compile(model)
    opt = torch.optim.AdamW(raw.parameters(), lr=6e-4, fused=True)

    tokens = torch.randint(0, cfg.vocab_size, (micro_batch, cfg.block_size + 1), device="cuda")
    x, y = tokens[:, :-1].contiguous(), tokens[:, 1:].contiguous()

    def step() -> None:
        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = model(x, y)
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)

    # Warm up outside the profiler. Profiling the compile itself produces a
    # spectacular and completely unrepresentative table.
    for _ in range(8):
        step()
    torch.cuda.synchronize()

    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], record_shapes=False) as prof:
        for _ in range(5):
            step()
        torch.cuda.synchronize()

    print(prof.key_averages().table(sort_by=sort_by, row_limit=rows))
    if trace:
        prof.export_chrome_trace(str(trace))
        print(f"\nwrote chrome trace to {trace}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--compile", dest="compile_model", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--micro-batch", type=int, default=16)
    ap.add_argument("--sort", dest="sort_by", default="self_cuda_time_total",
                    choices=["self_cuda_time_total", "self_cpu_time_total", "cuda_time_total"])
    ap.add_argument("--rows", type=int, default=20)
    ap.add_argument("--trace", type=Path, default=None, help="write a chrome://tracing timeline")
    args = ap.parse_args()
    profile_steps(args.compile_model, args.micro_batch, args.sort_by, args.rows, args.trace)


if __name__ == "__main__":
    main()
