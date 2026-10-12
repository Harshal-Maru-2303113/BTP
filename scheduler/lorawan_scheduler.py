"""
LoRaWAN-Hypercycle-Scheduler  (Algorithm 3)

End-to-end scheduling framework that integrates:
  Phase 1 – Unrelated machine makespan minimisation (2-approximation)
  Phase 2 – Per-channel EDF timeline with demod-aware placement
  Phase 3 – Priority-based packet dropping (deadline + demod violations)

The 8-demod limit is checked DURING Phase 2 (sweep-line with segment
tree) rather than as a post-hoc check, so violations are caught at
placement time and packets are time-shifted before resorting to drops.
"""

import math
from typing import List, Tuple, Optional, Set

from data_structures import (
    Packet, Machine, ScheduleEntry, ScheduleResult, INF,
)
from segment_tree import SegmentTree
from approximation.binary_search import find_2approx_assignment
from approximation.graph_utils import compute_loads
from lorawan_toa import compute_cost_matrix


def _build_edf_timeline_with_demod(
    packets: List[Packet],
    machines: List[Machine],
    P: List[List[int]],
    alpha: List[int],
    H_ms: int,
    max_demod: int,
    candidate_ids: List[int],
) -> Tuple[List[ScheduleEntry], List[int], List[int]]:
    """
    Phase 2 + integrated Phase 3: build per-channel EDF timelines while
    enforcing the gateway demodulation limit via a segment tree.

    For each channel, packets are placed in EDF (deadline) order.
    Before placing a packet at [s, f), the segment tree is queried for
    max occupancy in that interval.  If occupancy ≥ max_demod, the
    start time is shifted forward until a feasible slot is found.

    Parameters
    ----------
    packets : list[Packet]
        Full packet list (indexed by packet.id).
    machines : list[Machine]
        Machine list.
    P : list[list[int]]
        ToA matrix (only rows for candidate_ids are used).
    alpha : list[int]
        Assignment: alpha[local_idx] = machine index.
    H_ms : int
        Hypercycle duration in ms.
    max_demod : int
        Gateway concurrent demodulation limit (8).
    candidate_ids : list[int]
        Packet IDs in the current candidate set.

    Returns
    -------
    (entries, deadline_violators, demod_violators)
    """
    n = len(candidate_ids)
    m = len(machines)

    # Group local indices by assigned machine
    machine_jobs: List[List[int]] = [[] for _ in range(m)]
    for local_i in range(n):
        machine_jobs[alpha[local_i]].append(local_i)

    # Sort each machine's jobs by deadline (EDF)
    for j in range(m):
        machine_jobs[j].sort(
            key=lambda li: packets[candidate_ids[li]].deadline
        )

    # Segment tree over [0, H_ms) for global demod occupancy
    demod_tree = SegmentTree(H_ms)

    entries: List[ScheduleEntry] = []
    deadline_violators: List[int] = []   # local indices
    demod_violators: List[int] = []      # local indices

    # Per-channel cursor: next available time on each machine
    channel_cursor = [0] * m

    # Process machines in a deterministic order; within each machine, EDF
    # We process ALL machines and build a global timeline.
    # To interleave fairly (earlier starts first), we use a merged
    # priority-queue approach.
    import heapq
    # (tentative_start, local_idx, machine_idx, queue_position)
    pq: list = []

    for j in range(m):
        if machine_jobs[j]:
            li = machine_jobs[j][0]
            pkt = packets[candidate_ids[li]]
            s = max(channel_cursor[j], pkt.release_time)
            heapq.heappush(pq, (s, li, j, 0))

    placed: set = set()  # local indices that have been placed

    while pq:
        _, li, j, q_pos = heapq.heappop(pq)

        if li in placed:
            # This entry may have been superseded; push next if needed
            continue

        pkt = packets[candidate_ids[li]]
        toa = P[li][j]

        # Earliest start respecting per-channel ordering and release time
        s = max(channel_cursor[j], pkt.release_time)
        f = s + toa

        # ---- Demod-aware placement (sweep-line shift) ---- #
        # Try to find earliest s' ≥ s where max occupancy in [s', s'+toa) < max_demod
        shift_limit = H_ms  # don't search past the hypercycle
        shifted = False

        if f <= H_ms:
            # Query current peak occupancy in [s, f-1]
            peak = demod_tree.range_max(s, f - 1) if f > s else 0
            if peak >= max_demod:
                # Need to shift forward
                # Strategy: scan forward in steps to find a clear window
                candidate_s = s + 1
                found = False
                while candidate_s + toa <= shift_limit:
                    peak = demod_tree.range_max(
                        candidate_s, candidate_s + toa - 1
                    )
                    if peak < max_demod:
                        s = candidate_s
                        f = s + toa
                        shifted = True
                        found = True
                        break
                    # Jump past congested region: increment by 1
                    # (Could optimise with binary search on segment tree)
                    candidate_s += 1
                if not found:
                    # Cannot fit within hypercycle with demod constraint
                    demod_violators.append(li)
                    placed.add(li)
                    # Push next job from this machine
                    next_pos = q_pos + 1
                    if next_pos < len(machine_jobs[j]):
                        nli = machine_jobs[j][next_pos]
                        npkt = packets[candidate_ids[nli]]
                        ns = max(channel_cursor[j], npkt.release_time)
                        heapq.heappush(pq, (ns, nli, j, next_pos))
                    continue

        # ---- Deadline check ---- #
        if f > pkt.deadline or f > H_ms:
            deadline_violators.append(li)
            placed.add(li)
            # Still advance cursor so subsequent packets on this channel
            # don't pile up behind a phantom
            # Push next job from this machine
            next_pos = q_pos + 1
            if next_pos < len(machine_jobs[j]):
                nli = machine_jobs[j][next_pos]
                npkt = packets[candidate_ids[nli]]
                ns = max(channel_cursor[j], npkt.release_time)
                heapq.heappush(pq, (ns, nli, j, next_pos))
            continue

        # ---- Place the packet ---- #
        demod_tree.range_add(s, f - 1, 1)
        channel_cursor[j] = f
        placed.add(li)

        mach = machines[j]
        entries.append(ScheduleEntry(
            packet_id=pkt.id,
            machine_id=j,
            start_time=s,
            finish_time=f,
            deadline=pkt.deadline,
            deadline_met=True,
            sf=mach.sf,
            channel=mach.channel,
        ))

        # Push next job from this machine
        next_pos = q_pos + 1
        if next_pos < len(machine_jobs[j]):
            nli = machine_jobs[j][next_pos]
            npkt = packets[candidate_ids[nli]]
            ns = max(channel_cursor[j], npkt.release_time)
            heapq.heappush(pq, (ns, nli, j, next_pos))

    return entries, deadline_violators, demod_violators


