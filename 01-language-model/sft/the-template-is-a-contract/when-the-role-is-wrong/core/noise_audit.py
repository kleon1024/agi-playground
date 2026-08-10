"""The mask trusts the role. Measure what the loss trains when the
trust is wrong.

Stage 03's masker excludes user text by trusting the role label on each
turn: `turn["role"] == "assistant"` decides the loss span, and everything
else is `IGNORE_INDEX`. That is a trust boundary, and this audit measures
what actually becomes a loss target when the metadata the mask depends on
is wrong, on the real frozen tokenizer, the real `render_and_mask`, and
the real 9,500-conversation no_robots set:

  1. The real-data baseline. Scan the curated conversations for the
     defect classes the masker's tests exist to catch: non-canonical role
     strings (case variants, unknown roles), empty assistant turns, rows
     whose last turn is not assistant, and literal marker strings inside
     content. Curated data is expected to be clean; the scan fixes the
     guardrail's false-positive rate on the data it is meant to protect.

  2. Role mislabels. A swapped role makes user text a loss target and
     suppresses the answer; a case-variant role ("Assistant") silently
     suppresses the whole turn with no error anywhere. Each is rendered
     with the real masker, and the decoded target span shows verbatim what
     the model is trained to imitate. A corpus-scale pass then swaps the
     roles of every 20th two-turn row and measures what a 5% swap rate does
     to the loss mix: how many user tokens become targets and how many
     answer tokens disappear.

  3. Empty assistant turns. An empty turn renders to exactly one loss
     target, the closing marker: the row trains "answer with nothing."
     When the empty turn is the last turn, the whole conversation is a
     silent no-op.

  4. Marker strings inside content. Content cannot forge a role boundary
     on this stack: the frozen vocab byte-splits the marker string, and
     the reserved ids are assigned by the render code, not the tokenizer.
     The failure is upstream: a pipeline that stores already-rendered
     ChatML as a message and re-renders it puts the byte-split markers
     inside the target span, so the model is trained to emit literal
     marker strings in its answers.

  5. The guardrail, executed. `validate_row` runs text-level checks on the
     raw rows before any rendering. This audit runs it over the injected
     defects (recall) and the real rows (false positives), so the fix the
     main chapter names -- "a unit test over rendered examples" -- has a
     measured cost.

Deterministic (single seed), CPU-only, about 15 seconds. Reads
HuggingFaceH4/no_robots from the local dataset cache (offline) and the
frozen tokenizer via the stage 01 HF export; see the runs record for the
export command.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

IM_START = 16385
IM_END = 16386
PAD_ID = 16387

CANONICAL_ROLES = {"system", "user", "assistant"}
MARKER_STRINGS = ("<|im_start|>", "<|im_end|>")


def load_masker(sft_path: Path):
    """Import the real masker and packer from stage 03's trainer."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("sft", sft_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render_and_mask, mod.pack


def validate_row(turns: list[dict]) -> list[str]:
    """Text-level checks that run on the raw rows, before any rendering.

    The mask trusts the role label, so the guardrail's checks are the ones
    that make the trust safe to grant. They are deliberately text-level:
    the data pipeline can run them on a row before the tokenizer is even
    loaded, and the tests stay hermetic.
    """
    problems: list[str] = []
    if not turns:
        return ["empty conversation: nothing to train on"]
    for i, turn in enumerate(turns):
        role = turn.get("role", "")
        content = turn.get("content")
        if role not in CANONICAL_ROLES:
            problems.append(
                f"turn {i}: role {role!r} is not in {sorted(CANONICAL_ROLES)}"
            )
        if role == "assistant" and (content is None or not content.strip()):
            problems.append(
                f"turn {i}: empty assistant turn trains only the stop marker"
            )
        if i > 0 and turn.get("role") == turns[i - 1].get("role"):
            problems.append(
                f"turn {i}: role {role!r} repeats the previous role "
                "(turns alternate in ChatML; a stamped pipeline leaks the "
                "user's text into the loss)"
            )
        if content and any(m in content for m in MARKER_STRINGS):
            problems.append(
                f"turn {i}: content contains a literal marker string "
                "(double-render leak)"
            )
    if turns[-1]["role"] != "assistant":
        problems.append("last turn is not assistant: nothing to train the loss on")
    return problems


def _text(row: dict) -> str:
    return row.get("content") or ""


def scan_real(rows) -> dict:
    """Defect scan over the real curated rows: what the guardrail must
    catch, and how often each class actually shows up."""
    roles: dict[str, int] = {}
    empty_assistant = 0
    not_assistant_last = 0
    marker_content = 0
    n_rows = 0
    for row in rows:
        turns = row["messages"]
        n_rows += 1
        if not turns:
            continue
        for turn in turns:
            role = turn.get("role", "")
            roles[role] = roles.get(role, 0) + 1
            if role == "assistant" and not _text(turn).strip():
                empty_assistant += 1
            if any(m in _text(turn) for m in MARKER_STRINGS):
                marker_content += 1
        if turns[-1].get("role") != "assistant":
            not_assistant_last += 1
    return {
        "rows": n_rows,
        "roles": roles,
        "empty_assistant_turns": empty_assistant,
        "rows_not_ending_in_assistant": not_assistant_last,
        "turns_with_marker_strings": marker_content,
    }


