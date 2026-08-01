"""A toy multi-job scheduler: same job batch, two dispatch policies.

Teaches one mechanism: when a fixed pool of workers ("GPU slots") is smaller
than the pending job batch, dispatch ORDER -- not total work -- decides who
waits. Every job here does real CPU-bound work (a real matmul loop, timed
with a real wall clock) so the wait-time numbers below are measured, not
simulated with time.sleep placeholders.

Run:  python scheduler.py --slots 2 --out ../runs
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Job:
    job_id: str
    priority: int  # 0 = high priority, 1 = low priority. Lower runs first.
    matmul_size: int
    reps: int
    arrival_index: int
    start_time: float | None = field(default=None)
    end_time: float | None = field(default=None)


def do_work(matmul_size: int, reps: int) -> None:
    """Real CPU-bound work standing in for a GPU job's compute."""
    a = np.random.rand(matmul_size, matmul_size)
    b = np.random.rand(matmul_size, matmul_size)
    for _ in range(reps):
        a @ b


def make_jobs() -> list[Job]:
    """10 jobs, high priority (0) interspersed with low priority (1), not
    front-loaded -- so a policy that ignores priority will make some high
    priority jobs wait behind several low priority ones."""
    priorities = [1, 1, 0, 1, 1, 0, 1, 0, 1, 1]
    jobs = []
    for i, p in enumerate(priorities):
        jobs.append(
            Job(
                job_id=f"job-{i:02d}",
                priority=p,
                matmul_size=350,
                reps=6,
                arrival_index=i,
            )
        )
    return jobs


def run_scheduler(jobs: list[Job], n_slots: int, policy: str) -> list[Job]:
    """Dispatch `jobs` onto `n_slots` worker threads.

    This assumes the whole batch is known upfront (batch scheduling) --
    a real simplification against a production scheduler like Slurm, which
    also handles jobs arriving continuously. `fifo` dispatches in arrival
    order; `priority` sorts the pending queue by priority once, up front,
    and always dispatches the highest-priority job still waiting. Neither
    policy preempts a job once it has started -- see "What this does not
    show" in the README.
    """
    if policy == "priority":
        pending = sorted(jobs, key=lambda j: (j.priority, j.arrival_index))
    elif policy == "fifo":
        pending = sorted(jobs, key=lambda j: j.arrival_index)
    else:
        raise ValueError(f"unknown policy: {policy}")

    running: list[tuple[threading.Thread, Job]] = []
    completed: list[Job] = []
    t0 = time.perf_counter()

    while pending or running:
        while len(running) < n_slots and pending:
            job = pending.pop(0)
            job.start_time = time.perf_counter() - t0
            th = threading.Thread(target=do_work, args=(job.matmul_size, job.reps))
            th.start()
            running.append((th, job))

        still_running = []
        for th, job in running:
            th.join(timeout=0.005)
            if th.is_alive():
                still_running.append((th, job))
            else:
                job.end_time = time.perf_counter() - t0
                completed.append(job)
        running = still_running
        if running:
            time.sleep(0.005)

    return completed


def summarize(completed: list[Job]) -> dict:
    by_priority: dict[int, list[float]] = {0: [], 1: []}
    for job in completed:
        wait = job.start_time  # jobs "arrive" at t=0, so start_time == wait time
        by_priority[job.priority].append(wait)
    makespan = max(job.end_time for job in completed)
    return {
        "makespan_s": makespan,
        "high_priority_mean_wait_s": (
            sum(by_priority[0]) / len(by_priority[0]) if by_priority[0] else None
        ),
        "low_priority_mean_wait_s": (
            sum(by_priority[1]) / len(by_priority[1]) if by_priority[1] else None
        ),
        "per_job": [
            {
                "job_id": j.job_id,
                "priority": j.priority,
                "arrival_index": j.arrival_index,
                "start_s": round(j.start_time, 4),
                "end_s": round(j.end_time, 4),
            }
            for j in sorted(completed, key=lambda j: j.start_time)
        ],
    }


def warmup() -> None:
    """Throwaway matmul work to warm up BLAS thread pools and page caches
    before any timed trial -- otherwise whichever policy runs first absorbs
    one-time cold-start cost that has nothing to do with scheduling, and the
    comparison is silently unfair."""
    do_work(350, 6)
    do_work(350, 6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slots", type=int, default=2)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--out", type=Path, default=Path("runs"))
    args = parser.parse_args()

    warmup()

    trials: dict[str, list[dict]] = {"fifo": [], "priority": []}
    # alternate policy order across trials so neither one systematically
    # runs first -- any remaining order effect then shows up as spread,
    # not as a fake difference between policies.
    order = ["fifo", "priority"]
    for t in range(args.trials):
        for policy in (order if t % 2 == 0 else list(reversed(order))):
            jobs = make_jobs()
            completed = run_scheduler(jobs, args.slots, policy)
            trials[policy].append(summarize(completed))

    def stats(values: list[float]) -> dict:
        return {
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    results = {}
    for policy in ("fifo", "priority"):
        makespans = [r["makespan_s"] for r in trials[policy]]
        hi_waits = [r["high_priority_mean_wait_s"] for r in trials[policy]]
        lo_waits = [r["low_priority_mean_wait_s"] for r in trials[policy]]
        results[policy] = {
            "trials": trials[policy],
            "makespan_s": stats(makespans),
            "high_priority_mean_wait_s": stats(hi_waits),
            "low_priority_mean_wait_s": stats(lo_waits),
        }
        print(f"\n=== policy={policy} slots={args.slots} trials={args.trials} ===")
        print(f"makespan: {results[policy]['makespan_s']}")
        print(f"high-priority mean wait: {results[policy]['high_priority_mean_wait_s']}")
        print(f"low-priority mean wait:  {results[policy]['low_priority_mean_wait_s']}")

    args.out.mkdir(parents=True, exist_ok=True)
    out_file = args.out / "scheduler-result.json"
    out_file.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {out_file}")


if __name__ == "__main__":
    main()
