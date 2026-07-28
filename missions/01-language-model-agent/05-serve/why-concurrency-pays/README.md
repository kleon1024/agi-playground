---
status: verified
verified: 2026-07-28
base: scratch
label: Why concurrency pays
---

# Why should sixteen requests cost less than sixteen times one?

**Question:** [the previous chapter](../) left the engine generating a flat
120-145 tokens per second for a single request, and explained why: a fixed
per-step cost that the KV cache cannot touch. A fixed cost per step is exactly
the kind of cost that should be *shared*. If sixteen users send a prompt at the
same moment, sixteen decode steps read the same weights out of memory. Read them
once, and fifteen of those reads were never necessary.

So concurrency should be close to free. This chapter builds the scheduler that
makes it possible, measures it, finds it buys nothing, and then finds out why —
with a number attached.

## The scheduler: a change of decision point, not of batch size

Static batching waits for a fixed group of requests, runs the whole batch
until every sequence in it finishes, and only then admits new ones — so a
short request that finishes early sits idle, holding its slot, while the
batch waits on whatever request is longest. **Continuous batching**
(Orca's "iteration-level scheduling") instead makes the admit/evict decision
*every forward pass*: the moment a sequence finishes, its slot and its blocks
free up, and a waiting request can be admitted into the very next iteration.
`ContinuousBatchingEngine.step()` is exactly this: `_admit()` pulls in
whatever waiting requests current free blocks allow, one step runs for every
currently running request, and anything that just finished is evicted and
its blocks returned before the function returns. The batch's *composition* —
not any fixed size parameter — is what changes on every call.

Watch the same requests under static and iteration-level scheduling. No model
or batch-capacity parameter changes; only the admission decision moves from the
end of a batch to every forward pass.

<!-- interactive: ContinuousBatching -->

The engine here loops over admitted requests one at a time in Python; a
production engine fuses that loop into one batched kernel call over ragged
sequence lengths (the fused paged-attention kernels `prod/vllm_serve.py`
gets access to by switching engines). The scheduling logic — what gets
admitted, what gets evicted, when — is identical either way; only how the
resulting batch is executed on the GPU differs.

That difference is the whole game, and it is measurable. Run this engine at
1, 2, 4, 8 and 16 concurrent requests and aggregate throughput does not move:

| Concurrent requests | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| Aggregate tokens/second | 118.8 | 121.4 | 120.9 | 121.0 | 124.5 |
| Wall-clock | 1.08s | 2.11s | 4.24s | 8.46s | 16.45s |

Sixteen requests take 15.3x as long as one. **Concurrency buys nothing here** —
and that is not a defect in the scheduler, which is admitting, evicting, and
freeing exactly as designed. The throughput win of batching comes from one
kernel serving many sequences and amortising a fixed per-step cost across all
of them. A per-request Python loop has nothing to amortise.

So continuous batching is two separable things: a **scheduling policy** and a
**fused kernel**. This lesson implements and can teach the first. The second is
what makes the first pay.

## Proving it was the kernel

That last paragraph is an explanation, and an explanation that predicts
something is worth testing. The prediction: give the *same* checkpoint and the
*same* scheduling decisions to an engine that has the fused kernel, and
concurrency should start paying. `prod/vllm_serve.py` converts the checkpoint
and runs the identical sweep.

| Concurrent requests | 1 | 2 | 4 | 8 | 16 |
|---|---:|---:|---:|---:|---:|
| This lesson's engine, tok/s | 118.8 | 121.4 | 120.9 | 121.0 | 124.5 |
| vLLM without CUDA graphs, tok/s | 178.3 | 336.0 | 667.0 | 1310.5 | 2488.2 |
| vLLM as shipped, tok/s | 836.1 | 1632.6 | 3138.5 | 5589.7 | 11093.0 |

Read the middle row first, because it is the controlled comparison: same
policy, fused kernel, no other help. Sixteen requests now return **14.0x** the
throughput of one, against this lesson's 1.05x. The scheduler was never the
problem.

The bottom row adds CUDA graphs, and what they contribute is a **flat 4.7x at
one request and 4.5x at sixteen**. A constant factor across the whole sweep is
the fingerprint of a cost that does not depend on how much work a step
contains — which is what a kernel launch is. Batching removes a per-*request*
cost; graphs remove a per-*step* one. They multiply, to 89x at 16 requests.

Even at a single request, where there is nothing to batch, the fused kernel
alone is 1.5x. Full sweep, versions, and the three WSL2 environment failures it
took to get vLLM running are in
[`runs/2026-07-28-vllm-bench.md`](../runs/2026-07-28-vllm-bench.md).

One caution before you generalise: 88M parameters is precisely the regime where
fixed per-step costs dominate, which is why graphs are worth 4.7x here. On a
serving-sized model the GEMMs are large enough to hide the launches and the
same flag buys far less. The mechanism transfers; the multiplier does not.

## What this chapter does not establish

- **That the hand-written engine is badly written.** It implements the
  scheduling policy it claims to, and this run confirms the policy is the right
  one. The gap is a missing kernel, not a missing idea.
- **Anything about latency percentiles.** Aggregate throughput on a synthetic
  prompt again — no time-to-first-token, no behaviour under sustained arrival.
- **That vLLM is 89x faster in general.** 88M parameters is the regime where
  fixed per-step costs dominate. On a serving-sized model the GEMMs hide the
  launches and the same flags buy far less.

## Reproduce it

```bash
cd missions/01-language-model-agent/05-serve/core
python engine.py bench --checkpoint ../../03-sft/ckpt/ckpt.pt \
    --device cuda --prompt-len 64 --max-new-tokens 128 --num-requests 16

cd ../prod
python vllm_serve.py convert ../../03-sft/ckpt/ckpt.pt ./hf-checkpoint
python vllm_serve.py bench ./hf-checkpoint --requests 1 2 4 8 16 [--eager]
# or the real production entrypoint, which serves the same directory over HTTP:
vllm serve ./hf-checkpoint --port 8000
```

All three hand-written engines produce identical greedy token sequences on a
random-init model of this architecture, including under block budgets tight
enough to force admission and eviction mid-run, and the HF conversion was
verified to produce bit-identical logits (`0.0` max absolute difference)
against `model.py`'s own forward pass. The environment failures vLLM hit on
this host, and how each was resolved, are recorded with the sweep.

## Check your mental model

1. The scheduler admits and evicts at every forward pass, exactly as designed,
   and throughput stayed flat. What does that tell you about which of the two
   mechanisms in continuous batching produces the speedup?
2. CUDA graphs bought 4.7x at one request and 4.5x at sixteen. Why does a
   roughly constant factor point at launch overhead rather than at arithmetic?
3. Batching gave 14.0x at sixteen requests, graphs gave 4.5x, and the total was
   89x. Why do these multiply rather than add?
4. Prefix caching was switched off for the comparison even though all sixteen
   prompts were identical. What would leaving it on have measured instead?
5. Which of the numbers in this chapter would you expect to survive a move to a
   7B model, and which would collapse?

## Exercises

1. **Break the block budget on purpose.** Pass a `num_blocks` to
   `ContinuousBatchingEngine` too small to admit every submitted request at
   once, and print `engine.waiting` each step. Confirm requests queue and
   drain rather than crash, and that finished requests' blocks are reused by
   the ones behind them.
2. **Measure the paging tax.** `PagedKVCache.read` materializes a contiguous
   copy every attention call; time how much of `paged+continuous`'s total
   wall-clock that gather accounts for versus the matmuls themselves.
3. **Turn prefix caching back on** in `vllm_serve.py bench` and rerun. The
   prompts are identical, so the gain you see is the one this chapter
   deliberately excluded. Decide whether it belongs in a comparison against an
   engine that has no such cache.
4. **Sweep generation length under vLLM.** The hand-written engine's KV-cache
   speedup did not grow with sequence length because a fixed cost dominated.
   With that fixed cost largely removed, find where the quadratic term finally
   shows up.
5. **Convert and diff.** Run `vllm_serve.py convert`, load the result with
   `transformers.LlamaForCausalLM.from_pretrained` (no vLLM needed) and compare
   its logits against `model.py`'s forward pass on the same input ids — confirm
   the `0.0` diff on your own checkpoint.

## Next

[Stage 06 — agent](../../06-agent/): once the model can be queried fast, it can
be queried repeatedly inside a loop — the next stage wraps this serving layer
in tool use and multi-step reasoning.
