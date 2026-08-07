---
status: verified
level: applied
base: scratch
label: What model size changes
verified: 2026-08-05
---

# What does model size change about SFT?

[The main SFT stage](../) ends with a specific result: an 88M model whose
fine-tune changed the *form* of its output — it answers, and stops — and
nothing about what it knows. That result carries an implicit claim: SFT
teaches shape, not content. This chapter asks whether that claim holds at
every model size, and it answers with the same recipe run at a smaller size,
against the recorded 88M run, and against dated results at scales this
repository cannot reach.

**Before this:** the SFT stage's own run and loss-masking mechanism.

## The question the main stage leaves open

The 88M evidence is one point on a size axis, and a single point cannot
distinguish "SFT teaches shape, not content" from "SFT teaches shape at 88M,
and does something else at other sizes." The superficial alignment hypothesis
— the claim that alignment mostly teaches the *style* of a reply while the
knowledge already lives in pretraining — was proposed at 65B parameters (Zhou
et al., LIMA, arXiv:2305.11206, 2023), a scale no single machine here can
reach. The small end of the axis is the part this repository *can* measure,
so that is where this chapter runs.

## The run: the same recipe at 5M, from two starting points

The full record is in [`runs/2026-08-05-sft-model-size.md`](runs/2026-08-05-sft-model-size.md).
The design holds everything fixed except the starting weights:

1. **A ~5M base** (4,941,504 params) pretrained on Tiny Shakespeare —
   ~330k tokens, 18 epochs, the same corpus `foundations/01` uses.
2. **SFT from that base** on the same 9,500 conversations the main stage used.
3. **SFT from random initialization** — same architecture, same data, same
   recipe, zero pretraining. This is the control that separates "the base
   brought something" from "the recipe alone does this."

The same `core/sft.py`, same block size, same budget (357 optimizer steps):

| step | pretrained-base SFT val | random-init SFT val |
|---:|---:|---:|
| 0 | 9.5188 | 9.7475 |
| 100 | 9.0501 | 9.2033 |
| 200 | 8.7736 | 8.9272 |
| 300 | 8.6496 | 8.8015 |

Two things fall out of this table, and both matter:

**The base prior helps even at 5M.** The pretrained arm starts lower (9.52 vs
9.75) and ends lower (8.65 vs 8.80). Random-init SFT does not catch up in
three epochs — the few hundred thousand tokens of Shakespeare-shaped English
in the base are still worth more than nothing when the model only has 5M
parameters to spend. The recipe alone is not the whole story; what the base
brought is part of the SFT result at every size.

**Neither arm lands the format.** Sample all three checkpoints on the same
prompt and you get word fragments, not the fluent-but-wrong prose the 88M
model produces:

```text
base:            Discovery kilomet forces-est mac mac acquire spir unfortunately ...
pretrained SFT:  dal off a I of the the was and the to not not in that know:,,al ...
random SFT:      look about all about, and this in the, come that5 than. The hees
```

At 5M there is not enough capacity to hold the chat template, the dialogue
distribution, and fluent English at once. The loss lands where it can — a
shallow imitation of the surface — and the residual is degenerate text. The
88M model had room for the format *or* the content, and spent the room on
format; a frontier model has room for both, and the literature below says
what SFT does with that room.

## The size axis, with this repo's measured points

| model | pretraining | SFT result (same recipe family) |
|---|---|---|
| 5M (this run) | ~330k tokens, Shakespeare | val 9.52 -> 8.65; word fragments; format does not land |
| 88M (recorded 2026-07-28) | 3.0B tokens, FineWeb-Edu | val 3.1829 -> 2.7828; fluent format, wrong content |

The two rows are **not head-to-head** — different tokenizer, corpus, and
device — and the chapter never presents them as such. They are two measured
points on the axis the next section extends with dated external results.

## What changes as the model grows

Three dated results span the part of the axis this repository cannot run:

- **At 65B, format is almost free.** LIMA fine-tuned a 65B model on 1,000
  curated demonstrations and matched far more heavily trained systems on
  style-following, which is the evidence behind the superficial alignment
  hypothesis (Zhou et al., arXiv:2305.11206, 2023). At this scale, SFT's job
  really is mostly surface — the knowledge is already in the base.
- **At scale, SFT can inject knowledge, but the method decides how well.**
  Token-scaled versus fact-scaled SFT data changes whether new facts actually
  land in an LLM (arXiv:2509.16596, Sep 2025). The claim "SFT cannot add
  knowledge" is not true at the top of the axis; it becomes a data-design
  question instead.
