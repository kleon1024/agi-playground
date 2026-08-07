"""The two baselines mission 06's `mission.yaml` requires, measured against
the same grid-world environment stage 01's GRPO policy will be trained on
and scored on. Both baselines act open-loop, exactly like the trained policy
will -- they commit to a full action string before seeing whether any move
succeeded, so the comparison isolates policy quality, not who gets to see
more of the episode.
"""

from __future__ import annotations

import random

from gridworld import ACTIONS, Grid, manhattan


def random_policy(rng: random.Random, max_steps: int) -> str:
    """Uniform-random legal-alphabet action string -- the floor. "Legal
    alphabet" means only U/D/L/R are ever emitted; whether a given move is
    legal *on this board* (in-bounds, not a wall) is for the environment's
    own `step` to decide, the same as it would for any other policy."""
    return "".join(rng.choice(ACTIONS) for _ in range(max_steps))


def greedy_policy(grid: Grid, max_steps: int) -> str:
    """One-step lookahead: from the current (simulated) position, take
    whichever of the 4 actions reduces Manhattan distance to the goal the
    most, breaking ties by a fixed action order. This is a real heuristic
    with a real, discoverable failure mode -- it has no memory of visited
    cells, so a wall configuration that requires temporarily moving *away*
    from the goal to route around an obstacle traps it in a back-and-forth
    loop for the rest of the budget. That failure mode is the reason this
    baseline is beatable, not a bug to fix; mission.yaml asks for exactly
    this kind of baseline, not a shortest-path solver.
    """
    pos = grid.start
    actions = []
    for _ in range(max_steps):
        if pos == grid.goal:
            break
        best_action = ACTIONS[0]
        best_dist = None
        for action in ACTIONS:
            candidate = grid.step(pos, action)
            dist = manhattan(candidate, grid.goal)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_action = action
        actions.append(best_action)
        pos = grid.step(pos, best_action)
    # Pad to max_steps so run_episode's length handling matches every other
    # policy's output shape; the padding actions are never reached because
    # run_episode stops the instant the goal is hit.
    while len(actions) < max_steps:
        actions.append(ACTIONS[0])
    return "".join(actions)
