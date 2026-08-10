"""A 2-D synthetic driving simulator: lane following plus obstacle
avoidance, observed through a low-resolution bird's-eye render.

The world is deliberately minimal -- a sinusoidal lane center, a car with
discrete steering and throttle, and a few circular obstacles -- because the
claim under test is about the imitation-and-closed-loop method, not about
visual realism. A 32x32 render over a 8m x 8m patch ahead of the car is the
only observation the learned policies ever see; the expert sees the true
state.

Coordinate frame: x is along the road, y is lateral, road width is 4m
centered on a sinusoidal center line. One simulated step is dt = 0.1s.
An episode ends when the car passes the target x, drives off the road
(|lateral offset| > road half width), or collides with an obstacle.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

ROAD_HALF_WIDTH = 2.0
ROAD_Y0 = 4.0
DT = 0.1
MAX_SPEED = 6.0
STEER_RATE = 0.12  # rad per step per unit steer
ACCEL = 1.4  # m/s^2
BRAKE = 3.0  # m/s^2
TARGET_X = 60.0
MAX_STEPS = 400
COLLISION_DIST = 0.9

GRID = 32
PATCH = 8.0  # meters per side of the rendered patch
M_PER_PIX = PATCH / GRID


@dataclass
class Scenario:
    """One track: a lane-center sinusoid plus a set of obstacles."""

    seed: int
    amplitude: float
    wavelength: float
    obstacles: list[tuple[float, float, float, float]] = field(default_factory=list)
    # obstacle entries: (x, y, radius, vx) -- vx is meters/s along the road

    def lane_center(self, x: float) -> float:
        return ROAD_Y0 + self.amplitude * math.sin(x / self.wavelength)


def sample_scenario(seed: int, hard: bool = False) -> Scenario:
    """Procedurally generated track. `hard` raises the curvature amplitude
    and obstacle speed/density for stage 05's out-of-distribution split."""
    rng = random.Random(seed)
    amplitude = rng.uniform(0.3, 0.7) if not hard else rng.uniform(0.9, 1.4)
    wavelength = rng.uniform(14.0, 22.0) if not hard else rng.uniform(9.0, 13.0)
    n_obs = rng.randint(2, 4) if not hard else rng.randint(4, 6)
    obstacles = []
    for _ in range(n_obs):
        x = rng.uniform(8.0, TARGET_X - 4.0)
        # obstacle lane offset from road center
        off = rng.choice([-1.2, 0.0, 1.2])
        y = ROAD_Y0 + amplitude * math.sin(x / wavelength) + off
        r = rng.uniform(0.4, 0.55)
        vx = rng.uniform(0.0, 1.2) if not hard else rng.uniform(1.5, 3.0)
        obstacles.append((x, y, r, vx))
    return Scenario(seed=seed, amplitude=amplitude, wavelength=wavelength,
                    obstacles=obstacles)


@dataclass
class Car:
    x: float = 2.0
    y: float = ROAD_Y0
    theta: float = 0.0
    v: float = 0.0

    def step(self, steer: int, throttle: int) -> None:
        """steer in {-1, 0, 1}; throttle in {0, 1} (1 = accelerate, 0 = brake)."""
        self.theta += steer * STEER_RATE
        if throttle == 1:
            self.v = min(self.v + ACCEL * DT, MAX_SPEED)
        else:
            self.v = max(self.v - BRAKE * DT, 0.0)
        self.x += self.v * math.cos(self.theta) * DT
        self.y += self.v * math.sin(self.theta) * DT


