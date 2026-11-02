"""
Baseline Scheduling Algorithms for R||C_max Comparison

Implements four standard baseline heuristics from the scheduling literature
for comparison against the combinatorial 2-approximation algorithm.

Baselines:
  1. Random Assignment    — each job picks a random feasible machine
  2. Greedy Least-Loaded  — assign each job to the least-loaded feasible machine
  3. Min-Min              — Ibarra & Kim (1977); assigns easiest job first
  4. Max-Min              — Ibarra & Kim (1977); assigns hardest job first

All baselines operate on the same n×m ToA matrix P and return
(assignment, makespan) for direct comparison.
"""

import heapq
import random
from typing import List, Tuple, Optional

from data_structures import INF


def _feasible_machines(P: List[List[int]], i: int, m: int, w: Optional[int] = None) -> List[int]:
    """Return list of feasible machine indices for job i."""
    if w is None:
        return [j for j in range(m) if P[i][j] < INF]
    return [j for j in range(m) if P[i][j] <= w and P[i][j] < INF]


def _compute_makespan(n: int, m: int, P: List[List[int]], alpha: List[int]) -> int:
    """Compute makespan (max machine load) from assignment."""
    loads = [0] * m
    for i in range(n):
        loads[alpha[i]] += P[i][alpha[i]]
    return max(loads) if loads else 0


# ──────────────────────────────────────────────────────────────────────
# Baseline 1: Random Assignment
# ──────────────────────────────────────────────────────────────────────

def random_assignment(
    n: int, m: int,
    P: List[List[int]],
    seed: int = 42,
) -> Tuple[Optional[List[int]], int]:
    """
    Baseline 1: Random Assignment.

    Each job is assigned uniformly at random to one of its feasible machines.
    Models uncoordinated LoRaWAN (Pure ALOHA) behavior.

    Reference: Standard baseline in LoRaWAN scheduling literature.

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    P : list[list[int]]
        n×m ToA matrix.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    (alpha, makespan) or (None, 0) if infeasible.
    """
    rng = random.Random(seed)
    alpha = []

    for i in range(n):
        feasible = _feasible_machines(P, i, m)
        if not feasible:
            return None, 0
        alpha.append(rng.choice(feasible))

    return alpha, _compute_makespan(n, m, P, alpha)


# ──────────────────────────────────────────────────────────────────────
# Baseline 2: Greedy Least-Loaded (List Scheduling)
# ──────────────────────────────────────────────────────────────────────

def greedy_least_loaded(
    n: int, m: int,
    P: List[List[int]],
) -> Tuple[Optional[List[int]], int]:
    """
    Baseline 2: Greedy Least-Loaded (List Scheduling).

    Processes jobs in arbitrary order. Each job is assigned to the feasible
    machine with the current lowest total load.

    Reference: Graham, R.L. "Bounds for certain multiprocessor anomalies",
               Bell System Technical Journal 45, 1966, pp. 1563-1581.

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    P : list[list[int]]
        n×m ToA matrix.

    Returns
    -------
    (alpha, makespan) or (None, 0) if infeasible.
    """
    loads = [0] * m
    alpha = []

    for i in range(n):
        feasible = _feasible_machines(P, i, m)
        if not feasible:
            return None, 0

        # Pick the feasible machine with the lowest current load
        best_j = min(feasible, key=lambda j: (loads[j] + P[i][j], P[i][j], j))
        alpha.append(best_j)
        loads[best_j] += P[i][best_j]

    return alpha, max(loads)


# ──────────────────────────────────────────────────────────────────────
# Baseline 3: Min-Min Heuristic
# ──────────────────────────────────────────────────────────────────────

def min_min(
    n: int, m: int,
    P: List[List[int]],
) -> Tuple[Optional[List[int]], int]:
    """
    Baseline 3: Min-Min Heuristic.

    Iteratively selects the unassigned job whose minimum completion time
    (across all machines) is the SMALLEST, and assigns it to that machine.
    Prioritizes easy/small jobs first.

    Reference: Ibarra, O.H. & Kim, C.E. "Heuristic algorithms for
               scheduling independent tasks on nonidentical processors",
               Journal of the ACM 24(2), 1977, pp. 280-289.

    Also widely cited in:
    - Braun et al. "A comparison of eleven static heuristics for mapping
      a class of independent tasks onto heterogeneous distributed computing
      systems", JPDC 61(6), 2001, pp. 810-837.

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    P : list[list[int]]
        n×m ToA matrix.

    Returns
    -------
    (alpha, makespan) or (None, 0) if infeasible.
    """
    loads = [0] * m
    alpha = [-1] * n
    assigned = [False] * n

    best_mach = [0] * n
    best_ct = [INF] * n
    machine_jobs = [set() for _ in range(m)]

    # Initial best machine and completion time for each job
    for i in range(n):
        b_j = -1
        b_ct = INF
        for j in range(m):
            if P[i][j] < INF:
                ct = P[i][j]
                if ct < b_ct:
                    b_ct = ct
                    b_j = j
        if b_j == -1:
            return None, 0
        best_mach[i] = b_j
        best_ct[i] = b_ct
        machine_jobs[b_j].add(i)

    # Min-heap of (best_ct, job_id, machine_id)
    heap = [(best_ct[i], i, best_mach[i]) for i in range(n)]
    heapq.heapify(heap)

    remaining = n
    while remaining > 0:
        ct, job, mach = heapq.heappop(heap)
        if assigned[job] or ct != best_ct[job] or mach != best_mach[job]:
            continue

        alpha[job] = mach
        loads[mach] += P[job][mach]
        assigned[job] = True
        remaining -= 1
        machine_jobs[mach].discard(job)

        # Only update unassigned jobs that were targeting 'mach'
        affected = list(machine_jobs[mach])
        machine_jobs[mach].clear()

        for i in affected:
            b_j = -1
            b_ct = INF
            for j in range(m):
                if P[i][j] < INF:
                    c = loads[j] + P[i][j]
                    if c < b_ct or (c == b_ct and P[i][j] < P[i][b_j]):
                        b_ct = c
                        b_j = j
            best_mach[i] = b_j
            best_ct[i] = b_ct
            machine_jobs[b_j].add(i)
            heapq.heappush(heap, (b_ct, i, b_j))

    return alpha, max(loads)


