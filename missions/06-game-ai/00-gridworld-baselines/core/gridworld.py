"""A tiny, deterministic, fully-observed grid-world: the verifiable-reward
environment mission 06's GRPO stage will train a policy against.

Chosen over CartPole (mission.yaml's other named option) for one concrete
reason: CartPole's physics is continuous and chaotic, so a policy that must
commit to its full action sequence in one text completion (see stage 01,
which reuses mission 01's `rollout_group` unmodified -- it samples one
completion per rollout, with no mid-episode observation fed back in) cannot
control it open-loop; any small drift compounds with no chance to correct.
A grid with deterministic transitions has no such problem: the full board is
in the prompt, so an open-loop plan is not a handicap, it is sufficient --
the same reason a shortest-path solver doesn't need to re-observe the grid
after every step either.

Board: fixed-size square grid, one start cell, one goal cell, some
impassable wall cells. An agent already at the grid edge or facing a wall
that attempts an illegal move simply stays where it is -- not a crash, not a
truncated episode, since a real policy (or a real player) will emit some
illegal moves and the environment needs a defined answer for that.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

ACTIONS = "UDLR"  # up, down, left, right
_DELTA = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


@dataclass(frozen=True)
class Grid:
    size: int
    walls: frozenset[tuple[int, int]]
    start: tuple[int, int]
    goal: tuple[int, int]

    def in_bounds(self, pos: tuple[int, int]) -> bool:
        r, c = pos
        return 0 <= r < self.size and 0 <= c < self.size

    def is_wall(self, pos: tuple[int, int]) -> bool:
        return pos in self.walls

    def step(self, pos: tuple[int, int], action: str) -> tuple[int, int]:
        """One move. An illegal destination (off-grid or a wall) leaves the
        agent in place -- the environment's own rule for an invalid action,
        not an error the caller has to guard against."""
        dr, dc = _DELTA[action]
        new_pos = (pos[0] + dr, pos[1] + dc)
        if not self.in_bounds(new_pos) or self.is_wall(new_pos):
            return pos
        return new_pos

    def run_episode(self, actions: str, max_steps: int) -> tuple[bool, int]:
        """Replay a full action string against this grid from `start`.
        Returns (reached_goal, steps_taken) -- steps_taken is capped at
        max_steps or the string length, whichever is shorter, and stops
        early the instant the goal is reached."""
        pos = self.start
        limit = min(max_steps, len(actions))
        for i in range(limit):
            pos = self.step(pos, actions[i])
            if pos == self.goal:
                return True, i + 1
        return pos == self.goal, limit

    def render_text(self) -> str:
        """A plain-text board a policy (or a person) can read directly:
        `.` open, `#` wall, `S` start, `G` goal."""
        rows = []
        for r in range(self.size):
            row_chars = []
            for c in range(self.size):
                pos = (r, c)
                if pos == self.start:
                    row_chars.append("S")
                elif pos == self.goal:
                    row_chars.append("G")
                elif pos in self.walls:
                    row_chars.append("#")
                else:
                    row_chars.append(".")
            rows.append("".join(row_chars))
        return "\n".join(rows)


def _reachable(grid_size: int, walls: frozenset, start: tuple[int, int], goal: tuple[int, int]) -> bool:
    """BFS reachability check -- a randomly placed wall set can trivially
    seal the goal off entirely, and a task set with unsolvable instances
    would silently deflate every policy's success rate for a reason that has
    nothing to do with policy quality."""
    seen = {start}
    queue = deque([start])
    while queue:
        pos = queue.popleft()
        if pos == goal:
            return True
        for action in ACTIONS:
            dr, dc = _DELTA[action]
            nxt = (pos[0] + dr, pos[1] + dc)
            if (
                0 <= nxt[0] < grid_size
                and 0 <= nxt[1] < grid_size
                and nxt not in walls
                and nxt not in seen
            ):
                seen.add(nxt)
                queue.append(nxt)
    return False


def sample_grid(rng: random.Random, size: int = 5, num_walls: int = 4) -> Grid:
    """Sample a random solvable grid: distinct start/goal, `num_walls` wall
    cells placed uniformly at random among the remaining cells, rejected and
    resampled (not merely reported) if the resulting board seals the goal
    off -- an unsolvable instance is a bug in the sampler, not a hard
    instance of the task."""
    while True:
        cells = [(r, c) for r in range(size) for c in range(size)]
        start, goal = rng.sample(cells, 2)
        remaining = [c for c in cells if c not in (start, goal)]
        walls = frozenset(rng.sample(remaining, min(num_walls, len(remaining))))
        if _reachable(size, walls, start, goal):
            return Grid(size=size, walls=walls, start=start, goal=goal)


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