def first_two_turn_row(rows, min_len: int = 8):
    """First deterministic row shaped exactly [user, assistant], both sides
    non-trivial, so the injected defects share one real conversation."""
    for row in rows:
        turns = row["messages"]
        if (
            len(turns) == 2
            and turns[0]["role"] == "user"
            and turns[1]["role"] == "assistant"
            and len(_text(turns[0]).strip()) >= min_len
            and len(_text(turns[1]).strip()) >= min_len
        ):
            return turns
    raise RuntimeError("no two-turn row found")


def render_targets(turns, render_and_mask, tok) -> dict:
    """Render with the real masker and describe the target span: what the
    loss is actually training the model to imitate."""
    ids, labels = render_and_mask(turns, tok)
    target_ids = [i for i, lab in zip(ids, labels) if lab != -100]
    body_ids = [i for i in target_ids if i not in (IM_START, IM_END)]
    n_byte_markers = 0
    for marker in (tok.encode("<|im_start|>").ids, tok.encode("<|im_end|>").ids):
        for start in range(len(body_ids) - len(marker) + 1):
            if body_ids[start : start + len(marker)] == marker:
                n_byte_markers += 1
    return {
        "n_targets": len(target_ids),
        "n_marker_targets": sum(1 for i in target_ids if i in (IM_START, IM_END)),
        "n_byte_marker_strings_in_target": n_byte_markers,
        "decoded_target": tok.decode(body_ids),
    }


def corpus_swap_effect(rows, render_and_mask, tok, every: int = 20) -> dict:
    """Swap the roles of every `every`-th two-turn row and measure the
    change to the loss mix: leaked user tokens now taught as answers, and
    answer tokens suppressed from the loss. `every = 20` is a 5% swap rate."""
    leaked = suppressed = clean_targets = swapped_targets = corrupted = 0
    for idx, row in enumerate(rows):
        turns = row["messages"]
        if len(turns) == 2 and turns[0]["role"] == "user" \
                and turns[1]["role"] == "assistant" and idx % every == 0:
            ids_c, labels_c = render_and_mask(turns, tok)
            clean_targets += sum(1 for lab in labels_c if lab != -100)
            swap = [{"role": "assistant", "content": turns[0]["content"]},
                    {"role": "user", "content": turns[1]["content"]}]
            ids_s, labels_s = render_and_mask(swap, tok)
            swapped_targets += sum(1 for lab in labels_s if lab != -100)
            leaked += sum(
                1 for i, lab in zip(ids_s, labels_s)
                if lab != -100 and i not in (IM_START, IM_END)
            )
            suppressed += sum(
                1 for i, lab in zip(ids_c, labels_c)
                if lab != -100 and i not in (IM_START, IM_END)
            )
            corrupted += 1
    return {
        "corrupted_rows": corrupted,
        "clean_targets": clean_targets,
        "swapped_targets": swapped_targets,
        "leaked_user_tokens": leaked,
        "suppressed_answer_tokens": suppressed,
    }


