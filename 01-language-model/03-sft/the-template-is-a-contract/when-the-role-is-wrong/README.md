---
status: verified
level: applied
base: scratch
label: When the role is wrong
verified: 2026-08-07
---

# The mask trusts the role. What happens when the role is wrong?

**Question:** stage 03's masker keeps user text out of the loss by trusting
one thing — the role label on each turn. What does the model actually get
trained to imitate when that label is wrong: a swapped role, an empty
assistant turn, or marker strings that leaked into content?

**Before this:** [the chat template is a contract](../) measured the
healthy baseline — what the mask trains on when the data is clean. This
detour breaks the data and reads the loss, on the same real tokenizer,
the same real masker, and the same 9,500-conversation no_robots set.

## The mask's only source of truth is the role label

The masker decides the loss span from one string: `turn["role"]`. An
assistant turn's content is a loss target; everything else is `-100`. It
never looks at the text — it cannot know whether a sentence was written
by the user or the assistant, so the entire defense against imitating the
user is the metadata, and the metadata is produced by whoever built the
dataset. Human-curated sets like no_robots are the LIMA argument (Zhou et
al., 2023, arXiv:2305.11206): a small, carefully written set gets most of
the way — but "carefully written" is a property of the pipeline, and the
audit below finds the defect classes the pipeline has to check for,
because even the curated set carries a few.

## A swapped role teaches the model to imitate the user

The run ([record](runs/2026-08-07-injected-noise-audit.md)) takes one
real two-turn conversation and swaps the roles. The clean row contributes
24 target tokens — the answer. The swapped row contributes 214: 213 of
the user's tokens are now loss targets, and the decoded target span is
the user's question verbatim:

```text
target span the loss imitates:
'Please summarize the goals for scientists in this text: ...'
```

That is not a formatting slip. Cross-entropy trains exactly this span, so
the model is being taught to reproduce the user's sentence as its answer,
while the real answer's 23 tokens lose target status. The case-variant
role (`Assistant` instead of `assistant`) is the silent version: the
whole turn falls into the masked branch, and 0 tokens of the answer are
ever trained — a data drop with no error anywhere. This is why role
membership has to be an exact set, checked before rendering, not a
best-effort convention.

## An empty assistant turn trains "answer with nothing"

An assistant turn with empty content renders to exactly one loss target:
the closing marker. When it is the last turn, the entire conversation is
a silent no-op that teaches the model to emit the stop marker right after
the header — an answer-shaped model that produces no answer. The
empty-turn defect is the signature of a synthetic pipeline whose answer
extraction failed but still emitted a row; a mid-conversation empty turn
teaches the same lesson for its prompt while later turns train normally,
which is why it is a data-quality bug that never surfaces as a crash.

## Markers: the tokenizer defends, the pipeline does not

Content cannot forge a role boundary on this stack. The frozen stage-01
vocab byte-splits the string `<|im_start|>` into 8 ordinary tokens —
never the reserved id 16385 — because the ids are assigned by the render
code, not by the tokenizer. That defense has one upstream hole: a
pipeline that stores already-rendered ChatML as a message and re-renders
it. Then the byte-split markers land inside the assistant content, and
the loss imitates them — the double-rendered row produces 274 targets
with 4 literal marker strings inside the target span, so the model is
trained to emit a nested transcript with `<|im_start|>user...` inside its
answers. Any downstream parser that scans decoded text for markers then
sees a phantom turn boundary. The check is text-level: no marker string
may appear in any content, because the only legitimate place for a marker
is the render code.

## The guardrail, executed — and what it found in the curated data

