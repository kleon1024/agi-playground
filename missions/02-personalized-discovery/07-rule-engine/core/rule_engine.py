"""A declarative rule engine: rules are data, not branches in the serving path.

Stage 05 turned a prediction vector into a scalar; stage 06 (not yet built)
will turn a ranked set of scalars into a slate. Neither stage can answer "why
was this item shown to this user" in a form a regulator, a lawyer, or a
partner can act on, because the honest answer from a learned ranker is "the
weights said so" -- true, and useless to someone who needs to change the
outcome without retraining a model. This file is the layer that exists for
that one job: some decisions have an external owner -- legal, policy, a
contract -- who must be able to read the decision, change it, and be held to
it. That ownership test, not accuracy, is what routes a decision here instead
of into a model.

Rules below are literal data (`DEFAULT_RULES`), evaluated by one small
interpreter (`matches`, `apply_rules`). Adding a rule means appending a
record, not writing an `if` in the serving path -- that is the entire
difference between a declarative constraint layer and if-statements
scattered through the code, and it is also what makes an audit possible:
every rule that could have fired is enumerable without reading the code that
runs them.

Three things this file insists on:

**A decision record, not a filtered list.** `apply_rules` returns a
`Decision` per item -- kept, removed, or capped, and which rule gets credited
with the human-readable reason -- not just a shorter list. A shorter list
answers "what happened"; a decision record answers "why," which is the only
question stage 05's opening scenario actually asked.

**Explicit precedence.** Blocks are evaluated before boosts, and a fired
block is terminal regardless of any boost that also matches -- an editorial
boost cannot rescue a legally blocked item, because a block encodes a
constraint an external owner imposed and a boost encodes a preference this
system expressed. Kind ordering (block > boost > cap) is a stronger rule
than any individual rule's priority number, and it is stated here rather than
left as an accident of list order. Caps run last of all, in score order,
because "has this creator already used its quota" is only a well-defined
question once the keep order is fixed.

**Detecting the empty set.** Two rules can each be reasonable in isolation
and still intersect to nothing -- `demo_empty_set` below constructs exactly
this by hand, not by unlucky sampling, so it reproduces every time it runs.
An engine that returns an empty slate the same way it returns any other
slate has hidden the one failure a policy conversation most needs to see.

This module is standard library only. `prod/cel_policy.py` does the same job
with CEL (Google's Common Expression Language, used for exactly this kind of
per-request policy decision in Kubernetes admission control and Firebase
security rules), reading its conditions from a policy file instead of a
Python list.

Run:  python rule_engine.py
      python rule_engine.py --region EU
      python rule_engine.py --cap 1
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from typing import Any

Condition = tuple[str, str, Any]  # (field, operator, value) -- every rule's predicate is this one shape


@dataclass(frozen=True)
class Item:
    item_id: str
    creator_id: str
    licensed_regions: frozenset[str]
    safety_flag: bool
    is_editorial_partner: bool
    score: float


@dataclass(frozen=True)
class Rule:
    rule_id: str
    kind: str  # "block" | "boost" | "cap"
    priority: int  # breaks ties within a kind; does NOT override kind ordering
    condition: Condition | None  # None only for a cap -- its predicate is cross-item state, see below
    param: float
    reason: str  # a template, filled with the request context or the rule's own param


def matches(item: Item, condition: Condition, context: dict) -> bool:
    """The entire interpreter for a per-item condition. Three operators is
    enough to express every rule below; a real deployment would extend this
    list, not add a special case elsewhere -- that discipline is what keeps
    the rule set legible as it grows.
    """
    field_name, op, value = condition
    actual = getattr(item, field_name)
    if isinstance(value, str) and value.startswith("$"):
        value = context[value[1:]]
    if op == "excludes":
        return value not in actual
    if op == "eq":
        return actual == value
    raise ValueError(f"unknown operator {op!r}")


DEFAULT_RULES: list[Rule] = [
    Rule(
        "regional_block", "block", priority=0,
        condition=("licensed_regions", "excludes", "$region"),
        param=0.0, reason="not licensed in {region}",
    ),
    Rule(
        "safety_block", "block", priority=1,
        condition=("safety_flag", "eq", True),
        param=0.0, reason="flagged unsafe for this surface",
    ),
    Rule(
        "editorial_boost", "boost", priority=10,
        condition=("is_editorial_partner", "eq", True),
        param=0.08, reason="editorial partner boost (+{param:.2f})",
    ),
    # A cap has no per-item condition: "has this creator already used its
    # quota" is a question about the other items already kept, not about
    # this item alone, so it cannot be expressed in the same (field, op,
    # value) shape every other rule uses. Declarative policy languages
    # (CEL, Rego) hit the same wall -- see prod/README for where that
    # boundary is actually drawn in a real deployment.
    Rule("per_creator_cap", "cap", priority=20, condition=None, param=2, reason="creator cap of {param:.0f} reached"),
]


@dataclass
class Decision:
    item_id: str
    entering_score: float
    final_score: float | None  # None once removed -- there is no score for an item not being ranked
    status: str  # "kept" | "removed" | "capped"
    fired: list[str]
    explanation: str


def apply_rules(items: list[Item], rules: list[Rule], context: dict) -> tuple[list[Decision], dict[str, int]]:
    """Evaluate every rule against every item and return one Decision per
    item plus a recall-cost table: how many candidates each block/cap rule
    removed. Order of operations is the precedence policy stated in the
    module docstring, made concrete: blocks first (terminal), then boosts
    (additive, can stack), then caps (order-dependent, run last).
    """
    blocks = sorted((r for r in rules if r.kind == "block"), key=lambda r: r.priority)
    boosts = sorted((r for r in rules if r.kind == "boost"), key=lambda r: r.priority)
    caps = [r for r in rules if r.kind == "cap"]

    decisions: dict[str, Decision] = {}
    removed_by: dict[str, int] = {r.rule_id: 0 for r in blocks + caps}
    survivors: list[tuple[Item, float, list[str]]] = []

    for item in items:
        fired_blocks = [r for r in blocks if matches(item, r.condition, context)]
        if fired_blocks:
            # Multiple blocks can legitimately fire on the same item (a
            # region-locked item can also be safety-flagged); the lowest
            # priority number is credited as the reason a human reads, but
            # every rule that matched is kept in `fired` so an audit sees
            # the overlap instead of only the first cause.
            authoritative = fired_blocks[0]
            removed_by[authoritative.rule_id] += 1
            decisions[item.item_id] = Decision(
                item_id=item.item_id, entering_score=item.score, final_score=None, status="removed",
                fired=[r.rule_id for r in fired_blocks],
                explanation=authoritative.reason.format(**context),
            )
            continue

        score = item.score
        fired_boosts = []
        for r in boosts:
            if matches(item, r.condition, context):
                score += r.param  # boosts stack -- unlike blocks, there is no reason a boost should veto another
                fired_boosts.append(r.rule_id)
        survivors.append((item, score, fired_boosts))

    survivors.sort(key=lambda triple: -triple[1])
    kept_per_creator: dict[str, int] = {}
    for item, score, fired_boosts in survivors:
        cap_hit = next((c for c in caps if kept_per_creator.get(item.creator_id, 0) >= c.param), None)
        if cap_hit is not None:
            removed_by[cap_hit.rule_id] += 1
            decisions[item.item_id] = Decision(
                item_id=item.item_id, entering_score=item.score, final_score=None, status="capped",
                fired=[*fired_boosts, cap_hit.rule_id],
                explanation=cap_hit.reason.format(param=cap_hit.param),
            )
            continue
        kept_per_creator[item.creator_id] = kept_per_creator.get(item.creator_id, 0) + 1
        boost_text = "; boosted by " + ", ".join(fired_boosts) if fired_boosts else "; no rule fired"
        decisions[item.item_id] = Decision(
            item_id=item.item_id, entering_score=item.score, final_score=score, status="kept",
            fired=fired_boosts, explanation="kept" + boost_text,
        )

    ordered = [decisions[it.item_id] for it in items]
    return ordered, removed_by


def detect_empty_set(items: list[Item], rules: list[Rule], context: dict) -> dict[str, Any] | None:
    """If the full rule set leaves nothing, report which block/cap rules
    would remove what on their own, so the emptiness has a legible cause
    instead of being reported as just a number. This is what an engine that
    "detects and reports" the empty-candidate case actually has to compute:
    the joint result plus each contributing rule's solo effect.
    """
    decisions, recall_cost = apply_rules(items, rules, context)
    if any(d.status == "kept" for d in decisions):
        return None
    solo_removed = {}
    for r in (r for r in rules if r.kind in ("block", "cap")):
        solo_decisions, _ = apply_rules(items, [r], context)
        solo_removed[r.rule_id] = sum(1 for d in solo_decisions if d.status != "kept")
    return {"total": len(items), "solo_removed": solo_removed, "joint_recall_cost": recall_cost}


def build_items() -> list[Item]:
    """Sixteen items, constructed by hand rather than sampled, so the
    empty-set demonstration below reproduces on every run instead of
    depending on a lucky or unlucky draw.

    Ten items are licensed only in the EU and every one of them also carries
    the safety flag -- standing in for a content category held back in one
    region pending a compliance review. Six items are licensed only in the
    US, none of them flagged, split evenly across three creators so each
    creator sits exactly at a cap of two.
    """
    items = []
    eu_creators = ["c1", "c1", "c2", "c2", "c3", "c3", "c4", "c4", "c5", "c5"]
    for i, creator in enumerate(eu_creators):
        items.append(
            Item(f"eu_{i}", creator, frozenset({"EU"}), safety_flag=True, is_editorial_partner=(i == 0),
                 score=round(0.50 + 0.03 * i, 3))
        )
    us_creators = ["c1", "c1", "c2", "c2", "c3", "c3"]
    for i, creator in enumerate(us_creators):
        items.append(
            Item(f"us_{i}", creator, frozenset({"US"}), safety_flag=False, is_editorial_partner=(i == 0),
                 score=round(0.60 + 0.02 * i, 3))
        )
    return items


def print_decisions(decisions: list[Decision], recall_cost: dict[str, int], total: int) -> None:
    for d in decisions:
        tail = f"score {d.final_score:.3f}" if d.final_score is not None else "no score -- not ranked"
        print(f"  {d.item_id:8s} {d.status:7s} {tail:24s} {d.explanation}")
    print("  recall cost (candidates removed, of the requested-region survivors and overall):")
    for rule_id, count in recall_cost.items():
        print(f"    {rule_id:18s} removed {count:2d} / {total} ({count / total:.0%})")


def run_demo(region: str, cap: int) -> None:
    items = build_items()
    context = {"region": region}

    print(f"decision record, region={region!r}, per_creator_cap={cap}")
    rules = [replace(r, param=cap) if r.rule_id == "per_creator_cap" else r for r in DEFAULT_RULES]
    decisions, recall_cost = apply_rules(items, rules, context)
    print_decisions(decisions, recall_cost, len(items))

    print("\ntighten the cap, region=US: cap=2 (default) vs cap=1, same items, same request")
    for cap_value in (2, 1):
        tightened = [replace(r, param=cap_value) if r.rule_id == "per_creator_cap" else r for r in DEFAULT_RULES]
        d2, r2 = apply_rules(items, tightened, {"region": "US"})
        kept = sum(1 for d in d2 if d.status == "kept")
        print(f"  cap={cap_value}: {kept} kept, per_creator_cap removed {r2['per_creator_cap']} -- "
              f"the reader's edit changed the explanation for a specific item, not just a count:")
        moved = next(d for d in d2 if d.status == "capped") if cap_value == 1 else None
        if moved is not None:
            print(f"    {moved.item_id}: {moved.explanation}")

    print("\ntwo individually reasonable rules, one region that empties jointly: region=EU")
    report = detect_empty_set(items, DEFAULT_RULES, {"region": "EU"})
    if report is None:
        print("  did not empty -- unexpected, check build_items()")
    else:
        print(f"  requested region emptied the candidate set ({report['total']} candidates in)")
        print("  each rule's effect alone, on the full candidate set:")
        for rule_id, count in report["solo_removed"].items():
            print(f"    {rule_id:18s} alone removes {count:2d} / {report['total']}"
                  f" ({count / report['total']:.0%}) -- not empty by itself")
        print("  applied together, in this request's context, they remove all of it:")
        for rule_id, count in report["joint_recall_cost"].items():
            if count:
                print(f"    {rule_id:18s} contributed {count} of the joint removal")
        print("  reported, not silently returned as an empty slate.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=["US", "EU"], default="US")
    parser.add_argument("--cap", type=int, default=2, help="per-creator cap for the first, region-only demo")
    args = parser.parse_args()
    run_demo(args.region, args.cap)


if __name__ == "__main__":
    main()
