"""
Binary search over candidate makespan w  (Theorem 3.4)

Finds the smallest w for which Unsplittable-Truemper produces an
assignment with all loads ≤ 2w, yielding Cost(P, α) ≤ 2·OPT(P).

Overall complexity: O(m² · A · log m · log(w_max - w_min))
"""

import math
from typing import List, Optional, Tuple

from data_structures import INF
from approximation.graph_utils import compute_loads
from approximation.truemper import unsplittable_truemper


def find_2approx_assignment(
    n: int, m: int,
    P: List[List[int]],
    C: List[List[int]],
    b: float,
    H_ms: Optional[int] = None,
) -> Tuple[Optional[List[int]], int]:
    """
    Binary search + Unsplittable-Truemper to find assignment with
    makespan ≤ 2 · OPT(P).

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    P : List[List[int]]
        n×m ToA matrix (INF for infeasible).
    C : List[List[int]]
        n×m cost matrix.
    b : float
        Rounding base = 1 + 1/m.
    H_ms : Optional[int]
        Optional hypercycle duration in milliseconds.

    Returns
    -------
    (alpha, w_star) :
        alpha = assignment list (or None if all infeasible)
        w_star = the critical w value found by binary search
    """
    if n == 0:
        return [], 0

    # ---- Compute binary search bounds ---- #
    # w_min: each job must be assigned to at least one machine
    min_toas = []
    max_toas = []
    for i in range(n):
        row_min = INF
        row_max = 0
        for j in range(m):
            if P[i][j] < INF:
                row_min = min(row_min, P[i][j])
                row_max = max(row_max, P[i][j])
        if row_min >= INF:
            return None, 0  # Infeasible: job i has no usable machine
        min_toas.append(row_min)
        max_toas.append(row_max)

    w_min = max(min_toas)

    # Tight upper bound: average min-ToA load plus maximum possible job duration
    # This upper bound guarantees an assignment exists if the system is balanceable.
    sum_min = sum(min_toas)
    w_max_tight = math.ceil(sum_min / m) + max(max_toas)
    
    if H_ms is not None:
        w_max = min(H_ms, w_max_tight * 2)
    else:
        w_max = w_max_tight * 2

    # Ensure w_max >= w_min
    w_max = max(w_min, w_max)

    # ---- Binary search ---- #
    lo, hi = w_min, w_max
    best_alpha: Optional[List[int]] = None
    best_w = w_max

    while lo <= hi:
        mid = (lo + hi) // 2

        # Run Unsplittable-Truemper for candidate bound mid
        result = unsplittable_truemper(n, m, P, C, mid, b)

        if result is not None:
            # Success: all loads ≤ 2·mid
            best_alpha = list(result)
            best_w = mid
            hi = mid - 1
        else:
            # Failure: OPT > mid
            lo = mid + 1

    if best_alpha is None:
        return None, 0

    return best_alpha, best_w
