---
status: verified
level: applied
base: scratch
label: Chat template contract
verified: 2026-08-07
---

# The chat template is a contract

**Question:** SFT renders every conversation as
`<|im_start|>role\ncontent<|im_end|>\n` and trains only on the assistant
turn. The assistant header is supplied by the inference harness, never
predicted, so the model's whole notion of "a turn" lives in that exact
byte pattern. What breaks when the pattern drifts — a marker that is not
an id, a header that differs by one token, a mask that leaks user text?

**Before this:** [stage 03's SFT](../) for the template and the loss mask
this chapter audits. The claims there are the rule ("exactly one
convention, at train and inference time"); this chapter measures the
three properties the rule depends on, on the real frozen tokenizer, the
real masker, and the real 9,500-conversation no_robots training set.

## A marker is one id, or it is eight

The markers are ids 16385/16386, reserved out of the 127-id padding gap
stage 02 left. The frozen stage-01 vocabulary — trained on web documents,
which contain no chat markers — would split them instead. The run
([record](runs/2026-08-07-template-contract-audit.md)) encodes the marker
strings against that vocab:

The exact strings, as code:

```text
<|im_start|>  -> 1 id (16385) when reserved, 8 byte tokens when not
<|im_end|>    -> 1 id (16386) when reserved, 7 byte tokens when not
```

Across the 9,500 conversations that is 46,380 markers. Unreserved, they
would add about 301,000 tokens to the corpus — **+11.1%** of its real
tokens, before a single content token is considered. The per-conversation
inflation is small (1.1x on a long-answer example), which is why the cost
stays invisible until blocks fill up and long conversations start getting
dropped. The cost is the visible half; the invisible half is that an
8-token marker is a weaker convention than a 1-token one, because the
"a turn starts here" information is spread over eight positions that each
fire far less often as a unit. Reserve the ids at the tokenizer freeze, or
use a separator that already exists in the vocab; do not let the marker be
reconstructed from raw strings at serve time.

## The header is supplied, so it must be byte-exact

The canonical assistant header is ids [557, 8697, 10] — `assistant\n`.
The model never predicts it (it is masked out of the loss), so the harness
is the only source of the pattern the model uses to switch into answer
mode. The run encodes five plausible drift variants and records the first
token where each diverges from the trained pattern:

| served header | tokens | first divergence |
|---|---|---|
| `assistant` (no newline) | 2 | token 2 |
| `Assistant\n` (capital) | 3 | token 0 |
| ` assistant\n` (leading space) | 2 | token 0 |
| `assistant  \n` (extra space) | 4 | token 2 |
| `assistant\r\n` (CRLF) | 4 | token 2 |

Two of the five diverge at token 0 — the model has never seen that prefix
in training, so its continuation starts off-distribution immediately. This
is the measured shape of the main chapter's rule: the harness must render
the template from the same code path that rendered the training data, not
from a second template string that "looks the same". A parity check that
encodes the rendered prompt with the frozen tokenizer and compares ids
against the training render catches all five.

## The mask's job here is exclusion, not density

The mask exists to keep user and system text out of the loss. On this
curated set the answers are long — assistant turns average 177 tokens
against 83 for user prompts — so **68.2%** of the 2.72M real tokens in the
packed blocks are loss targets, and the mask's real work is the other
31.8%: keeping the model from being trained to imitate the user. The
distribution is the risk surface, not the average:

- per-block target share ranges from **1.7%** (a long-prompt conversation
  that trains almost entirely on masked context) to 88.7% at p90;
- 217 of 9,500 conversations exceed one 1024-token block and are dropped
  by packing — a silent data loss that a density report surfaces;
- the 3,305 blocks carry 663,715 padding tokens, 19.6% of block capacity.

That is why the masker's correctness is load-bearing: a masking bug on a
curated set leaks user text into a loss that is mostly answer, and on a
scraped or model-generated corpus (shorter answers, longer prompts) the
target share moves toward the measured 1.7% tail, where the same bug
trains the model on noise most of the time.

## The fix and its trade

The fix is the three guardrails the chapter measured, each owned by the
pipeline stage that can break it. Reserve the marker ids at the tokenizer
freeze (one id instead of eight, so 46,380 markers do not inflate the
corpus by +11.1%); render the header from the same code path that rendered
the training data, with a token-id parity check against the training render
as the test (it catches all five drift variants, two of them at token 0);
and keep the masker's correctness under unit tests, because on a curated
set the mask's real job is the 31.8% it excludes, not the 68.2% it trains.

The trade is in each guardrail's cost. Reserved ids spend vocabulary
headroom: 16385/16386 come out of the 127-id gap stage 02 left, and every
marker id competes with future tokens the vocabulary might need. The parity
check turns template rendering into a tested contract, which means a second
template string that "looks the same" is now a test failure instead of a
silent drift — the cost is that any legitimate template change has to update
the training render and the test together. The mask's exclusion trade is
the sharpest: at 68.2% target share the mask barely matters, but on scraped
or model-generated data (shorter answers, longer prompts) the share moves
toward the measured 1.7% tail, and the same masker bug that is a leak on
curated data becomes the dominant training signal. Packing carries its own
accepted trade — 217 of 9,500 conversations dropped, 19.6% padding — which
TRL and torchtune answer with block-diagonal attention masks at the cost of
a different memory and attention contract.

## Who owns the contract

- **Stage 01 (tokenizer) owns the reserved ids.** The freeze commits
  `tokenizer.json`; ids 16385-16387 are the headroom it left, and nothing
  downstream may rebuild the vocab or shift the ids.
- **The serve harness owns byte parity.** The prompt renderer is part of
  the SFT contract; a token-id parity test against the training render is
  the guardrail that catches the five variants above.
- **The data pipeline owns masker tests.** The mask trusts the role
  labels; a unit test over rendered examples (empty assistant turns,
  marker strings inside content, mislabeled roles) is what keeps user
  text out of the gradient. This chapter measures the healthy baseline;
  the injected-noise audit
  ([when-the-role-is-wrong](when-the-role-is-wrong/)) executes that
  test: the swapped role trains the model to imitate the user, the empty
  turn trains a silent no-op, and the alternation check finds 15 real
  anomalies in the curated set itself.

## What this chapter does not establish

All numbers are token-level measurements on the real tokenizer, the real
masker, and the real data. There is no GPU run, so header drift is shown
as token-sequence divergence, not as an end-to-end quality drop; and the
byte-split marker cost is a property of the frozen vocab, not a trained
comparison. The mask-density figure describes no_robots, a curated set —
the LIMA argument (Zhou et al., "LIMA: Less Is More for Alignment," 2023,
arXiv:2305.11206) that a small, carefully curated set gets most of the
way, now with the measured reason: the signal per block is dense and the
mask keeps it clean. The packing behavior (no attention reset at
boundaries, long examples dropped) is the accepted trade documented in
`core/sft.py`, not a claim that production packing is unnecessary — TRL
and torchtune add block-diagonal attention masks for exactly that reason.

## Next

Return to [stage 03](../) for the training commands, or continue to
[stage 04 — RL](../../04-rl/), where the objective stops being imitating
an answer and starts being improving one.
