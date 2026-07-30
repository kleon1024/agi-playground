# Run — INT8 weight-only quantization, hand-rolled and torchao

## Commands

```bash
cd platform/serving/02-quantization/core
python quantize.py footprint --checkpoint <ckpt.pt> --device cuda
python quantize.py verify    --checkpoint <ckpt.pt> --device cuda --tokens 64
python quantize.py bench     --checkpoint <ckpt.pt> --device cuda --max-new-tokens 128 --repeat 7
python quantize.py profile   --checkpoint <ckpt.pt> --device cuda --steps 50

cd ../prod
PYTHONPATH=../core python torchao_quantize.py bench --checkpoint <ckpt.pt> --device cuda \
    --max-new-tokens 128 --repeat 7
```

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 591.86 (same box as `platform/serving/01-graph-execution`'s recorded run) |
| Host | WSL2 Ubuntu, reached over Tailscale |
| torch | 2.13.0+cu130 |
| torchao | 0.17.0 (`Int8WeightOnlyConfig`, version 1 — the package warns this config is deprecated in favor of a version-2 API, noted for anyone reproducing this later) |
| Checkpoint | the 88,197,888-parameter stage 03 chat model, same file `01-graph-execution`'s run used |
| Shape | 64-token prompt, batch 1, cache sized 1024, greedy decoding |
| Total GPU time | well under 5 minutes across all commands |
| Cost | $0 (local lane) |

## Result 1: footprint

```
quantized: attn(q,k,v,o) + mlp(gate,up,down) x 12 layers (embedding/head left fp32, tied, 50,724,864 bytes)
quantized-layer bytes:  fp32 301,989,888  ->  int8 75,829,248  (3.98x)
whole-model bytes:      before 352,791,552  ->  after 126,554,112  (2.79x)
```

## Result 2: correctness — why greedy exact match is the wrong gate

```
first-position logits: KL(fp32||int8)=0.0027 nats, cosine similarity=0.99975, top-1 token agrees: False
fp32 vs int8 greedy tokens over a full generation: 1/64 match
  first divergence at token 0: fp32 109 vs int8 10
```

The two distributions are nearly identical (cosine 0.9997, KL 0.003 nats) and the single argmax
token still flips at position 0, because the top-2 logits there are close (measured separately:
fp32 top-2 were token 320 at p=0.0772 and token 62 at p=0.0644 — a 1.3-point gap that 8-bit
per-channel rounding error, mean 3.2% relative per weight, is large enough to cross). Every later
position then conditions on a different token than the reference, so the divergence compounds
across the whole generation. The distributional check at the first position is the real gate; it
passed (threshold cosine>0.99, KL<0.05) and `bench` proceeded.

## Result 3: bench — the hand-rolled path is slower, not faster

```
prompt 64, 128 new tokens, batch 1, cache sized 1024, 7 rounds each
configuration                    tok/s   ms/token   round spread  vs eager fp32
eager, fp32                      129.1      7.748  119.1-139.4            1.00x
eager, int8 weight-only           97.8     10.228   90.8-103.9            0.76x
CUDA graph, fp32                 373.8      2.675  372.6-374.1            2.90x
CUDA graph, int8                 322.8      3.098  321.4-323.0            2.50x
```

int8 is slower than fp32 in both regimes: 0.76x eager, and 0.86x under CUDA-graph replay
(322.8 / 373.8). A 2.79x smaller model did not buy any speed at batch 1.

## Result 4: profile — where the extra time goes

```
eager, fp32
  self CPU time total       446.0 ms   ( 8.920 ms/step)
  self CUDA time total       65.6 ms   ( 1.312 ms/step)
  host / device              6.80x

eager, int8 weight-only
  self CPU time total       572.8 ms   (11.455 ms/step)
  self CUDA time total       88.6 ms   ( 1.771 ms/step)
  host / device              6.47x
```

Device time went **up** 35% (1.312 -> 1.771 ms/step), not down. The dequantize-then-matmul path
adds a real elementwise multiply-and-cast kernel per Linear on top of the same matmul the fp32
path already pays for, and that additional compute costs more than the smaller HBM read saves.
Host time rose too (8.920 -> 11.455 ms/step), consistent with more distinct kernel launches per
step (the dequant op per Linear, in addition to the matmul).

## Result 5: torchao's real int8 kernel, for comparison

```
identity check: 26/64 tokens match eager fp32

prompt 64, 128 new tokens, batch 1, 7 rounds each
configuration                    tok/s   ms/token   round spread  vs eager fp32
eager, fp32                      130.5      7.665  117.6-139.1            1.00x
eager, torchao int8               88.6     11.293   79.5-90.9             0.68x
```

torchao's `Int8WeightOnlyConfig` dispatches to a real int8 GEMM (`torch.ops.aten._int_mm`) rather
than dequantizing to fp32 first, and it is *slower* than the hand-rolled version on this run
(0.68x vs 0.76x). No root cause was profiled for torchao specifically; the most likely
contributor, stated as a hypothesis and not measured here, is per-call tensor-subclass dispatch
overhead (`AffineQuantizedTensor`) that does not amortize at this model's small per-layer matmul
sizes and batch-1 decode. The identity check (26/64 greedy tokens match) shows the same
close-logit sensitivity as Result 2, not a different failure.

## Verdict

Both the hand-rolled and library INT8 weight-only paths shrink the model 2.79x-3.98x and neither
delivers a decode speedup at batch 1 on this hardware and model size — both are measured slower
than fp32. This confirms `01-graph-execution`'s prediction: the decode step here is launch-bound,
not bandwidth-bound, so a technique that reduces bytes moved without reducing kernel launches (and
adds one) has nothing to win against and something to lose.
