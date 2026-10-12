"""
Graph construction utilities for the residual network and admissible subgraph.

Provides:
  - Reversed residual graph multi-source Dijkstra using reduced costs
  - Admissible graph extraction (edges with zero reduced costs)
  - BFS height computation for Unsplittable-Blocking-Flow
  - Machine load calculation
"""

import heapq
from collections import deque
from typing import List, Tuple, Dict, Set

from data_structures import INF

AdjList = Dict[int, List[int]]


def compute_loads(n: int, m: int, P: List[List[int]], alpha: List[int]) -> List[int]:
    """Compute current load on each machine given assignment alpha."""
    loads = [0] * m
    for i in range(n):
        loads[alpha[i]] += P[i][alpha[i]]
    return loads


def dijkstra_to_sinks(
    n: int, m: int,
    P: List[List[int]], C: List[List[int]],
    w: int,
    alpha: List[int],
    pi_job: List[float], pi_mach: List[float],
    sinks: List[int],
) -> Tuple[List[float], List[float]]:
    """
    Compute shortest-path distances from every node to the sink set M⁻
    using reduced costs on the residual graph.

    Nodes:
      Jobs: 0 ... n-1
      Machines: n ... n+m-1

    Edges in residual graph:
      - Backward edge (machine j -> job i, where alpha[i] == j):
        Original cost = -C[i][j].
        Reduced cost = -C[i][j] - pi_mach[j] + pi_job[i].
      - Forward edge (job i -> machine j, where alpha[i] != j and P[i][j] <= w):
        Original cost = +C[i][j].
        Reduced cost = C[i][j] - pi_job[i] + pi_mach[j].

    We reverse all edges and run multi-source Dijkstra from sinks in M⁻.
    Returns (d_job, d_mach).
    """
    total = n + m
    dist = [float("inf")] * total

    # Build reversed adjacency list with reduced costs
    rev_adj: Dict[int, List[Tuple[int, float]]] = {u: [] for u in range(total)}

    for i in range(n):
        j_curr = alpha[i]
        # Original: machine j_curr -> job i
        # Reversed: job i -> machine j_curr
        rc_back = -C[i][j_curr] - pi_mach[j_curr] + pi_job[i]
        rc_back = max(0.0, rc_back)  # numerical safety clamp
        rev_adj[i].append((n + j_curr, rc_back))

        # Original: job i -> machine j
        # Reversed: machine j -> job i
        for j in range(m):
            if j == j_curr:
                continue
            if P[i][j] <= w and P[i][j] < INF:
                rc_fwd = C[i][j] - pi_job[i] + pi_mach[j]
                rc_fwd = max(0.0, rc_fwd)
                rev_adj[n + j].append((i, rc_fwd))

    heap: List[Tuple[float, int]] = []
    for j in sinks:
        node = n + j
        dist[node] = 0.0
        heapq.heappush(heap, (0.0, node))

    while heap:
        d_v, v = heapq.heappop(heap)
        if d_v > dist[v]:
            continue
        for u, rc in rev_adj[v]:
            nd = d_v + rc
            if nd < dist[u]:
                dist[u] = nd
                heapq.heappush(heap, (nd, u))

    d_job = [dist[i] for i in range(n)]
    d_mach = [dist[n + j] for j in range(m)]
    return d_job, d_mach


def build_admissible_graph(
    n: int, m: int,
    P: List[List[int]], C: List[List[int]],
    w: int,
    alpha: List[int],
    pi_job: List[float], pi_mach: List[float],
) -> Dict[int, List[int]]:
    """
    Build the admissible subgraph containing only edges with zero reduced cost.
    Returns forward adjacency list.
    """
    total = n + m
    adj: Dict[int, List[int]] = {u: [] for u in range(total)}

    for i in range(n):
        j_curr = alpha[i]
        # Backward edge: machine j_curr -> job i
        rc_back = -C[i][j_curr] - pi_mach[j_curr] + pi_job[i]
        if abs(rc_back) < 1e-9:
            adj[n + j_curr].append(i)

        # Forward edge: job i -> machine j
        for j in range(m):
            if j == j_curr:
                continue
            if P[i][j] <= w and P[i][j] < INF:
                rc_fwd = C[i][j] - pi_job[i] + pi_mach[j]
                if abs(rc_fwd) < 1e-9:
                    adj[i].append(n + j)

    return adj


def bfs_heights(
    total: int, n: int,
    adj: Dict[int, List[int]],
    sinks: List[int],
) -> List[float]:
    """
    Compute height labels h(u) = shortest hop distance from u to nearest sink
    in the admissible graph.
    """
    rev_adj: Dict[int, List[int]] = {u: [] for u in range(total)}
    for u, nbrs in adj.items():
        for v in nbrs:
            rev_adj[v].append(u)

    h = [float("inf")] * total
    q = deque()
    for j in sinks:
        node = n + j
        h[node] = 0.0
        q.append(node)

    while q:
        v = q.popleft()
        for u in rev_adj[v]:
            if h[u] == float("inf"):
                h[u] = h[v] + 1
                q.append(u)

    return h


def get_admissible_successors(
    u: int,
    adj: Dict[int, List[int]],
    h: List[float],
) -> List[int]:
    """
    Return list S(u) of admissible successors v with h(u) = h(v) + 1,
    sorted deterministically in ascending order.
    """
    hu = h[u]
    if hu == float("inf"):
        return []
    res = [v for v in adj.get(u, []) if h[v] != float("inf") and hu == h[v] + 1]
    res.sort()
    return res