- **SFT's format-stabilizing role persists, and RL builds on it.** At
  frontier scale, SFT tends to memorize and stabilize output format while RL
  generalizes; the same study reports that removing SFT degrades RL's gains
  (Chu et al., "SFT Memorizes, RL Generalizes," ICML 2025, arXiv:2501.17161).

Read together with this chapter's runs, the axis has a consistent mechanism:
SFT moves the output distribution toward the fine-tuning data's surface, and
how much it can move depends on the room the model has — capacity to hold the
new surface without destroying the prior, and a prior rich enough to be
surfaced. At 5M both are near zero, so SFT produces fragments. At 88M capacity
exists and the prior is thin, so SFT lands the format and nothing else. At
65B-plus the prior is rich, so SFT mostly reshapes the surface — and with the
right data, can push new facts in.

## Evidence boundary

This chapter measured one new point (5M, two arms) and re-reads the recorded
88M point; the 5M and 88M numbers are not comparable head-to-head. It does
not demonstrate: any point between 5M and 88M; the effect of larger SFT
budgets at each size; or the mechanism claimed for frontier-scale models —
the three external results are attributed, dated, and run at scales no lane
in this repository reaches.

## Reproducing

```bash
cd 01-language-model/03-sft/what-model-size-changes
uv run --with tokenizers python runs/tokenize_shakespeare.py \
    /tmp/shakespeare/input.txt /tmp/shakespeare/tok.json \
    --out-dir /tmp/shakespeare/tokens --val-tokens 30000

uv run --group torch python ../../02-pretrain/core/train.py \
    --data /tmp/shakespeare/tokens --out /tmp/shakespeare/base --tokens 6e6 \
    --device mps --n-layer 4 --n-head 4 --n-kv-head 4 \
    --d-model 192 --d-ff 512 --block-size 1024

uv run --group torch python runs/init_random_ckpt.py \
    --out /tmp/shakespeare/rand/ckpt.pt \
    --n-layer 4 --n-head 4 --n-kv-head 4 --d-model 192 --d-ff 512

uv run --group torch --with datasets python ../../03-sft/core/sft.py train \
    --tokenizer /tmp/shakespeare/tok.json \
    --init-checkpoint /tmp/shakespeare/base/ckpt.pt \
    --out /tmp/shakespeare/sft-pretrained \
    --dataset HuggingFaceH4/no_robots --epochs 3 --device mps \
    --block-size 256 --n-layer 4 --n-head 4 --n-kv-head 4 \
    --d-model 192 --d-ff 512
```

The model-size flags (`--n-layer`, `--n-head`, `--n-kv-head`, `--d-model`,
`--d-ff`, `--block-size`) are the additions that let stage 02's trainer and
this stage's SFT run below the 88M default; omitting them reproduces the
recorded configurations exactly.

## Check your mental model

Answer each before opening it.

**1. Why does the 5M SFT produce word fragments rather than the fluent-but-wrong
prose the 88M model produces?**

<details>
<summary>Answer</summary>

Because at 5M there is not enough capacity to hold the chat template, the
dialogue distribution, and fluent English at once. The model fits what it
can — a shallow imitation of the fine-tuning surface — and the residual is
degenerate text. The 88M model had room for the format or the content, and
spent the room on format; a 5M model does not have room for either at usable
quality.

</details>

**2. Why does the pretrained 5M arm end lower than the random-init arm, even
though both are tiny?**

<details>
<summary>Answer</summary>

Because the base prior transfers: a few hundred thousand tokens of
Shakespeare-shaped English still gives the fine-tune a better starting point
than random weights when the model only has 5M parameters to spend. The
pretrained arm starts lower (9.52 vs 9.75) and ends lower (8.65 vs 8.80) —
the recipe alone is not the whole SFT result; what the base brought is part
of it at every size.

</details>

**3. Does this chapter's 5M run contradict the superficial alignment hypothesis?**

<details>
<summary>Answer</summary>

No. LIMA's hypothesis is about a 65B model whose pretraining already carries
the knowledge — at that scale SFT mostly reshapes style. This chapter's 5M
run measures the opposite end of the axis, where neither capacity nor prior
is sufficient, so SFT cannot even land the surface. The two results are
consistent with the same mechanism: SFT moves the output surface, and how
much it can move is bounded by what the model has room and prior for.

</details>

## Next

The main SFT stage's next step is [RL](../../04-rl/) — where the model has to
generate the answer and be scored on it. The scale question reappears there:
the same format-vs-content split, now under a reward signal.