def render(scenario: Scenario, car: Car) -> list[list[float]]:
    """Bird's-eye render of the patch ahead of the car, 32x32, ego heading up.

    Values: 0 off-road, 0.4 road edge, 0.8 road surface (darker farther from
    lane center), 1.5 lane-boundary line, 2.0 obstacle, 3.0 ego marker.
    """
    grid = [[0.0] * GRID for _ in range(GRID)]
    cos_t, sin_t = math.cos(car.theta), math.sin(car.theta)
    # world coords of the pixel at (row, col): row 0 is farthest ahead
    for row in range(GRID):
        ahead = PATCH * (1.0 - (row + 0.5) / GRID)  # 0 at ego, PATCH at top
        for col in range(GRID):
            lat = PATCH * ((col + 0.5) / GRID - 0.5)
            # rotate (ahead, lat) by heading into world frame
            wx = car.x + ahead * cos_t - lat * sin_t
            wy = car.y + ahead * sin_t + lat * cos_t
            yc = scenario.lane_center(wx)
            off = abs(wy - yc)
            if off > ROAD_HALF_WIDTH:
                continue
            if off > ROAD_HALF_WIDTH - 0.25:
                grid[row][col] = 1.5
            else:
                grid[row][col] = 0.8 - 0.4 * (off / ROAD_HALF_WIDTH)
    for ox, oy, r, _vx in scenario.obstacles:
        # project obstacle into ego frame
        dx, dy = ox - car.x, oy - car.y
        ahead = dx * cos_t + dy * sin_t
        lat = -dx * sin_t + dy * cos_t
        if ahead < -0.5 or ahead > PATCH + 0.5:
            continue
        row = int(GRID * (1.0 - ahead / PATCH))
        col = int(GRID * (lat / PATCH + 0.5))
        rad_px = max(1, int(r / M_PER_PIX))
        for dr in range(-rad_px, rad_px + 1):
            for dc in range(-rad_px, rad_px + 1):
                rr, cc = row + dr, col + dc
                if 0 <= rr < GRID and 0 <= cc < GRID:
                    grid[rr][cc] = max(grid[rr][cc], 2.0)
    return grid


@dataclass
class Outcome:
    completed: bool
    collided: bool
    offroad: bool
    steps: int
    x_reached: float
    min_clearance: float


def simulate(scenario: Scenario, policy, max_steps: int = MAX_STEPS) -> Outcome:
    """Run `policy(render, state) -> (steer, throttle)` until episode end."""
    car = Car()
    min_clearance = float("inf")
    for step in range(max_steps):
        obs = render(scenario, car)
        steer, throttle = policy(obs, car)
        car.step(steer, throttle)
        off = abs(car.y - scenario.lane_center(car.x))
        for ox, oy, r, _ in scenario.obstacles:
            d = math.hypot(car.x - ox, car.y - oy)
            min_clearance = min(min_clearance, d)
            if d < r + 0.35:
                return Outcome(False, True, False, step + 1, car.x, min_clearance)
        if off > ROAD_HALF_WIDTH:
            return Outcome(False, False, True, step + 1, car.x, min_clearance)
        if car.x >= TARGET_X:
            return Outcome(True, False, False, step + 1, car.x, min_clearance)
    return Outcome(False, False, False, max_steps, car.x, min_clearance)


def collect_demos(scenarios: list[Scenario], expert_policy,
                  max_steps: int = MAX_STEPS):
    """Roll out the expert on each scenario, recording (render, steer,
    throttle) at every step plus the outcome."""
    demos: list[tuple[list[list[float]], int, int]] = []
    outcomes = []
    for scenario in scenarios:
        car = Car()
        for _ in range(max_steps):
            obs = render(scenario, car)
            steer, throttle = expert_policy(obs, car)
            demos.append((obs, steer, throttle))
            car.step(steer, throttle)
            off = abs(car.y - scenario.lane_center(car.x))
            done = False
            for ox, oy, r, _ in scenario.obstacles:
                if math.hypot(car.x - ox, car.y - oy) < r + 0.35:
                    done = True
            if off > ROAD_HALF_WIDTH:
                done = True
            if car.x >= TARGET_X:
                done = True
            if done:
                break
        outcomes.append((car.x >= TARGET_X, car.x))
    return demos, outcomes

