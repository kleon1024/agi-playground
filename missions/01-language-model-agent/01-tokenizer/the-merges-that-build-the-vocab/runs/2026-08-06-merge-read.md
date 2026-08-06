# Run — the merges that build the vocabulary, read from the recorded BPE run

**Date:** 2026-08-06
**Command:** `uv run python core/merge_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the BPE training was the stage's recorded Modal
run).

## Purpose

Stage 01's BPE training recorded the merge sequence. This run reads the
record and lays out the progression.

## Output

```
  merge    256: 32,116 -> ' t' (x1,015,622)
  merge    257: 32,97 -> ' a' (x795,862)
  merge    258: 104,101 -> 'he' (x777,146)
  merge   1000: 265,97 -> 'ata' (x5,031)
  merge  11000: 2393,1435 -> 'sequently' (x157)
  merge  16000: 10024,12303 -> ' catastrophe' (x88)
```

## Notes

- The merge order is the vocabulary's logic: early merges collapse
  frequent characters and bigrams, late merges keep rare whole words.
- The sequence is what the 16,384-vocab tokenizer is built from, and the
  chars/token of 4.497 is the compression it achieves.
