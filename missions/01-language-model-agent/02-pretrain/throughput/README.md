---
status: verified
level: applied
verified: 2026-07-28
base: scratch
label: Throughput
---

# Your run will take ten hours. Should it?

**Question:** a training script prints a tokens-per-second number and an ETA.
Both are real measurements of the run you launched. Neither tells you whether
the same model, the same batch, and the same card could have finished in a
third of the time — and at 88M parameters on one 24GB card, this chapter's
measurement says it could have finished in a **fourteenth**.

You need one thing from [pretraining](../)
before starting: that a training step is a forward pass, a backward pass, and
an optimizer update over a fixed batch of tokens. This chapter changes nothing
about any of them. Every configuration below computes the same gradient on the
same data and produces the same model. Only the wall-clock differs.

**Before this:** [what are you actually training](../README.md), for the model
and token budget this chapter measures the execution of.
You need a token budget you have committed to before it is worth asking how fast
it is being spent.

## The number that survives changing the model

Tokens per second is what you feel, and it is not comparable to anything. Halve
the model and it doubles, which measures nothing. **Model FLOPs Utilization**
is the fraction of the card's advertised throughput that a run converts into
gradient:

$$
\text{MFU} = \frac{\text{tokens/s} \times \text{FLOPs per token}}{\text{peak FLOPs/s}}
$$

with FLOPs per token approximated as `6 * params + 12 * n_layer * block_size *
d_model` — six per parameter for the forward-and-backward matmuls, plus the
attention term, which is quadratic in sequence length and so does not fold into
the parameter count.

**Worked, on the 88M model:** $6 \times 88{,}197{,}888 = 529{,}187{,}328$ for
the parameters, plus $12 \times 12 \times 1024 \times 768 = 113{,}246{,}208$
for attention — **642,433,536 FLOPs per token**, of which attention is 17.6%.
The slowest configuration below runs at 11,521 tokens/second, so it converts
$11{,}521 \times 642{,}433{,}536 = 7.40$ TFLOP/s out of the card's advertised
165, which is **4.5%**. The fastest runs at 169,230 tokens/second: 108.72
TFLOP/s, **65.9%**. Those are the first and last rows of the table below, and
you can now reproduce either of them from three numbers.

MFU has a ceiling of 100% and no run reaches it. What matters is that a run at
4% and a run at 66% are doing identical arithmetic, and one of them is spending
94% of the card on something else. Finding out what is the rest of this
chapter.

## Five flags, measured one at a time

Each row below adds one change to the row above it, on the stage-02
configuration, on one 4090. The full record is in
[`runs/2026-07-28-throughput-ladder.md`](runs/2026-07-28-throughput-ladder.md).

<!-- interactive: ThroughputLadder -->

Read the two large jumps first. **Flash attention** is worth 2.94x, and it is
not a faster matrix multiply — it is the same attention computed without ever
writing the `(sequence x sequence)` score matrix to memory. **`torch.compile`**
is worth another 1.72x by fusing chains of small elementwise operations into
single kernels. Both of these attack memory traffic, not arithmetic.

**Fused AdamW is worth 1.03x**, which at this size is nearly noise: the
optimizer touches 88M parameters once per step against 16.8M tokens of forward
and backward work. That ratio shifts toward the optimizer as batch size falls,
which is the sort of thing a table like this exists to make visible rather than
to memorise.

**Activation checkpointing costs 17% of throughput and returns 2.5x the
memory** — 8,686MB down to 3,410MB. It is the one row that is not an
improvement but a trade, and whether to take it depends entirely on whether the
freed memory buys a bigger batch.

## Proving the diagnosis rather than asserting it

"Memory-bound elementwise work" is an explanation, and explanations are cheap.
`prod/profile_step.py` runs the same step under `torch.profiler`, which
attributes every microsecond to a kernel. Compiled against uncompiled, five
steps each:

| | eager | compiled |
|---|---:|---:|
| Total self-CUDA | 818.6ms | 477.6ms |
| `aten::mm` (the matmuls) | 275.8ms — 33.7% | 277.5ms — 58.1% |

**The matmuls do not move.** 275.8ms before, 277.5ms after. Compilation deleted
341ms of everything else and did not touch a single multiply-accumulate the
model needed. Before compiling, two thirds of the card's time went to
operations producing no useful FLOPs; afterwards the same arithmetic accounts
for most of a much shorter step.

That is the general shape of the diagnosis. If the profile is dominated by
GEMMs, the run is compute-bound and fusion has nothing left to take. If it is
dominated by elementwise kernels and copies, fusion is the lever. If the *host*
is the bottleneck — the profiles here show `Command Buffer Full` at 37% of CPU
time in both cases — the fix is fewer, larger launches rather than faster ones.

## The trap this run walked into

The fp32 rung needed 27.7GB on a 24.5GB card. It did not crash. WSL2's driver
pages GPU allocations into host memory instead of raising out-of-memory, so the
run completed and reported a perfectly plausible number that was substantially
a measurement of PCIe traffic.

Rerun both dtypes at a micro-batch that fits, and bf16 is worth **1.28x**, not
the 2.82x the ladder credits it with. Both numbers are true statements about
different things: 1.28x is what bf16 arithmetic buys, and 2.82x is what
actually happened at that batch size on that card. Only one of them is an
attribution.

The general rule is worth more than the specific correction. **A configuration
that does not fit will not always tell you so.** Any throughput comparison
whose arms have different memory footprints needs its peak-memory column read
before its throughput column.

