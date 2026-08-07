"""The mask trusts the role, so the guardrail catches wrong metadata.

Stage 03's masker decides the loss span from `turn["role"]` alone; it
never reads the text, so the only defense against a wrong role is a check
that runs on the raw row before rendering. This test pins the guardrail
from the injected-noise audit
(`01-language-model/03-sft/the-template-is-a-contract/when-the-role-is-wrong/`)
to the defect classes it exists to catch: a role-swapped conversation, a
case-variant role, an empty assistant turn, marker strings that leaked
into content (double-render), and a pipeline that stamped every turn as
assistant. It also pins the clean row: a normal conversation must pass.

CPU-only, no torch, no dataset, no tokenizer: the guardrail is text-level
by design, so it can run in the data pipeline before the tokenizer is
even loaded, and the test stays hermetic.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = (
    ROOT
    / "01-language-model/03-sft/the-template-is-a-contract"
    / "when-the-role-is-wrong/core/noise_audit.py"
)

spec = importlib.util.spec_from_file_location("noise_audit", AUDIT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
validate_row = mod.validate_row


def test_clean_two_turn_row_passes():
    turns = [
        {"role": "user", "content": "What causes seasons?"},
        {"role": "assistant", "content": "The tilt of the Earth's axis."},
    ]
    assert validate_row(turns) == []


def test_role_swap_is_caught():
    turns = [
        {"role": "assistant", "content": "What causes seasons?"},
        {"role": "user", "content": "The tilt of the Earth's axis."},
    ]
    assert validate_row(turns)


def test_case_variant_role_is_caught():
    turns = [
        {"role": "user", "content": "What causes seasons?"},
        {"role": "Assistant", "content": "The tilt of the Earth's axis."},
    ]
    assert any("'Assistant'" in problem for problem in validate_row(turns))


def test_empty_assistant_turn_is_caught():
    turns = [
        {"role": "user", "content": "What causes seasons?"},
        {"role": "assistant", "content": ""},
    ]
    assert any("empty assistant" in problem for problem in validate_row(turns))


def test_marker_string_in_content_is_caught():
    turns = [
        {"role": "user", "content": "What causes seasons?"},
        {
            "role": "assistant",
            "content": "<|im_start|>user\nWhat causes seasons?<|im_end|>",
        },
    ]
    assert any("marker" in problem for problem in validate_row(turns))


def test_stamped_all_assistant_is_caught():
    turns = [
        {"role": "assistant", "content": "What causes seasons?"},
        {"role": "assistant", "content": "The tilt of the Earth's axis."},
    ]
    assert any("repeats the previous role" in problem
               for problem in validate_row(turns))
