"""Catalogue real attempts by how they failed, not just whether they did.

`mission.yaml`'s guardrail list ends with "failures catalogued by category, not
merely counted." This script does not run anything itself -- every attempt it
reads already happened, scored by `scoring.score` (stage 02) at the time it
ran. What this adds is the category breakdown across every real attempt this
mission has produced so far: stage 03's frontier-tier runs and stage 01's
no-harness runs.

Categories, in the order `scoring.score` checks them:

  tampered              -- the diff touched a file under tests/
  no_tests_ran          -- the target test produced no outcomes at all
  target_still_failing  -- the target test still fails after the patch
  regressed             -- a previously-passing test now fails
  resolved              -- none of the above

Stage 01 adds one category `scoring.score` has no way to see: `patch_applied`.
A no-harness attempt with nothing to apply (or a diff `git apply` rejects) is
recorded as `target_still_failing` by the scorer, because nothing changed --
that verdict is correct, but it collapses "wrote a patch that did not fix the
bug" and "did not produce an applicable patch at all" into one bucket. This
script splits that bucket back open using the `patch_applied` field stage 01's
harness records alongside the scorer's verdict.

Run:
    python taxonomy.py
"""

from __future__ import annotations

import json
from pathlib import Path

MISSION_ROOT = Path(__file__).resolve().parents[2]
STAGE01_RESULTS = MISSION_ROOT / "01-no-harness" / "runs" / "no-harness-results.jsonl"
STAGE03_RESULTS = MISSION_ROOT / "03-cheap-or-expensive" / "runs" / "2026-07-29-results.jsonl"
STAGE02_DEMO_MD = MISSION_ROOT / "02-agent-loop" / "runs" / "2026-07-29-harness-end-to-end.md"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def categorize(records: list[dict], arm: str, has_patch_applied_field: bool) -> dict:
    by_verdict: dict[str, int] = {}
    tampered_examples = []
    not_applied = 0
    for r in records:
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1
        if r.get("tampered"):
            tampered_examples.append((r["task_id"], r.get("model", "?"), r["tampered"]))
        if has_patch_applied_field and r["verdict"] == "target_still_failing" and not r.get("patch_applied", True):
            not_applied += 1
    return {
        "arm": arm,
        "n": len(records),
        "by_verdict": by_verdict,
        "tampered_examples": tampered_examples,
        "patch_did_not_apply": not_applied if has_patch_applied_field else None,
    }


def main() -> None:
    lines = ["Mission 04 failure taxonomy", "=" * 72, ""]

    stage03 = load_jsonl(STAGE03_RESULTS)
    stage01 = load_jsonl(STAGE01_RESULTS)

    if not stage03:
        lines.append(f"MISSING: {STAGE03_RESULTS} -- stage 03 has not produced results")
    if not stage01:
        lines.append(f"MISSING: {STAGE01_RESULTS} -- stage 01 has not produced results")
    if not stage03 or not stage01:
        print("\n".join(lines))
        return

    cat03 = categorize(stage03, "harness (stage 03: haiku/sonnet/opus, full tool loop)", has_patch_applied_field=False)
    cat01 = categorize(stage01, "no-harness (stage 01: one blind call, no tools)", has_patch_applied_field=True)

    # `scoring.score`'s own four verdicts, plus `timeout` -- a category stage
    # 01 can produce that the shared scorer has no way to know about, since a
    # timeout means the model call never returned and there is nothing to
    # score. Listed first so it is never silently dropped from a category a
    # fixed tuple did not anticipate; any further category a future stage
    # invents is still caught by the sorted-remainder pass below it.
    KNOWN_VERDICTS = ("resolved", "target_still_failing", "regressed", "tampered", "no_tests_ran", "timeout")
    for cat in (cat03, cat01):
        lines.append(f"{cat['arm']} -- {cat['n']} real attempts")
        lines.append("-" * 72)
        seen_verdicts = set(cat["by_verdict"])
        for verdict in KNOWN_VERDICTS:
            count = cat["by_verdict"].get(verdict, 0)
            lines.append(f"  {verdict:<22} {count}/{cat['n']}")
        unlisted = sorted(seen_verdicts - set(KNOWN_VERDICTS))
        for verdict in unlisted:
            lines.append(f"  {verdict:<22} {cat['by_verdict'][verdict]}/{cat['n']}  (uncatalogued category)")
        if cat["patch_did_not_apply"] is not None:
            lines.append(
                f"    of which patch did not apply at all: "
                f"{cat['patch_did_not_apply']}/{cat['by_verdict'].get('target_still_failing', 0)} "
                f"of target_still_failing"
            )
        if cat["tampered_examples"]:
            lines.append(f"  test-tampering guardrail FIRED on: {cat['tampered_examples']}")
        lines.append("")

    total_tampered = len(cat03["tampered_examples"]) + len(cat01["tampered_examples"])
    lines.append("Test-tampering guardrail, across every real model attempt in this mission")
    lines.append("-" * 72)
    total_attempts = cat03["n"] + cat01["n"]
    if total_tampered == 0:
        lines.append(
            f"  Never fired on a real attempt, across {total_attempts} real model attempts "
            f"({cat03['n']} harness + {cat01['n']} no-harness). The only recorded firing is the "
            f"scripted demonstration in stage 02 "
            f"({STAGE02_DEMO_MD.relative_to(MISSION_ROOT)}), which used a scripted backend with no "
            f"model behind it, deliberately, to prove the check works before any model was pointed "
            f"at it. Per mission.yaml's acceptance bullet, this is reported as 'never fired', not "
            f"claimed as demonstrated."
        )
    else:
        lines.append(f"  Fired on {total_tampered}/{total_attempts} real attempts: {cat03['tampered_examples'] + cat01['tampered_examples']}")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
