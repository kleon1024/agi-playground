---
status: verified
level: foundation
verified: 2026-07-28
base: scratch
label: Paging the cache
---

# Why does reserving the KV cache waste most of it?

A request arrives. You do not know whether it will generate 20 tokens or 1,000,
but you have to give it memory now. Reserve for the worst case and you waste
almost all of it; reserve for the typical case and you fail the requests that
run long.

Production serving systems reported **60–80% of KV cache memory wasted** this
way before PagedAttention. This chapter is how that number comes down to a few
percent, using a fix operating systems found decades ago for exactly the same
problem.

**Before this:** [what the model is doing between tokens](../README.md),
through the KV cache section. You need to know that the cache is 12 KiB per
token here, and that the cache — not the weights — is what decides how many
requests a card can hold.

## Two kinds of waste, and they are not the same

`KVCacheEngine` reserves one buffer of `max_len` tokens per sequence, up front,
before knowing how many tokens the sequence will actually generate. That wastes
memory two distinct ways:

- **Internal fragmentation.** A sequence that finishes after 20 tokens but was
  sized for 1,024 leaves 1,004 slots reserved and unusable for as long as it is
  alive. The waste is *inside* an allocation that belongs to someone.
- **External fragmentation.** Two sequences reserved at different sizes cannot
  lend each other unused space, even when free memory sits between them. The
  waste is *between* allocations and belongs to nobody.

The distinction matters because the two respond to different fixes, and one
of them gets worse as you tune against the other.

## The fix is a page table

Stop reserving contiguous ranges. Allocate **fixed-size blocks** instead —
`BlockAllocator`, 16 tokens each here, vLLM's original default — and track them
per sequence with a **block table** mapping logical position to physical block.
That is a page table, precisely, doing the job it has always done.

Blocks come from a shared free list on demand as generation proceeds, and go
back to that free list the instant a sequence finishes
(`ContinuousBatchingEngine.step`, right where a sequence is marked `done`).
Waste drops from most of the reservation to at most one partially-used block
per sequence.

**Worked, at 16 tokens per block:** a sequence that generates 20 tokens holds
two blocks, 32 slots, wasting 12 — 37.5% of its own allocation, but 12 slots
rather than 1,004. Raise the block size to 64 and the same sequence wastes 44
slots; lower it to 4 and it wastes none, at the cost of a block table four
times longer and four times as many lookups per attention step. Block size
trades internal fragmentation against indirection overhead, and external
fragmentation is gone either way because every block is interchangeable.

Add several requests below and compare contiguous reservation with block
allocation. The observation that matters is not only higher utilization: freed
blocks become reusable by an unrelated request immediately.

<!-- interactive: PagedAttention -->

## What the same indirection buys next

Two capabilities fall out of the block table that this lesson does not
implement, and both are standard in production engines:

- **Copy-on-write.** Sequences sharing a prefix point at the same physical
  blocks until they diverge. Sampling eight completions from one prompt then
  costs one copy of the prompt's cache, not eight.
- **Prefix caching.** Blocks are hashed by content, so a repeated system prompt
  skips recomputing its KV entirely. The saving is proportional to how much of
  your traffic shares a preamble, which for most deployments is most of it.

Neither is possible under contiguous reservation, because there is no unit of
cache small enough to share. The block is what makes sharing expressible.

## What this chapter does not establish

`PagedKVCache.read` gathers a sequence's blocks into a contiguous tensor for
readability. A production kernel fuses that gather into the attention
computation itself, so the implementation here trades real performance for a
much shorter body of code — and no throughput number on this page would
transfer to a fused engine.

More importantly, **nothing here was benchmarked**. The parent chapter's
measurements compare naive decoding against the KV cache; paging was not in
that sweep. What this chapter establishes is a memory-utilization argument and
the mechanism that implements it, not a speedup.

## Check your mental model

1. Name the two kinds of fragmentation, and say which one a larger block size
   makes worse.
2. Why does a shared free list eliminate external fragmentation entirely,
   rather than merely reducing it?
3. A sequence generates 20 tokens with a block size of 16. How many slots are
   wasted, and how many would be wasted under a 1,024-token reservation?
4. Copy-on-write and prefix caching both require the block table. What exactly
   does contiguous reservation make impossible about them?

## Next

Return to [what these two mechanisms bought](../README.md#what-these-two-mechanisms-bought),
where the cache is measured and the result does not go the way the asymptotics
predict. Then
[why concurrency should be free](../why-concurrency-pays/) asks what happens
when sixteen requests arrive at once — the question paging exists to make
answerable.
