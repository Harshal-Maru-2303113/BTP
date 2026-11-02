"""
Phase 1.5: Energy-Optimal Capacity-Constrained Downshifting.

Optimizes the Phase 1 assignment to minimize total radio energy consumption
across all packets while strictly maintaining:
  1. The 2-approximation makespan upper bound: max_j delta_j <= 2 * w_star <= 2 * OPT.
  2. Individual job feasibility: P[i][alpha(i)] <= w_star.
  3. Hypercycle boundary compliance: max_j delta_j <= H_ms.

Algorithm:
  - Considers all packets assigned to higher spreading factors (SF > 7).
  - Greedily downshifts packets to lower-SF machines that offer the highest energy reduction Delta E.
  - Ensures target machine load after receiving the job satisfies delta_target + P[i][target] <= 2 * w_star.
  - Performs intra-SF channel load balancing to prevent channel bottlenecks.
"""

from typing import List, Tuple, Dict, Optional
from data_structures import Machine, INF


def energy_optimal_downshift(
    n: int,
    m: int,
    P: List[List[int]],
    E: List[List[float]],
    alpha: List[int],
    w_star: int,
    machines: List[Machine],
    H_ms: Optional[int] = None,
) -> Tuple[List[int], Dict[str, float]]:
    """
    Downshift packet assignments to minimize total energy subject to makespan <= 2 * w_star.

    Parameters
    ----------
    n, m : int
        Number of packets and machines.
    P : List[List[int]]
        Time-on-Air matrix (integer ms).
    E : List[List[float]]
        Energy matrix (millijoules per packet transmission).
    alpha : List[int]
        Initial assignment from Phase 1.
    w_star : int
        Critical makespan threshold from Phase 1 binary search.
    machines : List[Machine]
        List of machine resource descriptors.
    H_ms : Optional[int]
        Optional hypercycle duration in milliseconds.

    Returns
    -------
    (alpha_star, energy_stats)
        alpha_star: Energy-optimized assignment list.
        energy_stats: Dictionary containing initial energy, optimized energy, and savings.
    """
    if n == 0 or m == 0 or not alpha:
        return list(alpha), {
            "initial_energy_mj": 0.0,
            "optimized_energy_mj": 0.0,
            "energy_saved_mj": 0.0,
            "energy_reduction_pct": 0.0,
            "downshift_moves": 0,
        }

    # Strict capacity bound: preserves the 2-approximation theorem
    cap_bound = 2 * w_star
    if H_ms is not None:
        cap_bound = min(cap_bound, H_ms)

    # Work on a copy of alpha
    curr_alpha = list(alpha)

    # Compute initial machine loads
    loads = [0] * m
    for i in range(n):
        mach = curr_alpha[i]
        if 0 <= mach < m and P[i][mach] < INF:
            loads[mach] += P[i][mach]

    # Compute initial energy
    initial_energy = sum(
        E[i][curr_alpha[i]]
        for i in range(n)
        if 0 <= curr_alpha[i] < m and E[i][curr_alpha[i]] < INF
    )

    downshift_moves = 0
    improved = True
    max_passes = 10  # Each packet can downshift at most 5 SF levels

    pass_count = 0
    while improved and pass_count < max_passes:
        improved = False
        pass_count += 1

        # Evaluate candidate downshifts across all packets
        # Find best candidate moves sorted by energy saving Delta E
        candidate_moves = []

        for i in range(n):
            curr_mach = curr_alpha[i]
            if curr_mach < 0 or curr_mach >= m:
                continue

            curr_e = E[i][curr_mach]
            curr_sf = machines[curr_mach].sf
            curr_p = P[i][curr_mach]

            # Consider target machines with lower SF or same SF with lower load
            for target_mach in range(m):
                if target_mach == curr_mach:
                    continue

                target_p = P[i][target_mach]
                target_e = E[i][target_mach]
                target_sf = machines[target_mach].sf

                # Must be feasible under Phase 1 threshold
                if target_p > w_star or target_p >= INF:
                    continue

                # Must not violate the 2-approximation capacity ceiling
                if loads[target_mach] + target_p > cap_bound:
                    continue

                delta_e = curr_e - target_e
                if delta_e > 1e-4:
                    # Significant energy reduction
                    candidate_moves.append((delta_e, i, curr_mach, target_mach, target_p, curr_p))
                elif abs(delta_e) <= 1e-4 and target_sf == curr_sf:
                    # Same energy / SF: use as secondary load-leveling if target is significantly less loaded
                    load_reduction = loads[curr_mach] - (loads[target_mach] + target_p)
                    if load_reduction > 10:  # meaningful load balance
                        # Small positive priority for balancing
                        candidate_moves.append((0.001 * load_reduction, i, curr_mach, target_mach, target_p, curr_p))

        # Sort candidate moves by descending energy reduction
        candidate_moves.sort(key=lambda x: x[0], reverse=True)

        # Apply non-conflicting moves in this pass
        for delta_e, i, src, dst, dst_p, src_p in candidate_moves:
            # Re-verify capacity constraint dynamically
            if loads[dst] + dst_p <= cap_bound and curr_alpha[i] == src:
                curr_alpha[i] = dst
                loads[src] -= src_p
                loads[dst] += dst_p
                downshift_moves += 1
                improved = True

    # Compute final energy
    optimized_energy = sum(
        E[i][curr_alpha[i]]
        for i in range(n)
        if 0 <= curr_alpha[i] < m and E[i][curr_alpha[i]] < INF
    )

    energy_saved = max(0.0, initial_energy - optimized_energy)
    reduction_pct = (energy_saved / initial_energy * 100.0) if initial_energy > 0 else 0.0

    stats = {
        "initial_energy_mj": round(initial_energy, 3),
        "optimized_energy_mj": round(optimized_energy, 3),
        "energy_saved_mj": round(energy_saved, 3),
        "energy_reduction_pct": round(reduction_pct, 2),
        "downshift_moves": downshift_moves,
    }

    return curr_alpha, stats