`validate_row` in the audit script runs four text-level checks before any
rendering: role membership (exact set), non-empty assistant content,
marker strings in content, and role alternation (consecutive turns with
the same role, the signature of a stamped pipeline that labeled every
turn assistant — the one the last-turn rule cannot see). On the five
injected defect classes it catches all five. On the real no_robots rows
it finds 15 problems in 9,500 conversations (0.16%), every one a
consecutive duplicate assistant role — and row 741's final pair reads
like a user reply ("Thanks. I'm just worried they won't like me
anymore.") labeled as assistant: the exact leak class, present in the
curated benchmark itself.

The guardrail's cost is one string scan per row at the pipeline boundary;
its trade is that it catches the mechanical defect classes and not
ambiguous intent — a role that is wrong but well-formed (both sides look
plausible) needs a sample review, not a rule. That is still the right
split: the checks catch the bugs that would otherwise leak user text into
the loss at scale, and the flag rate on curated data (0.16%) is small
enough that every flag is worth a human look.

## The fix and its trade

The fix is a row-level validator at the pipeline boundary, before any
rendering: role membership as an exact set, non-empty assistant content, no
marker strings in content, and role alternation — the four checks the audit
runs, catching all five injected defect classes and finding 15 real
anomalies in 9,500 curated rows (0.16%). The cost is one string scan per
row, which is the whole point of the placement: a defect is caught as a row
with a problem list, not as a model that imitates the user after a two-day
fine-tune.

The trade is that the validator catches mechanical classes and not
ambiguous intent. A role that is wrong but well-formed — both sides of the
conversation look plausible — passes every rule and needs a sample review,
which is why the 0.16% flag rate is the budget that makes human looks
affordable, not a license to trust the checks. The alternation check is the
one easy to over-trust: it catches the stamped-pipeline signature (238
targets on a two-turn stamped row that the last-turn rule misses), but a
pipeline that stamps roles with correct alternation still carries the same
defect while passing every rule, so the checks are a floor, not a proof.
The final trade is on the double-rendered row: the text-level marker check
closes the hole the tokenizer cannot (byte-split markers can never forge
the reserved id), but it costs the pipeline a content constraint — no
legitimate content may ever contain a marker string, because the only
allowed source of a marker is the render code.

## Who owns the loop

The data pipeline owns the masker's tests — the main chapter named this
handoff, and this detour executes it. The validator runs on raw rows
before rendering, so a defect is caught as a row with a problem list,
not as a model that imitates the user after a two-day fine-tune. The
model team consumes clean rows and owns the render path; the data team
owns the row contract. When nobody owns it, the synthetic pipeline
stamps wrong roles, the masker faithfully trains them, and the failure
shows up later as a chat model that echoes the user — attributed to
everything except the one line of metadata that caused it.

## What this chapter does not prove

The consequence of a leaked target is shown as the decoded span the loss
imitates, not as an end-to-end quality drop on a trained model — there
is no GPU run here. The mechanism is direct (cross-entropy trains exactly
the target span), but the magnitude of the behavioral change on a real
checkpoint is not measured. The injected defects are synthetic and
deterministic; real pipelines should scan their own rows with the same
validator and read the flag rate against a sample review before
thresholding.

## Check your mental model

Answer each before opening it.

**1. Why can't the masker detect a wrong role by reading the text?**

<details>
<summary>Answer</summary>

Because it decides the loss span from the role label alone and never
looks at the text — that is the design. Detecting "this content is really
user text" from the content itself is an open problem, so the defense has
to live where the metadata is produced: a row-level check before
rendering, which is the guardrail this chapter executes.

</details>

**2. Why is role alternation a check and not a style preference?**

<details>
<summary>Answer</summary>

Because the stamped-pipeline defect — every turn labeled assistant —
passes role membership, passes the empty-turn check, and ends in an
assistant turn, so the other rules cannot see that the user's question is
being trained as the model's own words. Consecutive duplicate roles are
the fingerprint of that bug, and the run confirms it: 238 targets on a
two-turn stamped row, and the last-turn rule misses it.

</details>

## Next

Return to [the template contract](../) or [stage 03](../../), where the
trainer renders and masks rows; the guardrail's checks are the row
contract that data must pass before any of that runs.
