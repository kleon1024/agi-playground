---
status: verified
level: applied
verified: 2026-07-28
base: scratch
label: Why concurrency pays
---

# Why should sixteen requests cost less than sixteen times one?

**Question:** [the previous chapter](../) left the engine generating a flat
105-135 tokens per second for a single request, and explained why: a fixed
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
cd 01-language-model/05-serve/core
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

<details>
<summary>Answer</summary>

It tells you the speedup comes from the fused kernel, not the scheduling
policy. Continuous batching is "two separable things: a scheduling policy
and a fused kernel," and this engine implements only the first — it admits,
evicts, and frees blocks correctly, exactly as designed, yet aggregate
throughput barely moves across 1 to 16 concurrent requests. The scheduling
policy decides *which* requests get to run each step; it's the fused kernel
that turns "many requests in one batch" into "one weight read serving many
requests' arithmetic." Without that kernel, a per-request Python loop has
nothing to amortize, so the policy alone buys nothing measurable.

</details>

2. CUDA graphs bought 4.7x at one request and 4.5x at sixteen. Why does a
   roughly constant factor point at launch overhead rather than at arithmetic?

<details>
<summary>Answer</summary>

A cost that scales with the amount of arithmetic in a step would show a
*changing* multiplier as batch size changes the FLOPs per step — but the
chapter finds a roughly flat 4.7x at one request and 4.5x at sixteen, a
constant factor across a sweep where the arithmetic per step varies enormously.
"A constant factor across the whole sweep is the fingerprint of a cost that
does not depend on how much work a step contains" — which is exactly what a
per-step kernel-launch overhead is: removing it saves the same fraction of
time whether the step is doing a little arithmetic or a lot, unlike a
compute-bound cost that would scale with the work.

</details>

3. Batching gave 14.0x at sixteen requests, graphs gave 4.5x, and the total was
   89x. Why do these multiply rather than add?

<details>
<summary>Answer</summary>

Because they remove two different, independent per-unit costs: batching
removes a per-*request* cost (amortizing one weight read across many
requests' arithmetic), while graphs remove a per-*step* cost (kernel-launch
overhead, paid once per step regardless of batch composition). Since each
mechanism scales the same underlying time by its own independent factor —
one shrinking the request-dependent portion, the other shrinking the
launch-overhead portion — their effects compound multiplicatively rather than
summing: 14.0 × 4.5 ≈ 63, and the chapter's measured 89x reflects both
factors acting on the same baseline together, not two separate additive
savings.

</details>

4. Prefix caching was switched off for the comparison even though all sixteen
   prompts were identical. What would leaving it on have measured instead?

<details>
<summary>Answer</summary>

It would have measured the additional saving from recognizing that all
sixteen prompts share the same content and skipping recomputation of their
KV entirely — a saving the chapter deliberately excludes from this
comparison because it isn't part of what continuous batching or CUDA graphs
contribute; it's a separate mechanism (hashing blocks by content, from the
paging chapter). Leaving it on would conflate "what does batching plus
graphs buy" with "what does batching plus graphs plus free redundant-prompt
elimination buy," which the chapter treats as a distinct, excludable
question — exercise 3 asks you to turn it back on and decide for yourself
whether it belongs in a fair comparison against an engine with no such
cache.

</details>

5. Which of the numbers in this chapter would you expect to survive a move to a
   7B model, and which would collapse?

<details>
<summary>Answer</summary>

The mechanisms survive; the multipliers don't. The chapter states this
directly: "88M parameters is precisely the regime where fixed per-step costs
dominate... on a serving-sized model the GEMMs are large enough to hide the
launches and the same flag buys far less." So the scheduling-policy-vs-kernel
distinction, the direction of the batching win, and the existence of some
CUDA-graph benefit would all survive — but the specific 14.0x, 4.5x, and 89x
figures would shrink substantially at 7B, because larger GEMMs raise
arithmetic intensity per step and make the per-step launch overhead a much
smaller fraction of the total time than it is at 88M parameters.

</details>

## When should the scheduler say no?

Continuous batching decides *whose token runs next*. It does not decide whether
a request should have been admitted at all, and those are different questions
with different failure modes. A scheduler that admits everything eventually
evicts a request mid-generation, which is the worst outcome available: the work
already spent is thrown away and the user gets a truncated answer.

So admission is its own check, made before the request joins the batch, against
what the engine can actually see at that moment:

```text
prompt tokens
maximum generation tokens
KV blocks required
current active batch
queue delay
deadline or priority
```

Rejecting or queueing early is safer than admitting work that will force
mid-generation eviction, and a capacity policy has to state which requests may
be preempted and whether partial output counts as a result. Exercise 1 below
runs the engine into exactly this wall on purpose.

For mixed workloads the two phases can be split onto different workers — prefill
is compute-bound, decode is not, so they contend for different resources.
Disaggregation buys specialization and costs a transfer, a routing decision, and
a new failure boundary between the halves. It is worth reaching for only after
phase-specific measurements show a real imbalance, which is not something either
run on this page establishes.

## Which number tells you the service is healthy?

Everything measured on this page is aggregate throughput, and an average is
where a latency problem goes to hide. A good median with a bad long-context tail
violates the user's contract while the throughput chart improves. A serving
dashboard therefore reports distributions:

- time to first token, and inter-token latency, kept apart — prefill and decode
  are bound by different resources, so one blended number describes neither;
- end-to-end latency and output tokens per second;
- queue delay, active requests, and KV utilization;
- prefix-cache hit rate, if used;
- OOM, eviction, cancellation, and error rates.

Slice each by prompt length, output length, and priority. And join the trace
across admission, scheduling, model execution, and finish reason — without that
join, a latency spike has no owner, and the next question after "the p99 moved"
is unanswerable.

That instrumentation is not free and is not this chapter's code.
[A mean step time hides the step that just took three times as long](../observability/)
builds the p50/p95/histogram machinery every bullet above assumes somebody
already has.

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
