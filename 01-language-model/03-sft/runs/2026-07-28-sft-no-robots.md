# SFT on no_robots — 88M base, 3 epochs

## Command

```bash
cd 01-language-model/03-sft/core
python sft.py train \
  --tokenizer   ../../01-tokenizer/tokenizer_hf.json \
  --init-checkpoint ../../02-pretrain/ckpt/ckpt.pt \
  --out ckpt \
  --samples-after 6
```

Everything else is the file's defaults: `HuggingFaceH4/no_robots`, splits
`train` and `test`, 3 epochs, micro-batch 8, gradient accumulation 4, peak LR
2e-5, 30 warmup steps, cosine decay, no weight decay, gradient clipping at 1.0.

## Base model

`01-language-model/02-pretrain`, the 88,197,888-parameter decoder
trained here on 3.00B tokens. The checkpoint records its own pretraining token
count and `sft.py` prints it on load, which is the check that the weights being
fine-tuned are the ones the previous stage produced.

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 591.86 |
| Host | WSL2 on Windows, reached over Tailscale |
| Repository | commit `f671be9` |
| torch | 2.13.0+cu130 |
| datasets | 5.0.0 |
| tokenizers | 0.23.1 |
| Cost | \$0 (local lane) |

## Data

| | |
|---|---|
| Train conversations | 9,500 |
| Eval conversations | 200 (sampled from the 500-row `test` split) |
| Packed training blocks | 3,305 of 1,025 tokens |
| Real tokens after packing | 80.4% |
| Dropped for exceeding one block | 217 train (2.3%), 4 eval |

Two numbers here are worth keeping. **19.6% of the packed tokens are padding**,
because conversations do not divide evenly into 1,024-token blocks and the last
block of each pack is finished with padding. And **217 conversations were
discarded outright** for being longer than a single block — this base model has
a 1,024-token context, so the longest 2.3% of a hand-written instruction set
cannot be trained on at all. Both are consequences of the context length chosen
in stage 02, arriving one stage later.

## Result

| | |
|---|---|
| Steps | 309 (3 epochs x 103) |
| Tokens seen | 9,830,400 |
| Wall-clock | 92.5s (0.03h) |
| Throughput | 106,268 tokens/second |
| MFU | 41.4% |
| Val loss at step 0 | 3.1829 |
| Best val loss | **2.7828** at step 250 |
| Final val loss | 2.8466 at step 300 |

```
step      0  val 3.1829  lr 6.67e-07      0.0M tok    0.0k tok/s  MFU  0.0%
step     50  val 2.9574  lr 1.98e-05      1.6M tok  102.9k tok/s  MFU 40.1%
step    100  val 2.8940  lr 1.73e-05      3.3M tok  105.6k tok/s  MFU 41.1%
step    150  val 2.8582  lr 1.30e-05      4.9M tok  106.5k tok/s  MFU 41.5%
step    200  val 2.8524  lr 7.97e-06      6.6M tok  107.0k tok/s  MFU 41.6%
step    250  val 2.7828  lr 3.91e-06      8.2M tok  105.9k tok/s  MFU 41.2%
step    300  val 2.8466  lr 2.05e-06      9.8M tok  106.3k tok/s  MFU 41.4%
```

Full history in [`history.json`](history.json).

### The step-0 number is not a regression

Pretraining ended at a validation loss of 3.0984 on web text. This run starts at
3.1829 on chat text before a single optimizer step. Nothing got worse: it is a
different held-out distribution, measured only on assistant tokens, through a
chat template the model has never seen. Comparing the two numbers directly is a
category error, and the only honest baseline for an SFT curve is its own step 0.

### Throughput is well below the pretraining run

41.4% MFU here against 65.1% in stage 02, on the same card and the same model.
`sft.py` does not enable `torch.compile`; stage 02 measured a 1.76x speedup from
it. At 92 seconds of total compute the flag is not worth the compilation delay,
but the gap is the same one stage 02 measured, not a new mystery.