# ──────────────────────────────────────────────────────────────────────
# Baseline 4: Max-Min Heuristic
# ──────────────────────────────────────────────────────────────────────

def max_min(
    n: int, m: int,
    P: List[List[int]],
) -> Tuple[Optional[List[int]], int]:
    """
    Baseline 4: Max-Min Heuristic.

    For each unassigned job, computes its minimum completion time across
    all machines. Then selects the job with the LARGEST such minimum
    completion time (the "hardest" job) and assigns it to the machine
    that achieved that minimum. Prioritizes hard/large jobs first.

    Reference: Ibarra, O.H. & Kim, C.E. "Heuristic algorithms for
               scheduling independent tasks on nonidentical processors",
               Journal of the ACM 24(2), 1977, pp. 280-289.

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    P : list[list[int]]
        n×m ToA matrix.

    Returns
    -------
    (alpha, makespan) or (None, 0) if infeasible.
    """
    loads = [0] * m
    alpha = [-1] * n
    assigned = [False] * n

    best_mach = [0] * n
    best_ct = [INF] * n
    machine_jobs = [set() for _ in range(m)]

    # Initial best machine and completion time for each job
    for i in range(n):
        b_j = -1
        b_ct = INF
        for j in range(m):
            if P[i][j] < INF:
                ct = P[i][j]
                if ct < b_ct:
                    b_ct = ct
                    b_j = j
        if b_j == -1:
            return None, 0
        best_mach[i] = b_j
        best_ct[i] = b_ct
        machine_jobs[b_j].add(i)

    # Max-heap: negative ct, negative processing time
    heap = [(-best_ct[i], -P[i][best_mach[i]], i, best_mach[i]) for i in range(n)]
    heapq.heapify(heap)

    remaining = n
    while remaining > 0:
        neg_ct, neg_p, job, mach = heapq.heappop(heap)
        ct = -neg_ct
        if assigned[job] or ct != best_ct[job] or mach != best_mach[job]:
            continue

        alpha[job] = mach
        loads[mach] += P[job][mach]
        assigned[job] = True
        remaining -= 1
        machine_jobs[mach].discard(job)

        # Only update unassigned jobs that were targeting 'mach'
        affected = list(machine_jobs[mach])
        machine_jobs[mach].clear()

        for i in affected:
            b_j = -1
            b_ct = INF
            for j in range(m):
                if P[i][j] < INF:
                    c = loads[j] + P[i][j]
                    if c < b_ct or (c == b_ct and P[i][j] < P[i][b_j]):
                        b_ct = c
                        b_j = j
            best_mach[i] = b_j
            best_ct[i] = b_ct
            machine_jobs[b_j].add(i)
            heapq.heappush(heap, (-b_ct, -P[i][b_j], i, b_j))

    return alpha, max(loads)


# ──────────────────────────────────────────────────────────────────────
# Summary runner
# ──────────────────────────────────────────────────────────────────────

ALL_BASELINES = {
    "Random Assignment": random_assignment,
    "Greedy Least-Loaded": greedy_least_loaded,
    "Min-Min": min_min,
    "Max-Min": max_min,
}


def run_all_baselines(
    n: int, m: int,
    P: List[List[int]],
    seed: int = 42,
) -> dict:
    """
    Run all four baselines and return results.

    Returns dict: name -> {"alpha": list, "makespan": int, "feasible": bool}
    """
    results = {}

    for name, fn in ALL_BASELINES.items():
        if name == "Random Assignment":
            alpha, makespan = fn(n, m, P, seed=seed)
        else:
            alpha, makespan = fn(n, m, P)

        results[name] = {
            "alpha": alpha,
            "makespan": makespan,
            "feasible": alpha is not None,
        }

    return results
