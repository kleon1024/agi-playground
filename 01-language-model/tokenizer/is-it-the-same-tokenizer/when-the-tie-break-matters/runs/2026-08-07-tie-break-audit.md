# Run — tie-break audit: the same corpus, the same rule, two vocabularies

**Date:** 2026-08-07
**Commands:**

```bash
cd 01-language-model/01-tokenizer/is-it-the-same-tokenizer/when-the-tie-break-matters/core
python tiebreak_audit.py --train-docs 8500 --held-out 1000 --vocab-size 4096
```

**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; `datasets` 5.0.1 and `tokenizers` 0.23.1
from the local HuggingFace cache (offline).
**Wall-clock:** 12.4s real.
**Cost:** \$0 (local lane).

## Purpose

The parent chapter proved two implementations produce the *same* vocabulary
when they run the same algorithm with the same tie-break. This audit measures
the silent second axis the parent deliberately held fixed: what happens when
the tie-break itself differs. BPE's "merge the most frequent pair" is a partial
order — real text produces real ties — and whichever pair wins a tie is
arbitrary but not inconsequential, because a merge rewrites the counts around
it. Two runs of the *same* algorithm on the *same* corpus can therefore learn
different vocabularies, and the aggregate metrics a team checks may not see it.

The run trains an indexed BPE (`core/bpe.py`'s `train_bpe_indexed` logic,
imported by `tiebreak_audit.py`) twice on the same 8,500 no_robots training
turns, under two deterministic tie-break rules (lexicographic and
reverse-lexicographic on the pair), then reads the divergence on 1,000 held-out
turns: tie incidence during training, the first divergent merge, merge-set
overlap at several depths, held-out chars/token, piece-level segmentation
disagreement, and edge-case encodings for numbers, CJK, and accented
characters.

## Output

```
tokenizer tie-break audit (real no_robots, CPU):
  train docs 8,500, held-out 1,000, 51,707 unique pieces, vocab 4096

  1. tie incidence: 3522/3840 steps (91.7%) chose from a tie; mean width 25.7, max 194
  2. divergence: first different pair at step 132; merge-set Jaccard at depth 500/1000/2000/all: 0.508 / 0.506 / 0.534 / 0.541
  3. held-out chars/token: lex 3.418 vs rlex 3.416
     held-out segmentation: 39,525/96,383 pieces differ (41.0%); 250 differ in token count

  edge-case encodings (tokens; same under both arms at vocab 4096):
     28 tokens: 3|,|14|1|,|5|9|2| is| appro|x|imately| p|i| times| 1|,000|,000| and| 12|3|4|5|6|7|8|9|0
     48 tokens: �|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|3|3|3|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�|�
     13 tokens: c|af|é| n|a|�|�|ve| r|é|s|um|é
     11 tokens: he|ll|o| world|,| the| cat| sat| on| the| mat

  verdict: the tokenizer's tie-break is a hidden axis of the model. The same corpus and the same 'merge the most frequent pair' rule produce different vocabularies whenever real text ties, and the difference lands exactly on the edges a downstream model cares about: numbers and rare characters.
```

## Reading the output

The tie is the norm, not the exception: 91.7% of 3,840 merge steps chose from
a tie, with a mean tie width of 25.7 pairs and a maximum of 194. A tie-break
rule is therefore exercising real decision-making power on essentially every
merge. The first divergence lands early (step 132), and merge-set Jaccard
settles around 0.51-0.54 across depths — the two vocabularies share roughly
half their merge decisions. One early tie choice cascades through every
subsequent count.

The aggregate metric cannot see this. Held-out chars/token is 3.418 under the
lex rule and 3.416 under reverse-lex — identical within rounding — while 41.0%
of held-out pieces encode to a different token sequence. The divergence is
mostly *which* tokens, not *how many*: only 250 of 96,383 pieces differ in
token count. A team comparing two tokenizer implementations by chars/token (or
by loss) sees no signal; the segmentation is still different under the hood.

The edge cases show where the difference lands. A 28-token sentence containing
the number 1,234,567,890 splits per-digit (`12|3|4|5|6|7|8|9|0`) because the
pre-tokenizer caps digit runs at `\d{1,3}`; CJK characters fragment to 3
bytes-pieces each via the 256-byte base; accented characters split to 2 pieces.
Both arms agree on these at vocab 4096, but these are exactly the pieces where
real production tokenizers differ from each other, and where downstream
behavior measurably changes — number tokenization alters arithmetic accuracy
on frontier models (Singh et al., arXiv:2402.14903, Feb 2024: comma-separated
right-to-left number tokenization improves GPT-3.5/GPT-4 arithmetic, while
left-to-right digit runs produce stereotyped digit-4 errors).

## Evidence boundary

Mechanism demo at toy vocabulary size (4,096, not the mission's 16,384), on
one curated corpus (no_robots), with two fixed deterministic tie-break rules.
The run proves the divergence mechanism exists and measures its shape; it
does not train a model, so it does not measure the end-to-end behavioral cost.
That magnitude is cited to the external source above. Production tokenizers
also differ in pre-tokenizer digit rules and byte handling, which this run
holds fixed — real-world differences are therefore at least as large as what
is measured here.