## Generations

Sampled from the final checkpoint with the chat template applied. Prompts are
the first six from the `test` split.

> **What are some good desserts that use chocolate?**
> Candy, chocolate, and chocolate, are the two popular desserts for children.

> **What are 5 things I can do when it's raining in London? I am visiting for the fi...**
> Celebrate the day with these 5 things you can do when it's raining in London.
> Have fun with your friends, be active, and find out more!
>
> 1. Find some local shops or bookstores. You can shop at the sup...

> **Write several rhyming sentences from the perspective of Jay the RA, a resident a...**
> I'm sure you're interested in this rhyming couple. Every time you say "jay" in a
> rhyming word, you're actually talking to a friend and they have a conversation.
> Jay knows that they are together, so sh...

> **What other strange and obscure music genres can I check out?**
> While some of the most famous music genres are pop, rock, hip hop, rockabilly,
> and pop, you can also check out some other popular genres.

> **Write one paragraph about the Tlachihualtepetl pyramid. Keep it at or below 15 s...**
> The Tlachihualtepetl pyramid was built to be a symbolic and anarchic structure
> of stone. The pyramid would also symbolize the Tlachihualtepetl family, which
> was a descendant of the Paleolithic period.

> **The new Scream movie. It looks really good!**
> The film will be a hit but I think it's not the best in the world. I am having a
> ton of fun with it, so I hope to make it more exciting.

### What changed, and what did not

Compare these with the base model's generations in
[stage 02's run](../../02-pretrain/runs/2026-07-28-pretrain-3b.md), where
"The capital of France is" continued into "the city of Monaco, which is the
largest city in the Mediterranean" — the model treated the prompt as text to
continue.

These answer. Asked for five things, it produces a heading and starts a numbered
list. Asked for a paragraph, it writes a paragraph. Asked a question, it
responds rather than generating a plausible next question. It also stops, which
the base model would not do. **That is the entire behavioural claim of this
stage, and it is visible in three samples.**

What did not change is knowledge. "Candy, chocolate, and chocolate, are the two
popular desserts" is a sentence with the shape of an answer and no content;
pop appears twice in one list of distinct genres; the Tlachihualtepetl paragraph
is confident invention. SFT changed the form of the output and nothing about
what the model knows, which is the correct result — 9.8M tokens of instruction
data cannot install facts that 3.00B tokens of pretraining did not.

## What this run does not establish

- **That this is a good chat model.** No benchmark was run; the evidence here is
  a loss curve and six samples. Stage 07 owns measurement.
- **That three epochs is the right number.** Validation loss reached its best at
  step 250 of 309 and rose over the final 59 steps, the same late-run rise stage
  02 saw. One run cannot separate overfitting from evaluation noise. The saved
  checkpoint is the final one, not the best-scoring one.
- **That no_robots is the right dataset.** It was chosen for LIMA's argument
  (Zhou et al., 2023) that a small curated instruction set goes far. No
  alternative was tried, so this is a citation, not a finding.
- **That the 19.6% padding and 2.3% dropped conversations cost anything
  measurable.** Both are recorded because they are real, not because their
  impact was measured.

## Notes

- `core/sft.py` and `prod/trl_sft.py` both defaulted to splits `train_sft` and
  `test_sft`, which do not exist on this dataset. Every invocation of the
  documented command failed with `ValueError: Unknown split "train_sft"`. Fixed
  in `f671be9`. The lesson had working-looking code, a `draft` status, and no
  run — and the `draft` was the only thing keeping the claim honest.
- The local lane had no repository checkout; work had been done from ad-hoc
  copies in `~/agi-playground/`. This run was executed from a real clone at
  `~/repo-agi-playground` so that the command above is the command that ran.
- The venv had `torch` and `tokenizers` but neither `datasets` nor `pip`.
  `python -m ensurepip` then `pip install datasets` (5.0.0) fixed it.
