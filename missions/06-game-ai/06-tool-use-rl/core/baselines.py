"""The two fixed baselines mission 06's contract requires for this stage: a
policy that always answers directly (never pays the tool's cost, absorbs
whatever `simulated_accuracy` gives it at whatever difficulty it is asked)
and one that always invokes the tool (always pays `TOOL_COST`, always gets
the question right). Neither reads the difficulty label in the prompt at
all -- that is exactly the room a policy that does read it has to do better
than both, on the same open-loop, one-decision-per-episode footing every
other baseline in this mission uses.
"""

from __future__ import annotations

from env_text import Problem


def never_tool_policy(problem: Problem) -> str:
    return "A"


def always_tool_policy(problem: Problem) -> str:
    return "T"
