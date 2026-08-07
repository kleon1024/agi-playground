"""The production lane for stage 07: the same block/boost/cap decision, with
conditions read from `policy.json` and evaluated by CEL (Google's Common
Expression Language) instead of the `(field, op, value)` tuples `core/`
interprets by hand.

CEL is not a curiosity pick. It is the same policy language Kubernetes
uses for admission control and Firebase uses for security rules, chosen for
exactly this shape of problem: evaluate a small boolean expression against
one request's worth of context, fast, in a sandbox that cannot do anything
other than return true or false. A second production-grade alternative for
this stage is Open Policy Agent (Rego), which trades CEL's request-scoped
simplicity for a fuller query language and its own evaluation service; a
third, lighter-weight alternative many product teams reach for first is a
feature-flag-plus-policy service (e.g. a rules-capable flagging platform)
that stores the same kind of condition/action pairs behind a UI instead of a
policy file. All three exist because the requirement is the same one stage
07's README opens with: a policy edit must ship without a model retrain, and
whoever owns the policy needs to be able to read it.

`policy.json` holds the same three per-item rules `core/rule_engine.py`
hard-codes as `DEFAULT_RULES`, expressed as CEL condition strings instead of
Python tuples -- the declarative form stage 07 argues for is not just "data
instead of code," it is data in a form a non-engineer reading the policy
file can plausibly audit.

**What does not move into CEL.** The per-creator cap needs "how many items
from this creator have I already kept in this ranking," which is state
across items, not a fact about one item. CEL (like Rego) evaluates one input
against one policy at a time and has no notion of that running count, so the
cap stays in this file's calling code -- the same place it lives in `core/`,
for the same reason. Naming this boundary here, rather than pretending a
policy language can express everything, is the point of including it.

Requires `cel-python`, not part of this repository's base dependency group:
    pip install cel-python

Run:  python cel_policy.py
      python cel_policy.py --region EU
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

import celpy
import rule_engine as core

POLICY_PATH = Path(__file__).resolve().parent / "policy.json"


@dataclass
class CompiledRule:
    rule_id: str
    kind: str
    priority: int
    param: float
    reason: str
    program: Any  # a compiled celpy program: one boolean CEL expression, ready to evaluate


def load_policy(path: Path) -> dict:
    return json.loads(path.read_text())


def compile_rules(policy: dict, env: celpy.Environment) -> list[CompiledRule]:
    compiled = []
    for r in policy["rules"]:
        program = env.program(env.compile(r["condition"]))
        compiled.append(CompiledRule(r["rule_id"], r["kind"], r["priority"], r.get("param", 0.0), r["reason"], program))
    return compiled


def activation_for(item: core.Item, region: str) -> dict:
    """CEL evaluates against a context, not a Python object -- the item is
    handed over as plain data, the same boundary a real policy service
    would sit behind (a request comes in as JSON, not as a dataclass).
    """
    return celpy.json_to_cel(
        {
            "item": {
                "licensed_regions": sorted(item.licensed_regions),
                "safety_flag": item.safety_flag,
                "is_editorial_partner": item.is_editorial_partner,
            },
            "region": region,
        }
    )


def apply_policy(
    items: list[core.Item], rules: list[CompiledRule], cap: int, region: str
) -> tuple[list[dict], dict[str, int]]:
    blocks = sorted((r for r in rules if r.kind == "block"), key=lambda r: r.priority)
    boosts = sorted((r for r in rules if r.kind == "boost"), key=lambda r: r.priority)

    decisions: dict[str, dict] = {}
    removed_by: dict[str, int] = {r.rule_id: 0 for r in blocks}
    removed_by["per_creator_cap"] = 0
    survivors: list[tuple[core.Item, float, list[str]]] = []

    for item in items:
        activation = activation_for(item, region)
        fired_blocks = [r for r in blocks if bool(r.program.evaluate(activation))]
        if fired_blocks:
            authoritative = fired_blocks[0]
            removed_by[authoritative.rule_id] += 1
            decisions[item.item_id] = {
                "status": "removed",
                "explanation": authoritative.reason.format(region=region),
            }
            continue

        score = item.score
        fired_boosts = []
        for r in boosts:
            if bool(r.program.evaluate(activation)):
                score += r.param
                fired_boosts.append(r.rule_id)
        survivors.append((item, score, fired_boosts))

    survivors.sort(key=lambda triple: -triple[1])
    kept_per_creator: dict[str, int] = {}
    for item, score, fired_boosts in survivors:
        count = kept_per_creator.get(item.creator_id, 0)
        if count >= cap:
            removed_by["per_creator_cap"] += 1
            decisions[item.item_id] = {"status": "capped", "explanation": f"creator cap of {cap} reached"}
            continue
        kept_per_creator[item.creator_id] = count + 1
        boost_text = "; boosted by " + ", ".join(fired_boosts) if fired_boosts else "; no rule fired"
        decisions[item.item_id] = {
            "status": "kept",
            "score": round(score, 3),
            "explanation": "kept" + boost_text,
        }

    ordered = [{"item_id": it.item_id, **decisions[it.item_id]} for it in items]
    return ordered, removed_by


def run(region: str, cap: int) -> None:
    policy = load_policy(POLICY_PATH)
    env = celpy.Environment()
    rules = compile_rules(policy, env)
    items = core.build_items()

    print(f"policy: {POLICY_PATH.name}, region={region!r}, per_creator_cap={cap}")
    decisions, recall_cost = apply_policy(items, rules, cap, region)
    for d in decisions:
        tail = f"score {d['score']:.3f}" if "score" in d else "no score -- not ranked"
        print(f"  {d['item_id']:8s} {d['status']:7s} {tail:24s} {d['explanation']}")
    print("  recall cost:")
    for rule_id, count in recall_cost.items():
        print(f"    {rule_id:18s} removed {count:2d} / {len(items)} ({count / len(items):.0%})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=["US", "EU"], default="US")
    parser.add_argument("--cap", type=int, default=None, help="overrides policy.json's per_creator_cap")
    args = parser.parse_args()
    policy = load_policy(POLICY_PATH)
    cap = args.cap if args.cap is not None else policy["per_creator_cap"]
    run(args.region, cap)


if __name__ == "__main__":
    main()
