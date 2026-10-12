"""
Unsplittable-Blocking-Flow  (Algorithm 1 / Figure 1)

Inner loop of the Gairing–Monien–Woclaw (2007) 2-approximation algorithm.
Pushes discrete jobs along helpful paths from overloaded machines (M⁺)
toward underloaded machines (M⁻) in the admissible shortest-path graph G'_α(w).

Complexity: O(m · A) per invocation, where A = number of feasible machine options.
"""

from typing import List, Tuple, Dict, Set, Optional

from data_structures import INF
from approximation.graph_utils import bfs_heights, get_admissible_successors


def _build_helpful_path(
    n: int, m: int,
    v0_j: int,
    adj: Dict[int, List[int]],
    h: List[float],
    loads: List[int],
    P: List[List[int]],
    w: int,
) -> Optional[List[int]]:
    """
    Construct a helpful path starting from helpful machine v0_j.
    Implements Definition 2.4 of Gairing–Monien–Woclaw (2007).

    A helpful path is an alternating sequence [m₀, j₀, m₁, j₁, ..., m_r]
    where:
      - v₀ = m₀ is a helpful machine of minimum height
      - Each edge is admissible (h(u) = h(v) + 1)
      - Intermediate machines remain in [w+1, 2w] after swap
      - Terminal machine remains ≤ 2w after receiving job

    Returns path list or None if no valid helpful path can be extended.
    """
    path: List[int] = [n + v0_j]
    curr_mach = v0_j

    while True:
        mnode = n + curr_mach
        S_m = get_admissible_successors(mnode, adj, h)
        if not S_m:
            return None
        s_job = S_m[0]
        path.append(s_job)

        S_j = get_admissible_successors(s_job, adj, h)
        if not S_j:
            return None
        next_mnode = S_j[0]
        next_mach = next_mnode - n
        path.append(next_mnode)

        p_pushed = P[s_job][next_mach]
        if p_pushed >= INF:
            return None

        load_next = loads[next_mach]

        # Condition (4): Terminal machine check (receives s_job and stays <= 2w)
        if load_next + p_pushed <= 2 * w:
            return path

        # Condition (3): Intermediate machine check
        S_next = get_admissible_successors(next_mnode, adj, h)
        if not S_next:
            return None
        s_next_job = S_next[0]
        p_give = P[s_next_job][next_mach]
        if p_give >= INF:
            return None

        new_load = load_next + p_pushed - p_give
        if w + 1 <= new_load <= 2 * w:
            curr_mach = next_mach
            continue
        else:
            return None


def unsplittable_blocking_flow(
    n: int, m: int,
    alpha: List[int],
    loads: List[int],
    admissible_adj: Dict[int, List[int]],
    P: List[List[int]],
    w: int,
) -> Tuple[List[int], int]:
    """
    Algorithm 1: Unsplittable-Blocking-Flow.

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    alpha : List[int]
        Current assignment (modified in-place).
    loads : List[int]
        Current machine loads (modified in-place).
    admissible_adj : Dict[int, List[int]]
        Adjacency list of the admissible graph G'_α(w).
    P : List[List[int]]
        ToA processing time matrix.
    w : int
        Target makespan parameter.

    Returns
    -------
    (alpha, phases)
    """
    total = n + m
    adj: Dict[int, List[int]] = {u: list(nbrs) for u, nbrs in admissible_adj.items()}
    phases = 0
    max_phases = m

    while phases < max_phases:
        m_minus = [j for j in range(m) if loads[j] <= w]
        m_plus = [j for j in range(m) if loads[j] >= 2 * w + 1]

        if not m_minus or not m_plus:
            break

        h = bfs_heights(total, n, adj, m_minus)
        reachable_m_plus = [j for j in m_plus if h[n + j] < float("inf")]
        if not reachable_m_plus:
            break

        phases += 1
        pushed_any = False

        while True:
            m_minus = [j for j in range(m) if loads[j] <= w]
            m_plus = [j for j in range(m) if loads[j] >= 2 * w + 1]
            if not m_minus or not m_plus:
                break

            # Find helpful machines (Definition 2.3)
            helpful_machines = []
            for j in m_plus:
                mnode = n + j
                hj = h[mnode]
                if hj == float("inf"):
                    continue
                S_m = get_admissible_successors(mnode, adj, h)
                if not S_m:
                    continue
                s_job = S_m[0]
                if P[s_job][j] >= INF:
                    continue
                if loads[j] >= w + 1 + P[s_job][j]:
                    helpful_machines.append((hj, j))

            if not helpful_machines:
                break

            # Choose helpful machine of minimum height
            min_h = min(item[0] for item in helpful_machines)
            v0_j = min(j for (hj, j) in helpful_machines if hj == min_h)

            # Construct helpful path (Definition 2.4)
            path = _build_helpful_path(n, m, v0_j, adj, h, loads, P, w)
            if path is None or len(path) < 3:
                h[n + v0_j] = float("inf")
                continue

            # Push jobs along the helpful path: [m0, j0, m1, j1, ..., mr]
            num_swaps = (len(path) - 1) // 2
            for k in range(num_swaps):
                job_idx = path[2 * k + 1]
                old_m = path[2 * k] - n
                new_m = path[2 * k + 2] - n

                loads[old_m] -= P[job_idx][old_m]
                loads[new_m] += P[job_idx][new_m]
                alpha[job_idx] = new_m

                # Update adjacency list in admissible graph (reverse edge directions)
                if job_idx in adj[n + old_m]:
                    adj[n + old_m].remove(job_idx)
                if (n + old_m) not in adj[job_idx]:
                    adj[job_idx].append(n + old_m)

                if (n + new_m) in adj[job_idx]:
                    adj[job_idx].remove(n + new_m)
                if job_idx not in adj[n + new_m]:
                    adj[n + new_m].append(job_idx)

            pushed_any = True

        if not pushed_any:
            break

    return alpha, phases