## What this chapter does not establish

- **That these multipliers transfer to a larger model.** At 88M the fixed
  per-step costs are large relative to the arithmetic, which is exactly why
  fusion is worth 1.72x. A 7B model spends proportionally more time in GEMMs
  and the same flag buys less. The ranking is likely stable; the magnitudes are
  not.
- **Anything about the resulting model.** Every number here is throughput. No
  rung was trained to convergence and no rung's loss was compared. bf16
  autocast changes the numerics, and this chapter has nothing to say about
  whether it changes the answer — that is
  [the ablation ladder's](../architecture-ablations/) question, with a
  stated budget definition and multiple seeds.
- **That 65.9% is good.** It is what this configuration reached. Whether the
  remaining 34% is reachable at all on this hardware is not something a ladder
  of flags can answer.

## Reproduce it

```bash
cd missions/01-language-model-agent/02-pretrain/throughput/core
python throughput.py ladder --micro-batch 16 --steps 30 --warmup 10

cd ../prod
python profile_step.py --no-compile --rows 8   # then --compile, and compare
```

Each rung runs in its own process, deliberately: `torch.compile` leaves
compiled artifacts and allocator state behind, and SDPA backend selection is
process-global, so measuring rung N+1 in a process that already ran rung N
measures the leftovers as much as the change.

## Check your mental model

Answer each before opening it.

**1. A run reports 200,000 tokens/second. What else do you need before you can
say whether that is good?**

<details>
<summary>Answer</summary>

The model's parameter count, layer count, block size, and model width (to
compute FLOPs per token), plus the card's advertised peak FLOPs/s — everything
MFU needs. Tokens/second alone is not comparable across models: halve the
model size and the same hardware roughly doubles tokens/second, which
measures the model shrinking, not the run getting more efficient. Only after
converting to MFU (fraction of the card's advertised throughput actually
turned into gradient) can "is this good" be answered — and even then, 65.9%
in this chapter's own fastest configuration is a measured ceiling for this
setup, not a claim that 100% is reachable.

</details>

**2. Flash attention and `torch.compile` together are worth 5x here, and neither
makes a matrix multiply faster. What are they making faster?**

<details>
<summary>Answer</summary>

Memory traffic, not arithmetic. Flash attention's 2.94x comes from never
materializing the `(sequence x sequence)` score matrix in memory — same
attention computation, far less data moved. `torch.compile`'s 1.72x comes from
fusing chains of small elementwise operations into single kernels, cutting the
number of separate memory round-trips between them. The profiler evidence in
this same chapter confirms it directly: `aten::mm` (the actual matmuls) takes
275.8ms before compilation and 277.5ms after — statistically the same. The
341ms that disappeared was overhead around the matmuls, not the matmuls
themselves.

</details>

**3. The profiler shows `aten::mm` unchanged at 275.8ms and 277.5ms across the
compile boundary. Why is that the strongest possible evidence for the
memory-bound diagnosis?**

<details>
<summary>Answer</summary>

Because it rules out the alternative explanation directly rather than merely
being consistent with the memory-bound story. If compilation had somehow made
the matrix multiplies themselves faster, `aten::mm`'s time would have dropped
too — but it didn't move at all while total self-CUDA time fell from 818.6ms
to 477.6ms. The only place that missing 341ms could have come from is
non-GEMM work: elementwise kernels, copies, and launch overhead. A profiler
that attributes every microsecond to a specific kernel turns "explanations are
cheap" into a falsifiable claim, and this one didn't get falsified.

</details>

**4. Activation checkpointing lost 17% throughput. Under what circumstance is
turning it on the higher-throughput decision anyway?**

<details>
<summary>Answer</summary>

When the 2.5x memory it frees (8,686MB down to 3,410MB in this chapter's
measurement) lets you run a larger batch size than you could otherwise fit.
A larger effective batch can raise overall throughput and training stability
by more than the 17% per-step cost of recomputing activations during the
backward pass — but only if the freed memory is actually spent on a bigger
batch, not left unused. This is explicitly a trade, not a strict improvement:
whether it's worth it depends on what the freed memory buys, which this
chapter states rather than assumes.

</details>

**5. The fp32 rung reported a number without failing on a card too small to hold
it. What column would have caught that, and what would have caught it on a
platform that raises out-of-memory instead?**

<details>
<summary>Answer</summary>

The peak-memory column would have caught it here: 27.7GB requested against a
24.5GB card is a memory footprint that doesn't fit, visible the moment memory
is checked alongside throughput. WSL2's driver silently paged the overflow
into host memory over PCIe instead of raising an error, so the run "succeeded"
and printed a plausible-looking throughput number that was actually measuring
PCIe transfer speed, not GPU compute. On a platform that raises
out-of-memory instead of silently paging, the crash itself would have caught
it — the run simply wouldn't have completed. Either way, the lesson is the
same: any throughput comparison across configurations with different memory
footprints needs the peak-memory column read before the throughput column.

</details>

## Next

Take the five flags back to
[stage 02 of the language-model system](../),
which is where they turn a ten-hour run into a five-hour one against a real
corpus. That is what this chapter exists to hand back.

If instead you are still choosing the model rather than running it,
[architecture ablations](../architecture-ablations/) asks the question this
chapter deliberately refuses: not how fast a configuration runs, but whether it
produces a better model — and what "equal budget" has to mean before that
question has an answer.
