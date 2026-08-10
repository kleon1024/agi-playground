# Run — injected-noise audit: what the mask trains when the role is wrong

**Date:** 2026-08-07
**Commands:**

```bash
# export the frozen stage-01 tokenizer to HF format (parity verified in
# 01-tokenizer/runs/2026-07-26-bpe-16k.md)
cd 01-language-model/01-tokenizer/prod
python hf_tokenizer.py export ../tokenizer.json /tmp/tokenizer_hf.json \
    --corpus <corpus-dir> --verify-docs 300

cd 01-language-model/03-sft/the-template-is-a-contract/when-the-role-is-wrong/core
python noise_audit.py --tokenizer /tmp/tokenizer_hf.json
```

**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; tokenizers 0.23.1; datasets from the
local HuggingFace cache (offline).
**Wall-clock:** 3.2s (9,500 conversations scanned, rendered, corrupted, and
re-rendered).
**Cost:** \$0 (local lane).

## Purpose

Stage 03's masker keeps user text out of the loss by trusting one thing:
the role label on each turn (`turn["role"] == "assistant"` decides the
loss span). The template-contract audit measured the healthy baseline;
this run breaks the metadata and reads the loss, on the real frozen
tokenizer, the real `render_and_mask`, and the real 9,500-conversation
no_robots set. It answers three questions: what the loss trains when a
role is swapped, when an assistant turn is empty, and when marker strings
leak into content — then executes the row-level guardrail that catches
all of it, and reports what the guardrail finds in the curated data
itself.

## Output

```
injected-noise audit (real tokenizer, real masker, real no_robots 9,500 conversations):

  1. real-data defect scan (what the guardrail must catch):
     rows scanned: 9,500
     role values seen: {'user': 11190, 'assistant': 11205, 'system': 795}
     empty assistant turns: 0
     rows not ending in assistant: 0
     turns containing a literal marker string: 0

  host conversation (row   42, 1055 user / 133 assistant tokens by char):
    user:      'Please summarize the goals for scientists in this text:\n\nWithin three da...'
    assistant: 'Scientists are studying nests hoping to learn about transitional habitat...'

  2. role mislabels, executed:
     clean two-turn row: 24 target token(s), answer only
     swapped roles:      214 target token(s) = 1 marker + user text; 213 of the user's tokens are now taught as the answer
     decoded target span the model is trained to imitate:
       'Please summarize the goals for scientists in this text:\n\nWithin three days, the intertwined cup nest of grasses was complete, featuring a ca'
     the real answer is suppressed: 23 answer token(s) lose target status
     case-variant role 'Assistant': 0 target token(s) -- the whole turn vanishes from the loss with no error

  3. empty assistant turn (last turn), executed:
     targets: 1 token(s) -- exactly the closing marker; decoded: ''
     the row trains 'answer with nothing'; a mid-conversation empty turn teaches the same for its prompt but lets later turns train normally

  4. marker strings inside content, executed:
     content cannot forge a role boundary: the frozen vocab byte-splits '<|im_start|>' into 8 token(s) [60, 124, 317, 95, 306, 433, 124, 62], never the reserved id 16385
     double-rendered row (pre-rendered ChatML stored as a message and re-rendered):
       274 target token(s), 4 literal marker string(s) inside the target span
       decoded target span:
       '<|im_start|>user\nPlease summarize the goals for scientists in this text:\n\nWithin three days, the intertwined cup nest of grasses was complete, featuring a canop'

  the stamped-pipeline variant (every turn labeled assistant):
     238 target token(s) -- the user's question is taught as the model's own words, and the last-turn rule cannot see it

  corpus-scale effect of a 5% role-swap rate (every 20th two-turn row):
     rows corrupted: 439
     clean target tokens on those rows: 96,207
     after the swap:                   48,069
     user tokens now taught as answers: 47,630
     answer tokens suppressed:          95,768
     50% of the corrupted rows' clean targets become user text

  5. the guardrail (validate_row), executed:
     role swap                caught: last turn is not assistant: nothing to train the loss on
     case-variant role        caught: turn 1: role 'Assistant' is not in ['assistant', 'system', 'user']
     empty assistant turn     caught: turn 1: empty assistant turn trains only the stop marker
     double-rendered content  caught: turn 1: content contains a literal marker string (double-render leak)
     stamped all-assistant    caught: turn 1: role 'assistant' repeats the previous role (turns alternate in ChatML; a stamped pipeline leaks the user's text into the loss)
     real no_robots rows: 15 problem(s) across 9,500 rows, by rule:
       turn 5: role 'assistant' repeats the previous role (turns alternate in ChatML; a stamped pipeline leaks the user's text into the loss) x12
       turn 7: role 'assistant' repeats the previous role (turns alternate in ChatML; a stamped pipeline leaks the user's text into the loss) x3

  verdict: the masker's trust is in the role metadata, so the
  guardrail belongs at the data-pipeline boundary - role
  membership, non-empty assistant turns, and marker strings in
  content - before rendering, where the failure is visible as a
  row, not as a model that imitates the user.
```

## What the numbers show

- **A swapped role is a training-time leak, not a formatting bug.** One
  swapped two-turn row turns 213 user tokens into loss targets — against
  the 24 target tokens the clean row contributes — and suppresses the 23
  real answer tokens. The decoded target span is the user's question
  verbatim: the model is trained to imitate the user. A case-variant role
  (`Assistant`) is the silent version: 0 targets, the whole turn vanishes
  with no error anywhere.
- **An empty assistant turn trains "answer with nothing."** An empty last
  turn renders to exactly one target — the closing marker — so the entire
  row is a silent no-op that teaches the stop marker, not an answer.
- **The tokenizer defends the marker; the pipeline does not.** Content
  cannot forge a role boundary: the frozen vocab byte-splits the marker
  string into 8 tokens and never emits the reserved id. The failure is
  upstream — a pipeline that stores already-rendered ChatML as a message
  and re-renders it puts 4 literal marker strings inside the target span,
  training the model to reproduce the nested transcript with markers.
- **The last-turn rule is not enough.** A pipeline that stamps every turn
  as assistant produces 238 targets including the user's question, and
  the last turn IS assistant, so only a role-alternation check sees it.
- **At corpus scale the leak compounds.** A 5% role-swap rate (439 of the
  two-turn rows) turns 50% of the corrupted rows' clean targets into user
  text: 47,630 leaked user tokens against 95,768 suppressed answers.
- **The curated set is not perfectly clean.** The guardrail's alternation
  rule flags 15 of 9,500 no_robots rows (0.16%), all ending in two
  consecutive assistant responses; row 741's final pair reads like a user
  reply ("Thanks. I'm just worried they won't like me anymore.") labeled
  as assistant — the exact leak class, in the curated benchmark itself.

## Evidence boundary

- All numbers are token-level measurements on the real tokenizer, the
  real masker, and the real no_robots data; the injected defects are
  synthetic and deterministic (single seed), labeled as illustrative in
  the chapter.
- There is no GPU run: the consequence of a leaked target is shown as the
  decoded span the loss imitates, not as an end-to-end quality drop. The
  mechanism is direct — cross-entropy trains exactly the target span —
  but the magnitude of the behavior change on a real model is not
  measured here.
- The row-741 reading ("reads like a user reply") is an inspection
  observation, not a verified ground truth about the annotator's intent;
  the verifiable fact is the alternation anomaly itself.
