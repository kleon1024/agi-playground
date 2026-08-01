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

<details>
<summary>Answer</summary>

Internal fragmentation (waste *inside* an allocation that belongs to
someone — unused slots reserved for a sequence that finished early) and
external fragmentation (waste *between* allocations that belongs to nobody,
because differently-sized reservations can't lend each other unused space).
A larger block size makes internal fragmentation worse: the worked example
shows a 20-token sequence wasting 12 slots at a 16-token block size but 44
slots at a 64-token block size — the sequence can only round up to a whole
number of blocks, and bigger blocks mean a bigger last partial block.

</details>

2. Why does a shared free list eliminate external fragmentation entirely,
   rather than merely reducing it?

<details>
<summary>Answer</summary>

Because every block is the same fixed size, any free block can satisfy any
request's next allocation — there's no such thing as "free space that's the
wrong shape to reuse," which is precisely what external fragmentation is.
Contiguous reservation at varying sizes leaves gaps between allocations that
only a request needing exactly that gap's size could use; fixed-size,
interchangeable blocks pulled from one shared free list make every unit of
free memory usable by every waiting request, so the condition that creates
external fragmentation (free memory shaped wrong for anyone waiting) can't
arise at all.

</details>

3. A sequence generates 20 tokens with a block size of 16. How many slots are
   wasted, and how many would be wasted under a 1,024-token reservation?

<details>
<summary>Answer</summary>

At a 16-token block size: the sequence needs 2 blocks (32 slots) to hold 20
tokens, wasting 12 slots — 37.5% of its own allocation, but only 12 slots in
absolute terms. Under a 1,024-token contiguous reservation (`max_len`
reserved up front, as `KVCacheEngine` does), the same 20-token sequence
leaves 1,004 slots reserved and unusable for as long as it's alive — roughly
84x more wasted slots than the paged version, for the identical sequence.

</details>

4. Copy-on-write and prefix caching both require the block table. What exactly
   does contiguous reservation make impossible about them?

<details>
<summary>Answer</summary>

Both require a unit of cache smaller than an entire request that multiple
sequences can point at simultaneously — copy-on-write needs multiple
sequences to share the same physical blocks for a common prefix until they
diverge, and prefix caching needs blocks to be hashed and looked up by
content so a repeated preamble's KV can be skipped entirely. Contiguous
reservation gives each sequence one monolithic buffer with no internal
subdivision, so there is no unit small enough for two sequences to
partially share — "there is no unit of cache small enough to share." The
block table is what introduces that unit; without it, sharing anything less
than a whole sequence's cache is structurally impossible, not just
unoptimized.

</details>

## Next

Return to [what these two mechanisms bought](../README.md#what-these-two-mechanisms-bought),
where the cache is measured and the result does not go the way the asymptotics
predict. Then
[why concurrency should be free](../why-concurrency-pays/) asks what happens
when sixteen requests arrive at once — the question paging exists to make
answerable.
