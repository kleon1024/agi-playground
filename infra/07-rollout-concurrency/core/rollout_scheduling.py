"""RL rollout concurrency: why variable-length trajectories break lockstep
batching, and what asynchronous collection buys back.

`infra/03-orchestration/core/scheduler.py` measures scheduling for jobs of
*fixed*, known cost -- priority order reassigns wait time, but total makespan
barely moves. RL rollout generation breaks that assumption: trajectory length
is heavy-tailed (most episodes end quickly; a long tail run much longer), so a
scheduler that waits for a whole batch before starting the next one is at the
mercy of whichever trajectory in the batch happens to run longest. This
script measures that gap directly, with real CPU-bound work (a real matmul
loop per trajectory step, timed with time.perf_counter) under two policies:

- synchronous / lockstep -- submit exactly W trajectories at a time, wait for
  ALL W to finish, then submit the next W. Mirrors a training loop that waits
  for a full rollout batch before the update step can run.
- asynchronous / continuous -- a fixed pool of W workers pulls the next
  trajectory the moment it finishes its current one, same total set of
  trajectories, no batch boundary. Mirrors the decoupled generation/training
  pattern in Noukhovitch et al., "Asynchronous RLHF" (2024) and AReaL (2025).

Same trajectory-length list feeds both policies in every trial, so any
measured difference is the scheduling policy, not a different random draw.

Run:  python rollout_scheduling.py --workers 4,8 --trials 3 --out ../runs
"""

from __future__ import annotations

import argparse
import json
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_MATMUL_SIZE = 200


@dataclass
class Trajectory:
    traj_id: int
    reps: int  # stand-in for episode length: more reps = more decode steps
    start_time: float | None = field(default=None)
    end_time: float | None = field(default=None)


def do_step(matmul_size: int, reps: int) -> None:
    """Real CPU-bound work standing in for `reps` decode steps of one
    trajectory. NumPy's BLAS call releases the GIL during the matmul itself,
    so real concurrent compute happens across threads, matching
    infra/03-orchestration's own approach."""
    a = np.random.rand(matmul_size, matmul_size)
    b = np.random.rand(matmul_size, matmul_size)
    for _ in range(reps):
        a @ b


def make_trajectories(n: int, seed: int) -> list[Trajectory]:
    """Heavy-tailed episode-length distribution: 80% short (2-4 reps,
    matching most RL episodes ending quickly), 20% long tail (20-40 reps,
    matching the rare episode that runs much longer before terminating).
    This shape -- not a symmetric or uniform one -- is what makes the
    straggler problem real: a handful of long trajectories, not the average
    trajectory, decide how long a lockstep batch waits."""
    rng = random.Random(seed)
    trajs = []
    for i in range(n):
        if rng.random() < 0.8:
            reps = rng.randint(2, 4)
        else:
            reps = rng.randint(20, 40)
        trajs.append(Trajectory(traj_id=i, reps=reps))
    return trajs


def run_lockstep(trajs: list[Trajectory], n_workers: int) -> list[Trajectory]:
    """Submit exactly n_workers trajectories at a time; wait for the whole
    batch to finish before submitting the next batch. A worker that finishes
    early sits idle until every other worker in its batch also finishes."""
    t0 = time.perf_counter()
    pending = list(trajs)
    completed: list[Trajectory] = []
    while pending:
        batch = pending[:n_workers]
        pending = pending[n_workers:]
        threads = []
        for traj in batch:
            traj.start_time = time.perf_counter() - t0

            def target(tr: Trajectory = traj) -> None:
                do_step(_MATMUL_SIZE, tr.reps)
                tr.end_time = time.perf_counter() - t0

            th = threading.Thread(target=target)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        completed.extend(batch)
    return completed


def run_async(trajs: list[Trajectory], n_workers: int) -> list[Trajectory]:
    """A fixed pool of n_workers workers. Each worker pulls the next pending
    trajectory the instant it finishes its current one -- no batch boundary,
    no waiting on siblings. Implemented as a shared work queue with one
    persistent thread per worker slot, so worker count matches the lockstep
    policy exactly."""
    t0 = time.perf_counter()
    lock = threading.Lock()
    queue = list(trajs)
    completed: list[Trajectory] = []

    def worker() -> None:
        while True:
            with lock:
                if not queue:
                    return
                traj = queue.pop(0)
                traj.start_time = time.perf_counter() - t0
            do_step(_MATMUL_SIZE, traj.reps)
            traj.end_time = time.perf_counter() - t0
            with lock:
                completed.append(traj)

    threads = [threading.Thread(target=worker) for _ in range(n_workers)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    return completed


def summarize(completed: list[Trajectory], n_workers: int) -> dict:
    makespan = max(t.end_time for t in completed)
    return {
        "n_workers": n_workers,
        "n_trajectories": len(completed),
        "makespan_s": makespan,
        "throughput_traj_per_s": len(completed) / makespan,
    }


def warmup() -> None:
    """Throwaway matmul work to warm BLAS thread pools and page caches before
    any timed trial -- matching infra/03-orchestration's own warmup, for the
    same reason: whichever policy runs first in an untuned comparison absorbs
    a one-time cold-start cost that has nothing to do with scheduling."""
    do_step(_MATMUL_SIZE, 4)
    do_step(_MATMUL_SIZE, 4)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=str, default="4,8")
    parser.add_argument("--n-trajectories", type=int, default=40)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=Path("runs"))
    args = parser.parse_args()

    warmup()

    worker_counts = [int(w) for w in args.workers.split(",")]
    results: dict[str, dict] = {}

    for n_workers in worker_counts:
        trials: dict[str, list[dict]] = {"lockstep": [], "async": []}
        order = ["lockstep", "async"]
        for t in range(args.trials):
            policies = order if t % 2 == 0 else list(reversed(order))
            for policy in policies:
                trajs = make_trajectories(args.n_trajectories, seed=args.seed + t)
                if policy == "lockstep":
                    completed = run_lockstep(trajs, n_workers)
                else:
                    completed = run_async(trajs, n_workers)
                trials[policy].append(summarize(completed, n_workers))

        def stats(values: list[float]) -> dict:
            return {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }

        key = f"workers_{n_workers}"
        results[key] = {}
        for policy in ("lockstep", "async"):
            makespans = [r["makespan_s"] for r in trials[policy]]
            throughputs = [r["throughput_traj_per_s"] for r in trials[policy]]
            results[key][policy] = {
                "trials": trials[policy],
                "makespan_s": stats(makespans),
                "throughput_traj_per_s": stats(throughputs),
            }
        lockstep_mean = results[key]["lockstep"]["makespan_s"]["mean"]
        async_mean = results[key]["async"]["makespan_s"]["mean"]
        speedup = lockstep_mean / async_mean
        results[key]["async_speedup_x"] = speedup
        print(f"\n=== workers={n_workers} trajectories={args.n_trajectories} trials={args.trials} ===")
        print(f"lockstep makespan: {results[key]['lockstep']['makespan_s']}")
        print(f"async makespan:    {results[key]['async']['makespan_s']}")
        print(f"async speedup: {speedup:.2f}x")

    args.out.mkdir(parents=True, exist_ok=True)
    out_file = args.out / "rollout-scheduling-result.json"
    out_file.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {out_file}")


if __name__ == "__main__":
    main()
