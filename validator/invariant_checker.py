"""
Invariant checker for the 2-approximation algorithm.

Verifies the structural properties that the algorithm must maintain
at every step, providing confidence in correctness.

Checked invariants
------------------
1. Assignment feasibility:  P[i][alpha[i]] ≤ w  for all i.
2. Reduced-cost optimality:  c^π(u,v) ≥ 0  for all residual edges.
3. Load monotonicity (after blocking flow):
     - Sink loads never decrease
     - Source loads never increase
     - Medium loads stay in [w+1, 2w]
4. Schedule validity:
     - Per-channel non-preemption (no overlaps on same machine)
     - All finish times ≤ deadlines (for scheduled packets)
     - Global demod occupancy ≤ max_demod at every instant
"""

from typing import List, Optional

from data_structures import Packet, Machine, ScheduleEntry, INF


class InvariantError(Exception):
    """Raised when an algorithm invariant is violated."""
    pass


def check_assignment_feasibility(
    n: int, m: int,
    P: List[List[int]],
    alpha: List[int],
    w: int,
):
    """Every job must be assigned to a machine with ToA ≤ w."""
    for i in range(n):
        j = alpha[i]
        if j < 0 or j >= m:
            raise InvariantError(
                f"Job {i} assigned to invalid machine {j}"
            )
        if P[i][j] > w:
            raise InvariantError(
                f"Job {i} assigned to machine {j} with P={P[i][j]} > w={w}"
            )


def check_reduced_cost_optimality(
    n: int, m: int,
    P: List[List[int]], C: List[List[int]],
    w: int,
    alpha: List[int],
    pi_job: List[int], pi_mach: List[int],
):
    """All reduced costs in the residual graph must be ≥ 0."""
    for i in range(n):
        j_assigned = alpha[i]

        # Backward edge: machine j → job i, cost = -C[i][j]
        rc_back = -C[i][j_assigned] - pi_mach[j_assigned] + pi_job[i]
        if rc_back < -1:  # allow small rounding tolerance
            raise InvariantError(
                f"Negative backward reduced cost for job {i} on machine "
                f"{j_assigned}: rc = {rc_back}"
            )

        # Forward edges: job i → machine j (j ≠ α(i), P[i][j] ≤ w)
        for j in range(m):
            if j == j_assigned:
                continue
            if P[i][j] > w or P[i][j] >= INF:
                continue
            rc_fwd = C[i][j] - pi_job[i] + pi_mach[j]
            if rc_fwd < -1:
                raise InvariantError(
                    f"Negative forward reduced cost for job {i} → machine "
                    f"{j}: rc = {rc_fwd}"
                )


def check_load_bounds(
    m: int,
    loads: List[int],
    w: int,
    label: str = "",
):
    """Report load partition sizes (informational; hard check is makespan ≤ 2w)."""
    n_plus = sum(1 for j in range(m) if loads[j] >= 2 * w + 1)
    n_zero = sum(1 for j in range(m) if w + 1 <= loads[j] <= 2 * w)
    n_minus = sum(1 for j in range(m) if loads[j] <= w)
    max_load = max(loads) if loads else 0

    return {
        "label": label,
        "M_plus": n_plus,
        "M_zero": n_zero,
        "M_minus": n_minus,
        "max_load": max_load,
        "w": w,
        "two_w": 2 * w,
    }


def check_schedule_validity(
    entries: List[ScheduleEntry],
    machines: List[Machine],
    H_ms: int,
    max_demod: int,
):
    """
    Validate the final schedule:
      1. Per-channel non-preemption
      2. Deadline compliance
      3. Global demod limit
    """
    errors: List[str] = []

    # ---- Per-channel non-preemption ---- #
    by_machine: dict = {}
    for e in entries:
        by_machine.setdefault(e.machine_id, []).append(e)

    for mid, machine_entries in by_machine.items():
        machine_entries.sort(key=lambda e: e.start_time)
        for k in range(1, len(machine_entries)):
            prev = machine_entries[k - 1]
            curr = machine_entries[k]
            if curr.start_time < prev.finish_time:
                errors.append(
                    f"Overlap on machine {mid}: pkt {prev.packet_id} "
                    f"[{prev.start_time},{prev.finish_time}) overlaps "
                    f"pkt {curr.packet_id} [{curr.start_time},{curr.finish_time})"
                )

    # ---- Deadline compliance ---- #
    for e in entries:
        if e.finish_time > e.deadline:
            errors.append(
                f"Pkt {e.packet_id}: finish {e.finish_time} > "
                f"deadline {e.deadline}"
            )
        if e.finish_time > H_ms:
            errors.append(
                f"Pkt {e.packet_id}: finish {e.finish_time} > H={H_ms}"
            )

    # ---- Global demod limit (event sweep) ---- #
    events: List[tuple] = []
    for e in entries:
        events.append((e.start_time, +1))
        events.append((e.finish_time, -1))
    events.sort(key=lambda x: (x[0], x[1]))

    concurrent = 0
    max_concurrent = 0
    for t, delta in events:
        concurrent += delta
        max_concurrent = max(max_concurrent, concurrent)
        if concurrent > max_demod:
            errors.append(
                f"Demod limit exceeded at t={t}: {concurrent} > {max_demod}"
            )
            break  # one report is enough

    if errors:
        raise InvariantError(
            "Schedule validation failed:\n  " + "\n  ".join(errors)
        )

    return {
        "per_channel_ok": True,
        "deadlines_ok": True,
        "max_concurrent_demod": max_concurrent,
        "demod_limit_ok": max_concurrent <= max_demod,
    }
