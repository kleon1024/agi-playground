# Run — the stage-06 harness against a served model, for real

Every prior run of `core/harness.py` used `FakeBackend` -- a canned script,
not a model. This run points it at an actual served checkpoint for the first
time.

## Why there is a server here at all

vLLM is not installed on this box, and installing it is out of scope: stage
05's `prod/vllm_serve.py` already covers "how you'd serve this with vLLM" as
its own chapter. This run's point is the agent-harness discipline, not
re-proving vLLM serving, so [`serve_for_agent.py`](serve_for_agent.py) is a
minimal stdlib `http.server` wrapping the stage-03 checkpoint directly,
exposing one route,
`POST /v1/chat/completions`, in the shape `harness.py`'s
`OpenAICompatibleBackend.generate` already expects. It reuses two pieces of
this repo verbatim rather than reinventing them: `Config`/`Transformer` from
stage 02's `model.py`, and the ChatML rendering (`<|im_start|>role\ncontent
<|im_end|>\n`) plus temperature/top-k sampling loop from stage 03's `sft.py`
(`render_prompt`/`generate`), which already implements what stage 05's
`KVCacheEngine` does not: temperature and a seed. One deliberate deviation:
`OpenAICompatibleBackend.generate` hardcodes `"temperature": 0` in every
request it sends, so honoring the request body would make every rollout
identical regardless of seed. The server ignores that field and samples with
temperature/seed fixed at process startup instead, restarting between
rollouts -- the effective values are what is recorded in each transcript's
`harness` block, not the meaningless request-body `0`.

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, driver 591.86, reached over Tailscale (same box as the serving/quantization runs) |
| Checkpoint | `stage03/ckpt/ckpt.pt`, the chat-tuned SFT model (not the base pretrain checkpoint -- the harness needs instruction-following behavior) |
| Tokenizer | `stage01/tokenizer_hf.json` |
| Sandbox root | a fresh `task_root/` containing exactly two files, `harness.py` and `tools.py` (copies) -- chosen so "how many Python files" has an unambiguous, pre-stated answer |
| Cost | \$0 (local lane); total GPU time across all 6 rollouts under 3 minutes |

## The tasks, and their ground truth, stated before running anything

1. **`count-py-files`** -- "How many Python files are in this directory?
   Answer with just the number." Ground truth: **2** (`harness.py`,
   `tools.py`; nothing else in `task_root/`).
2. **`find-resolve-in-jail`** -- "Which file defines the function named
   `resolve_in_jail`? Answer with the filename." Ground truth: **`tools.py`**
   (confirmed by reading the file before this run: `def resolve_in_jail(root:
   Path, relative: str) -> Path`).

Both are answerable from `list_dir`/`read_file` alone (`AUTO`-tier, no
confirmation needed), deliberately avoiding `run_command`, which is
`CONFIRM`-tier and the harness's own `default_confirm` denies unconditionally
in a non-interactive run -- exercising that tool here would only ever produce
a permission-denied observation, not a test of task-solving.

Each task ran 3 times, seeds 1001/1002/1003, temperature 0.7, top-k 50,
`--max-steps 6 --token-budget 4000` -- everything held fixed except the seed.

## Result: 0/6, and the same failure mode every time

| task_id | seed 1001 | seed 1002 | seed 1003 |
|---|---|---|---|
| `count-py-files` | max_steps | max_steps | max_steps |
| `find-resolve-in-jail` | max_steps | max_steps | max_steps |

Zero rollouts produced a parseable `Action:`/`Action Input:` pair or a `Final
Answer:`. All 36 individual generations (6 rollouts x 6 steps) fell through
`parse_response` into `ParsedStep(kind="unparsed")`, and every run exhausted
`max_steps` without the model calling a single tool. This is a legitimate,
informative result, not a bug in the harness or the server: an 88M-parameter
model SFT'd on `HuggingFaceH4/no_robots` (chat-formatted Q&A, no ReAct-style
tool-use examples) has never seen `Thought: / Action: / Action Input:` as a
protocol to imitate, and it shows -- the model produces fluent, topically
relevant prose (it clearly "knows" the task is about Python files, or about a
function name) but never once reproduces the literal scaffold the system
prompt asks for.

The nearest miss, `count-py-files` seed 1002 step 5, is worth reading because
it is the single clearest signal that the model recognizes the shape of the
protocol without being able to execute it:

```
Action:<Tool name>
```

That is a template placeholder, not a call -- the model appears to have
picked up "a line starting with `Action:`" as a pattern from *somewhere* in
its instruction data, but not the requirement to name a real tool or follow
with `Action Input:` and a JSON object. Every other step across all 6
rollouts is prose with no structural markers at all -- explanations,
hedges ("Yes, you can do this by..."), or repetition loops
(`# Calculate the iterator` x14 in `count-py-files` seed 1003 step 6).

## The grounding rule never actually fired

`enforce_grounding` truncates anything at or after a hallucinated
`Observation:` line before parsing. Across all 36 steps in this run, no raw
model response ever contained the string `Observation:` -- `grounding_
triggered` is `false` in every step of every transcript. This run demonstrates
a *format-following* failure, not a grounding-rule stress test: the model
never got far enough into a coherent ReAct turn to reach the point where it
might fabricate an observation. Confirming the grounding rule actually catches
a hallucinated `Observation:` still rests on `GROUNDING_DEMO_SCRIPT`'s
scripted `FakeBackend` demo, not this run.

## What this does and does not establish

- **Does establish**: the harness's plumbing -- backend protocol, ChatML
  rendering, stop-sequence request, response parsing, permission ladder,
  context compaction -- works end-to-end against a real served checkpoint
  over real HTTP, not just against `FakeBackend`.
- **Does establish**: this specific 88M SFT checkpoint cannot execute the
  ReAct protocol this harness expects, at temperature 0.7 across 3 seeds, on
  two tasks with clean tool-only solutions.
- **Does not establish**: that a larger model, or this same model trained
  with even a handful of ReAct-formatted examples in its SFT mix, would fail
  the same way. Nothing here tests whether the gap is model scale or missing
  training data -- distinguishing those is future work, not this run.
- **Does not establish** anything about the grounding rule's real-world
  behavior, for the reason above.

## Reproduce

```bash
# copy serve_for_agent.py, ../core/harness.py, and ../core/tools.py to the
# GPU box (this repo has no .git on the remote scratch host used here), plus
# a task_root/ holding exactly harness.py and tools.py, then:
python3 serve_for_agent.py --checkpoint stage03/ckpt/ckpt.pt \
    --tokenizer stage01/tokenizer_hf.json --device cuda --port 8811 \
    --seed 1001 --temperature 0.7 --top-k 50 --max-new-tokens 200

# in a second shell, against the running server:
AGENT_BASE_URL=http://localhost:8811/v1 AGENT_MODEL=stage03-sft \
python3 harness.py --root task_root \
    --task "How many Python files are in this directory? Answer with just the number." \
    --max-steps 6 --token-budget 4000
```

Repeat with `--seed 1002`/`1003` and the second task string. The 6 resulting
transcripts, in the shape `07-eval/core/evaluate.py`'s `agent-report`
subcommand expects, are in `transcripts/`. `serve_for_agent.py`
lives in `runs/`, not `core/` or `prod/`, because it exists only to stand in
for vLLM on a box that does not have it, not to teach a second serving
mechanism -- stage 05's `core/`/`prod/` is where the real serving lane is
taught.
