# Three authors, one set of prompts: what held-out loss actually measures

Nine supervised fine-tunes of the same 88M base checkpoint. The prompts are
identical across every arm and appear in the same order; the only thing that
changes is who wrote the assistant turn. Then every checkpoint is scored
against every author's held-out answers to the same test prompts.

The intended question was whether teacher-generated data beats human data. The
answer the run gives is that the usual way of asking it cannot tell.

## Commands

```bash
# three training corpora over one set of prompts
python generate_traces.py --human --limit 3000 --out data/human.jsonl
python generate_traces.py --limit 3000 --base-url http://localhost:8000/v1 \
    --model Qwen/Qwen2.5-0.5B-Instruct --out data/teacher-small.jsonl
python generate_traces.py --limit 3000 --base-url http://localhost:8000/v1 \
    --model Qwen/Qwen2-7B-Instruct    --out data/teacher-large.jsonl

# the same three authors over the held-out test prompts
python generate_traces.py --human --split test --out data/eval-human.jsonl
#   ... and once per teacher, same prompts

# nine fine-tunes, step-matched
python sft.py train --tokenizer tokenizer_hf.json --init-checkpoint base.pt \
    --dataset data/$ARM.jsonl --max-steps 102 \
    --eval-dataset data/eval-human.jsonl --seed $SEED --out ckpt/$ARM-s$SEED

# twenty-seven scorings, plus the base checkpoint on each reference set
python sft.py score --tokenizer tokenizer_hf.json \
    --checkpoint ckpt/$ARM-s$SEED/ckpt.pt --dataset data/eval-$REF.jsonl --limit 446
```

## Environment

| | |
|---|---|
| Machine | local lane, one 24GB card, WSL2 kernel 6.18.33.2 |
| Training | torch 2.13.0+cu130, bf16 autocast, ~106k tok/s, MFU 41% |
| Teachers | vLLM 0.26.0, greedy (`temperature: 0.0`), served one at a time |
| Student | the 88M stage-02 checkpoint, 3.00B pretraining tokens |
| Prompts | `HuggingFaceH4/no_robots`, single-turn rows only |
| Train rows | 3,000 prompts; 3,000 / 2,999 / 2,999 answers kept |
| Eval rows | 446 test prompts, answered by all three authors |
| Seeds | 1337, 20260729, 7 |
| Cost | \$0 — local hardware, no API calls |

Each fine-tune took about 40 seconds. Trace generation took 45.8 s for the
0.5B teacher and 416.8 s for the 7B, at concurrency 64 and 48.

## Step-matching was not optional

Three epochs is not an equal budget when the arms differ in answer length:

| Arm | Packed blocks | Steps at 3 epochs |
|---|---|---|
| human | 1,100 | 102 |
| teacher-small | 1,443 | 135 |
| teacher-large | 1,706 | 159 |

Model teachers write longer answers, so the same 3,000 prompts pack into more
blocks and "3 epochs" quietly hands those arms 32% and 56% more gradient steps.
An unmatched first pass ran exactly this way and had the human arm winning on
held-out human loss — a result confounded by the arm that lost having had the
larger budget. Every run below is capped at 102 steps by `--max-steps`.

## The matrix

Mean loss over 3 seeds, with half the seed range as the spread. Lower is
better. Columns are **not** comparable to each other; only rows within a column
are.

| Trained on | ref: human | ref: teacher-small | ref: teacher-large |
|---|---|---|---|
| human | **2.9074** ±0.0005 | 2.0181 ±0.0013 | 2.3819 ±0.0001 |
| teacher-small | 3.0263 ±0.0013 | **1.8320** ±0.0003 | 2.2925 ±0.0006 |
| teacher-large | 2.9918 ±0.0029 | 1.8878 ±0.0014 | **2.2763** ±0.0016 |
| base, no SFT | 3.1916 | 2.3649 | 2.6895 |

Raw records: [`2026-07-29-scores.jsonl`](2026-07-29-scores.jsonl).

**The winner is the diagonal, in all three columns.** Every arm is best on its
own author's held-out answers, and every margin clears the seed spread by a
wide factor — the narrowest is teacher-large's 0.0162 lead against a spread of
0.0032, and the widest is human's 0.0844 against 0.0010.

## What that means for the experiment people usually run

The standard framing — train on teacher answers, train on human answers, compare
held-out loss — picks its winner in advance. The held-out set has an author. The
arm trained on that author wins. Run it with a human reference set and human
data "wins"; run the identical experiment with a teacher reference set and the
teacher data "wins" by the same logic and the same code.

Held-out loss here is measuring **author-matching**, not answer quality. It
cannot be used to rank the corpora, and a single-column version of this table
would have supported whichever conclusion its author had already chosen.

## What the table does support

**SFT works regardless of author.** Every arm beats the base checkpoint on every
reference set, by 0.28 to 0.53 nats. Learning the chat format and learning to
stop are not properties of who wrote the answers.

**Teacher size shows up off the diagonal.** On human reference text the 7B
teacher's data transfers better than the 0.5B teacher's — 2.9918 against 3.0263,
a gap of 0.0345 against spreads of 0.0029 and 0.0013. Neither reaches the human
arm's 2.9074. This is the only quality signal in the run that is not confounded
with the author of the reference set.

**Model text is markedly more predictable than human text.** The untrained base
checkpoint scores 3.1916 on human answers and 2.3649 on the 0.5B teacher's
answers to the same prompts. That gap owes nothing to fine-tuning; it is a
property of the text. It is also why the columns cannot be compared.

**The two model-authored arms resemble each other more than either resembles
human writing.** On teacher-large's reference set the teacher-small arm reaches
2.2925 against the winner's 2.2763, while the human arm sits at 2.3819 — the
human arm is roughly six times further from the winner than the other model arm
is.

## What this does not establish

**Nothing about answer quality.** No arm was judged by anything except next-token
loss against a reference. Ranking these corpora needs an author-neutral metric —
win rate under a judge, or a downstream task — and this run has neither.

**One student, one scale.** An 88M model with a 16,512-entry vocabulary, three
epochs' worth of steps, 3,000 prompts. Nothing here extrapolates to a 7B student
or to 100k rows.

**One prompt distribution.** All three arms answer `no_robots` prompts. A corpus
whose prompts also came from a model would confound author with prompt
distribution, which is the confound `generate_traces.py` exists to prevent and
which this run therefore says nothing about.

**Sequence-level only.** No logits were used anywhere. That is the path
available when the teacher is served over an API, and it is the path this
chapter documents; it is not a claim that logit-level distillation would land in
the same place.

**Greedy teachers.** Both teachers ran at `temperature: 0.0`. A sampled corpus
would be more diverse and might transfer differently; that comparison was not
run.