def lorawan_hypercycle_scheduler(
    packets: List[Packet],
    machines: List[Machine],
    P_full: List[List[int]],
    H_ms: int,
    max_demod: int,
    check_invariants: bool = False,
) -> ScheduleResult:
    """
    Algorithm 3: LoRaWAN-Hypercycle-Scheduler.

    Complete end-to-end scheduling:
      1. Clamp deadlines to H.
      2. Loop:
         a. Phase 1: 2-approx makespan minimisation.
         b. If makespan > H → drop lowest-priority, restart Phase 1.
         c. Phase 2: EDF timeline with demod-aware placement.
         d. If violations → drop lowest-priority offender, retry Phase 2
            (without re-running Phase 1).
         e. If clean → return schedule.

    Parameters
    ----------
    packets : list[Packet]
        All packets with release times, deadlines, priorities.
    machines : list[Machine]
        m = N_ch × N_sf machines.
    P_full : list[list[int]]
        Full n_total × m ToA matrix.
    H_ms : int
        Hypercycle duration in milliseconds.
    max_demod : int
        Maximum concurrent gateway demodulations (8).

    Returns
    -------
    ScheduleResult
    """
    m = len(machines)
    result = ScheduleResult()

    # Step 1: Clamp deadlines
    for pkt in packets:
        pkt.deadline = min(pkt.deadline, H_ms)

    # Candidate set (packet IDs)
    candidate_ids: List[int] = [pkt.id for pkt in packets]
    pkt_by_id = {pkt.id: pkt for pkt in packets}

    b = 1.0 + 1.0 / m if m > 0 else 2.0

    while candidate_ids:
        n_cand = len(candidate_ids)

        # Build local ToA matrix for candidates only
        # local_idx → candidate_ids[local_idx]
        P_local = [[INF] * m for _ in range(n_cand)]
        for li, pid in enumerate(candidate_ids):
            P_local[li] = list(P_full[pid])

        # ---- Phase 1: Makespan Minimisation ---- #
        C_local = compute_cost_matrix(P_local, m)

        alpha, w_star = find_2approx_assignment(
            n_cand, m, P_local, C_local, b, H_ms=H_ms,
        )

        if alpha is None:
            # Some packet can't be assigned at all – fallback: drop lowest priority
            victim_id = min(
                candidate_ids,
                key=lambda pid: (pkt_by_id[pid].priority, -pkt_by_id[pid].deadline, pid),
            )
            result.add_drop(victim_id)
            victim_idx = candidate_ids.index(victim_id)
            candidate_ids.pop(victim_idx)
            continue

        # Compute makespan
        loads = compute_loads(n_cand, m, P_local, alpha)
        makespan = max(loads) if loads else 0

        if makespan > H_ms:
            # Makespan exceeds hypercycle – drop lowest-priority candidate
            victim_id = min(
                candidate_ids,
                key=lambda pid: (pkt_by_id[pid].priority, -pkt_by_id[pid].deadline, pid),
            )
            result.add_drop(victim_id)
            victim_idx = candidate_ids.index(victim_id)
            candidate_ids.pop(victim_idx)
            continue  # Restart Phase 1 with reduced set

        result.approx_ratio_w = w_star

        # ---- Phase 2 + 3: EDF timeline with demod check ---- #
        # Retry Phase 2 after dropping offenders without re-running Phase 1
        while candidate_ids:
            entries, deadline_viols, demod_viols = _build_edf_timeline_with_demod(
                packets=list(pkt_by_id.values()),
                machines=machines,
                P=P_local,
                alpha=alpha,
                H_ms=H_ms,
                max_demod=max_demod,
                candidate_ids=candidate_ids,
            )

            if not deadline_viols and not demod_viols:
                # ---- All clear: build final result ---- #
                result.entries = entries
                result.makespan_ms = max(
                    (e.finish_time for e in entries), default=0
                )
                final_loads = compute_loads(len(candidate_ids), m, P_local, alpha)
                result.machine_makespan_ms = max(final_loads, default=0)
                result.feasible = True
                return result

            # ---- Drop lowest-priority offender ---- #
            offender_locals = deadline_viols if deadline_viols else demod_viols
            offender_pids = [candidate_ids[li] for li in offender_locals]
            victim_id = min(
                offender_pids,
                key=lambda pid: (pkt_by_id[pid].priority, -pkt_by_id[pid].deadline, pid),
            )
            result.add_drop(victim_id)

            victim_idx = candidate_ids.index(victim_id)
            candidate_ids.pop(victim_idx)
            alpha.pop(victim_idx)
            P_local.pop(victim_idx)

        # If all candidates dropped
        result.feasible = False
        return result

    result.feasible = len(result.entries) > 0
    return result