def run(args) -> None:
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

    from datasets import load_dataset
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(args.tokenizer))
    render_and_mask, _ = load_masker(args.sft_path)
    rows = list(load_dataset("HuggingFaceH4/no_robots", split="train").select(
        range(min(args.rows, 9606))
    ))

    print("injected-noise audit (real tokenizer, real masker, real no_robots "
          f"{len(rows):,} conversations):")
    print()

    # 1. The real-data baseline.
    scan = scan_real(rows)
    print("  1. real-data defect scan (what the guardrail must catch):")
    print(f"     rows scanned: {scan['rows']:,}")
    print(f"     role values seen: {scan['roles']}")
    print(f"     empty assistant turns: {scan['empty_assistant_turns']}")
    print(f"     rows not ending in assistant: {scan['rows_not_ending_in_assistant']}")
    print(f"     turns containing a literal marker string: "
          f"{scan['turns_with_marker_strings']}")
    print()

    # 2-4. Injected defects on one real two-turn conversation.
    clean = first_two_turn_row(rows)
    q, a = _text(clean[0]).strip(), _text(clean[1]).strip()
    q_short = q if len(q) <= 72 else q[:72] + "..."
    a_short = a if len(a) <= 72 else a[:72] + "..."
    print(f"  host conversation (row {args.seed % 5000:>4,}, "
          f"{len(q)} user / {len(a)} assistant tokens by char):")
    print(f"    user:      {q_short!r}")
    print(f"    assistant: {a_short!r}")

    clean_t = render_targets(clean, render_and_mask, tok)

    swap = [{"role": "assistant", "content": q}, {"role": "user", "content": a}]
    swap_t = render_targets(swap, render_and_mask, tok)
    print()
    print("  2. role mislabels, executed:")
    print(f"     clean two-turn row: {clean_t['n_targets']} target token(s), "
          f"answer only")
    print(f"     swapped roles:      {swap_t['n_targets']} target token(s) = "
          f"{swap_t['n_marker_targets']} marker + user text; "
          f"{swap_t['n_targets'] - swap_t['n_marker_targets']} of the user's "
          f"tokens are now taught as the answer")
    print("     decoded target span the model is trained to imitate:")
    print(f"       {swap_t['decoded_target'][:140]!r}")
    print(f"     the real answer is suppressed: {clean_t['n_targets'] - 1} "
          f"answer token(s) lose target status")
    case = [{"role": "user", "content": q}, {"role": "Assistant", "content": a}]
    case_t = render_targets(case, render_and_mask, tok)
    print(f"     case-variant role 'Assistant': {case_t['n_targets']} target "
          f"token(s) -- the whole turn vanishes from the loss with no error")

    empty = [{"role": "user", "content": q}, {"role": "assistant", "content": ""}]
    empty_t = render_targets(empty, render_and_mask, tok)
    print()
    print("  3. empty assistant turn (last turn), executed:")
    print(f"     targets: {empty_t['n_targets']} token(s) -- exactly the "
          f"closing marker; decoded: {empty_t['decoded_target']!r}")
    print("     the row trains 'answer with nothing'; a mid-conversation "
          "empty turn teaches the same for its prompt but lets later turns "
          "train normally")

    double = [
        {"role": "user", "content": q},
        {
            "role": "assistant",
            "content": (
                f"<|im_start|>user\n{q}<|im_end|>\n"
                f"<|im_start|>assistant\n{a}<|im_end|>\n"
            ),
        },
    ]
    double_t = render_targets(double, render_and_mask, tok)
    marker_ok = tok.encode("<|im_start|>").ids
    print()
    print("  4. marker strings inside content, executed:")
    print(f"     content cannot forge a role boundary: the frozen vocab "
          f"byte-splits '<|im_start|>' into {len(marker_ok)} token(s) "
          f"{marker_ok}, never the reserved id {IM_START}")
    print("     double-rendered row (pre-rendered ChatML stored as a "
          "message and re-rendered):")
    print(f"       {double_t['n_targets']} target token(s), "
          f"{double_t['n_byte_marker_strings_in_target']} literal marker "
          f"string(s) inside the target span")
    print("       decoded target span:")
    print(f"       {double_t['decoded_target'][:160]!r}")

    # 5. The guardrail, executed: recall on the injected defects, false
    # positives on the real rows.
    stamped = [{"role": "assistant", "content": q},
               {"role": "assistant", "content": a}]
    stamped_t = render_targets(stamped, render_and_mask, tok)
    print()
    print("  the stamped-pipeline variant (every turn labeled assistant):")
    print(f"     {stamped_t['n_targets']} target token(s) -- the user's "
          f"question is taught as the model's own words, and the last-turn "
          f"rule cannot see it")
    print()
    print("  corpus-scale effect of a 5% role-swap rate "
          "(every 20th two-turn row):")
    cs = corpus_swap_effect(rows, render_and_mask, tok, every=20)
    print(f"     rows corrupted: {cs['corrupted_rows']}")
    print(f"     clean target tokens on those rows: {cs['clean_targets']:,}")
    print(f"     after the swap:                   {cs['swapped_targets']:,}")
    print(f"     user tokens now taught as answers: {cs['leaked_user_tokens']:,}")
    print(f"     answer tokens suppressed:          "
          f"{cs['suppressed_answer_tokens']:,}")
    if cs["clean_targets"]:
        print(f"     {cs['leaked_user_tokens'] / cs['clean_targets']:.0%} of the "
              f"corrupted rows' clean targets become user text")

    defects = {
        "role swap": swap,
        "case-variant role": case,
        "empty assistant turn": empty,
        "double-rendered content": double,
        "stamped all-assistant": stamped,
    }
    print()
    print("  5. the guardrail (validate_row), executed:")
    for name, turns in defects.items():
        problems = validate_row(turns)
        status = "caught" if problems else "MISSED"
        print(f"     {name:<24} {status}: {problems[0] if problems else 'clean'}")
    from collections import Counter

    real_counter: Counter = Counter()
    for row in rows:
        real_counter.update(validate_row(row["messages"]))
    print(f"     real no_robots rows: {sum(real_counter.values())} problem(s) "
          f"across {len(rows):,} rows, by rule:")
    for msg, count in real_counter.most_common():
        print(f"       {msg} x{count}")
    print()
    print("  verdict: the masker's trust is in the role metadata, so the")
    print("  guardrail belongs at the data-pipeline boundary - role")
    print("  membership, non-empty assistant turns, and marker strings in")
    print("  content - before rendering, where the failure is visible as a")
    print("  row, not as a model that imitates the user.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", type=Path,
                    default=Path("/tmp/tokenizer_hf.json"))
    ap.add_argument("--sft-path", type=Path,
                    default=Path(__file__).resolve().parents[3]
                    / "core" / "sft.py")
    ap.add_argument("--rows", type=int, default=9500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    run(args)


if __name__ == "__main__":
    main()
