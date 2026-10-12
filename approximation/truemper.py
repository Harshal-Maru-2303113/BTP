"""
Unsplittable-Truemper  (Algorithm 2 / Figure 2)

Outer loop of the Gairing–Monien–Woclaw (2007) 2-approximation framework.
Maintains node potentials π and iteratively computes shortest-path admissible
graphs for the inner Unsplittable-Blocking-Flow procedure.

Complexity per invocation: O(m² · A · log m)
"""

import math
from collections import deque
from typing import List, Optional, Set, Dict

from data_structures import INF
from approximation.graph_utils import (
    compute_loads,
    dijkstra_to_sinks,
    build_admissible_graph,
)
from approximation.blocking_flow import unsplittable_blocking_flow


def unsplittable_truemper(
    n: int, m: int,
    P: List[List[int]],
    C: List[List[int]],
    w: int,
    b: float,
    alpha: Optional[List[int]] = None,
) -> Optional[List[int]]:
    """
    Algorithm 2: Unsplittable-Truemper.

    Iteratively improves an assignment by pushing jobs from overloaded machines
    (M⁺) to underloaded machines (M⁻) along shortest augmenting paths.

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    P : List[List[int]]
        n×m ToA matrix (INF for infeasible).
    C : List[List[int]]
        n×m cost matrix C[i][j] = floor(log_b(P[i][j])).
    w : int
        Candidate makespan bound.
    b : float
        Rounding base = 1 + 1/m.
    alpha : Optional[List[int]]
        Optional initial assignment. If None, uses seed assignment
        where each job i is assigned to argmin_j P[i][j].

    Returns
    -------
    alpha : List[int] or None
        Updated assignment with all loads ≤ 2w if successful.
        None if OPT > w (lower-bound certificate).
    """
    if n == 0:
        return []

    potential_cap = math.log(m) / math.log(b) if m > 1 else float("inf")

    # Initial assignment: each job to machine with minimum ToA among those with P[i][j] <= w
    if alpha is None:
        alpha = []
        for i in range(n):
            feasible_machines = [j for j in range(m) if P[i][j] <= w and P[i][j] < INF]
            if not feasible_machines:
                return None  # Job i cannot be scheduled with makespan w
            best_j = min(feasible_machines, key=lambda j: (P[i][j], C[i][j], j))
            alpha.append(best_j)
    else:
        alpha = list(alpha)

    loads = compute_loads(n, m, P, alpha)

    # Initial potentials:
    # Machine potentials start at 0.
    # Job potentials set to C[i][alpha[i]] so that initial reduced costs
    # on backward edges are -C + 0 + C = 0, and on forward edges C[i][j] - C[i][alpha[i]] >= 0.
    pi_mach = [0.0] * m
    pi_job = [float(C[i][alpha[i]]) for i in range(n)]

    max_iters = int(m * potential_cap) + 20
    iters = 0

    while iters < max_iters:
        iters += 1
        m_plus = [j for j in range(m) if loads[j] >= 2 * w + 1]
        m_minus = [j for j in range(m) if loads[j] <= w]

        # 1. Success condition: M⁺ = ∅
        if not m_plus:
            return alpha

        # 2. Lower-bound termination: potential cap reached
        if any(pi_mach[j] >= potential_cap for j in m_plus):
            return None

        # 3. Dijkstra: shortest distances to sinks M⁻
        d_job, d_mach = dijkstra_to_sinks(
            n, m, P, C, w, alpha, pi_job, pi_mach, m_minus,
        )

        reachable_m_plus = [j for j in m_plus if d_mach[j] < float("inf")]
        if not reachable_m_plus:
            return None  # No path from M⁺ to M⁻ -> OPT > w

        # 4. Update potentials: π ← π + d
        for i in range(n):
            if d_job[i] < float("inf"):
                pi_job[i] += d_job[i]
        for j in range(m):
            if d_mach[j] < float("inf"):
                pi_mach[j] += d_mach[j]

        # 5. Build admissible graph (edges with zero reduced costs)
        admissible_adj = build_admissible_graph(
            n, m, P, C, w, alpha, pi_job, pi_mach,
        )

        # 6. M⁺_min: machines in M⁺ with minimum potential (closest to M⁻)
        min_pi = min(pi_mach[j] for j in m_plus)
        m_plus_min = [j for j in m_plus if abs(pi_mach[j] - min_pi) < 1e-9]

        # Restrict admissible graph to nodes reachable from M⁺_min
        reachable: Set[int] = set()
        q = deque([n + j for j in m_plus_min])
        for node in q:
            reachable.add(node)
        while q:
            u = q.popleft()
            for v in admissible_adj.get(u, []):
                if v not in reachable:
                    reachable.add(v)
                    q.append(v)

        filtered_adj: Dict[int, List[int]] = {
            u: [v for v in admissible_adj.get(u, []) if v in reachable]
            for u in reachable
        }
        for u in range(n + m):
            if u not in filtered_adj:
                filtered_adj[u] = []

        # 7. Run inner loop: blocking flow
        alpha_before = list(alpha)
        alpha, phases = unsplittable_blocking_flow(
            n, m, alpha, loads, filtered_adj, P, w,
        )
        loads = compute_loads(n, m, P, alpha)

        # Check if progress was made; if no push occurred and distances were zero, terminate
        if alpha == alpha_before:
            if all(abs(d_mach[j]) < 1e-9 for j in reachable_m_plus):
                return None

    return None
