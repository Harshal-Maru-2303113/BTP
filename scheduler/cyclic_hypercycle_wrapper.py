"""
Cyclic Executive Wrapper with Inter-Cycle Carryover Buffer.

Implements a hierarchical multi-cycle executive for periodic LoRaWAN traffic:
  - Major Hypercycle: H (e.g. 100s) = lcm(T_k), the master macro-horizon.
  - Minor Cycles: tau (e.g. 10s), the operational dispatch frames (H = K * tau).
  - Carryover Buffer: Packets dropped in minor cycle k due to transient capacity
    or demodulation congestion are deferred to cycle k+1 if their remaining
    slack allows (D_i >= (k+1)*tau + min_j P_ij).
  - Priority Boosting: Deferred packets receive priority escalation to prevent
    starvation while strictly bounding jitter within their period D_i = r_i + T_i.

In every minor cycle k, the 2-approximation guarantee C_max^(k) <= 2 * OPT_k
and the energy minimization invariant delta_j^(k) <= 2 * w_k* hold unconditionally.
"""

from typing import List, Dict, Tuple, Optional, Set
import copy

from data_structures import (
    Packet, Machine, ScheduleEntry, ScheduleResult, CyclicScheduleResult, INF,
)
from config_loader import SimConfig
from scheduler.lorawan_scheduler import lorawan_hypercycle_scheduler
from validator.invariant_checker import check_schedule_validity


def run_cyclic_hypercycle_scheduler(
    packets: List[Packet],
    machines: List[Machine],
    P_full: List[List[int]],
    config: SimConfig,
    E_full: Optional[List[List[float]]] = None,
    check_invariants: bool = False,
    enable_energy_opt: bool = True,
) -> CyclicScheduleResult:
    """
    Executes the Cyclic Executive scheduling framework over hypercycle [0, H).

    Parameters
    ----------
    packets : list[Packet]
        All packet instances generated for the hypercycle.
    machines : list[Machine]
        All available (SF, Channel) communication machines.
    P_full : list[list[int]]
        ToA matrix for all packets and machines (P_full[pkt.id][mach.id]).
    config : SimConfig
        Simulation configuration containing network, cyclic_executive, and energy settings.
    E_full : list[list[float]], optional
        Energy consumption matrix (E_full[pkt.id][mach.id] in mJ).
    check_invariants : bool
        Whether to run post-schedule invariant validation.
    enable_energy_opt : bool
        Whether to enable Phase 1.5 energy downshifting in each minor cycle.

    Returns
    -------
    CyclicScheduleResult
        Aggregated schedule result containing global entries, recovered packets,
        unrecoverable drops, per-cycle statistics, and energy metrics.
    """
    H_ms = config.network.hypercycle_duration_ms
    cyclic_cfg = config.cyclic_executive

    # Determine minor cycle durations: supports both homogeneous (uniform) and heterogeneous (variable-length) frames
    if cyclic_cfg.minor_cycle_durations_ms:
        cycle_durations_ms = [int(d) for d in cyclic_cfg.minor_cycle_durations_ms]
        if any(d <= 0 for d in cycle_durations_ms):
            raise ValueError(f"All minor cycle durations must be positive: {cycle_durations_ms}")
        if sum(cycle_durations_ms) != H_ms:
            raise ValueError(
                f"Sum of heterogeneous minor cycle durations ({sum(cycle_durations_ms)} ms) "
                f"must equal hypercycle duration H={H_ms} ms."
            )
        is_homogeneous = len(set(cycle_durations_ms)) == 1
    else:
        tau_ms = cyclic_cfg.minor_cycle_duration_ms
        if tau_ms <= 0:
            raise ValueError(f"Minor cycle duration tau_ms={tau_ms} must be positive.")
        if H_ms % tau_ms != 0:
            raise ValueError(
                f"Hypercycle duration H={H_ms} ms must be an integer multiple of "
                f"minor cycle duration tau={tau_ms} ms (H % tau = {H_ms % tau_ms})."
            )
        cycle_durations_ms = [tau_ms] * (H_ms // tau_ms)
        is_homogeneous = True

    num_cycles = len(cycle_durations_ms)

    # Compute execution window [t_start, t_end) for each minor cycle
    cycle_windows: List[Tuple[int, int]] = []
    cur_t = 0
    for dur in cycle_durations_ms:
        cycle_windows.append((cur_t, cur_t + dur))
        cur_t += dur

    max_demod = config.gateway.max_concurrent_demodulations
    enable_carryover = cyclic_cfg.enable_packet_carryover
    max_hops = cyclic_cfg.max_carryover_cycles
    priority_boost = cyclic_cfg.carryover_priority_boost

    pkt_by_id: Dict[int, Packet] = {pkt.id: pkt for pkt in packets}
    m = len(machines)

    # Precompute minimum feasible ToA for each packet across all machines
    min_toa_by_id: Dict[int, int] = {}
    for pkt in packets:
        feasible_toas = [P_full[pkt.id][j] for j in range(m) if P_full[pkt.id][j] < INF]
        min_toa_by_id[pkt.id] = min(feasible_toas) if feasible_toas else INF

    # Partition newly arriving packets into minor cycles by release time window
    cycle_arrivals: List[List[Packet]] = [[] for _ in range(num_cycles)]
    for pkt in packets:
        rel = pkt.release_time
        placed_cycle = -1
        for k, (w_start, w_end) in enumerate(cycle_windows):
            if w_start <= rel < w_end:
                placed_cycle = k
                break
        if placed_cycle == -1:
            if rel >= H_ms:
                placed_cycle = num_cycles - 1  # Boundary clamp to final cycle
            else:
                placed_cycle = 0
        cycle_arrivals[placed_cycle].append(pkt)

    # Carryover buffer: map packet_id -> current_hops
    carryover_buffer: Dict[int, int] = {}

    all_entries: List[ScheduleEntry] = []
    recovered_packet_ids: List[int] = []
    unrecoverable_dropped_ids: List[int] = []
    cycle_results: List[dict] = []

    # Iterate through minor cycles (uniform or variable-length)
    for k, (t_start, t_end) in enumerate(cycle_windows):
        tau_k = t_end - t_start

        # 1. Prune carryover buffer: check for expired deadlines or hop limits
        eligible_carryover_pids: List[int] = []
        for pid, hops in list(carryover_buffer.items()):
            p = pkt_by_id[pid]
            earliest_completion = t_start + min_toa_by_id[pid]

            if earliest_completion > p.deadline:
                # Unrecoverable deadline miss
                unrecoverable_dropped_ids.append(pid)
                del carryover_buffer[pid]
            elif hops >= max_hops:
                # Exceeded carryover hop ceiling
                unrecoverable_dropped_ids.append(pid)
                del carryover_buffer[pid]
            else:
                eligible_carryover_pids.append(pid)

        # 2. Assemble candidate set for cycle k
        local_candidates: List[Packet] = []

        # (a) New arrivals
        for p in cycle_arrivals[k]:
            local_rel = max(0, p.release_time - t_start)
            local_dead = max(1, min(tau_k, p.deadline - t_start))
            local_candidates.append(Packet(
                id=p.id,
                release_time=local_rel,
                deadline=local_dead,
                priority=p.priority,
                payload_size=p.payload_size,
                device_id=p.device_id,
                period=p.period,
            ))

        # (b) Eligible carryover packets (with priority escalation)
        for pid in eligible_carryover_pids:
            p = pkt_by_id[pid]
            hops = carryover_buffer[pid]
            boosted_priority = p.priority + hops * priority_boost
            local_dead = max(1, min(tau_k, p.deadline - t_start))
            local_candidates.append(Packet(
                id=p.id,
                release_time=0,  # Available immediately at cycle start
                deadline=local_dead,
                priority=boosted_priority,
                payload_size=p.payload_size,
                device_id=p.device_id,
                period=p.period,
            ))

        # 3. Schedule the minor cycle using Algorithm 3 (2-Approx + Energy Opt + Demod EDF)
        if not local_candidates:
            cycle_results.append({
                "cycle_index": k,
                "duration_ms": tau_k,
                "t_start_ms": t_start,
                "t_end_ms": t_end,
                "num_arrivals": 0,
                "num_carried_in": 0,
                "num_scheduled": 0,
                "num_recovered": 0,
                "num_dropped": 0,
                "makespan_ms": 0,
                "machine_makespan_ms": 0,
                "w_star_ms": 0,
                "energy_mj": 0.0,
            })
            continue

        local_res = lorawan_hypercycle_scheduler(
            packets=local_candidates,
            machines=machines,
            P_full=P_full,
            H_ms=tau_k,
            max_demod=max_demod,
            check_invariants=check_invariants,
            E_full=E_full,
            enable_energy_opt=enable_energy_opt,
        )

        # 4. Map scheduled entries back to global timeline [t_start, t_end)
        scheduled_in_cycle: Set[int] = set()
        recovered_in_cycle = 0

        for entry in local_res.entries:
            global_start = entry.start_time + t_start
            global_finish = entry.finish_time + t_start
            orig_p = pkt_by_id[entry.packet_id]
            is_met = global_finish <= orig_p.deadline

            all_entries.append(ScheduleEntry(
                packet_id=entry.packet_id,
                machine_id=entry.machine_id,
                start_time=global_start,
                finish_time=global_finish,
                deadline=orig_p.deadline,
                deadline_met=is_met,
                sf=entry.sf,
                channel=entry.channel,
            ))

            scheduled_in_cycle.add(entry.packet_id)

            if entry.packet_id in carryover_buffer:
                # Packet was previously dropped and has now been rescued!
                recovered_packet_ids.append(entry.packet_id)
                recovered_in_cycle += 1
                del carryover_buffer[entry.packet_id]

        # 5. Handle dropped candidates in cycle k
        cycle_drops = 0
        for dropped_pid in local_res.dropped_packet_ids:
            cycle_drops += 1
            if not enable_carryover:
                unrecoverable_dropped_ids.append(dropped_pid)
                continue

            current_hops = carryover_buffer.get(dropped_pid, 0)
            next_t_start = t_end
            p = pkt_by_id[dropped_pid]
            earliest_next_finish = next_t_start + min_toa_by_id[dropped_pid]

            # Viability check for the next cycle
            if (earliest_next_finish <= p.deadline) and (current_hops + 1 <= max_hops) and (next_t_start < H_ms):
                carryover_buffer[dropped_pid] = current_hops + 1
            else:
                unrecoverable_dropped_ids.append(dropped_pid)
                if dropped_pid in carryover_buffer:
                    del carryover_buffer[dropped_pid]

        cycle_energy_mj = 0.0
        if E_full is not None:
            cycle_energy_mj = sum(
                E_full[e.packet_id][e.machine_id]
                for e in local_res.entries
                if 0 <= e.machine_id < m and E_full[e.packet_id][e.machine_id] < INF
            )

        cycle_results.append({
            "cycle_index": k,
            "t_start_ms": t_start,
            "t_end_ms": t_end,
            "num_arrivals": len(cycle_arrivals[k]),
            "num_carried_in": len(eligible_carryover_pids),
            "num_scheduled": len(local_res.entries),
            "num_recovered": recovered_in_cycle,
            "num_dropped": cycle_drops,
            "makespan_ms": local_res.makespan_ms,
            "machine_makespan_ms": local_res.machine_makespan_ms,
            "w_star_ms": local_res.approx_ratio_w,
            "energy_mj": round(cycle_energy_mj, 3),
        })

    # Flush any remaining unserviced packets in carryover buffer at hypercycle end
    for pid in list(carryover_buffer.keys()):
        unrecoverable_dropped_ids.append(pid)
    carryover_buffer.clear()

    # Calculate overall energy metrics
    total_energy_mj = 0.0
    if E_full is not None:
        total_energy_mj = sum(
            E_full[e.packet_id][e.machine_id]
            for e in all_entries
            if 0 <= e.machine_id < m and E_full[e.packet_id][e.machine_id] < INF
        )

    # Sort final global entries by start_time
    all_entries.sort(key=lambda e: (e.start_time, e.machine_id))

    global_makespan_ms = max((e.finish_time for e in all_entries), default=0)

    # Construct final CyclicScheduleResult
    result = CyclicScheduleResult(
        entries=all_entries,
        dropped_packet_ids=list(set(unrecoverable_dropped_ids)),
        makespan_ms=global_makespan_ms,
        machine_makespan_ms=max((c["machine_makespan_ms"] for c in cycle_results), default=0),
        approx_ratio_w=max((c["w_star_ms"] for c in cycle_results), default=0),
        feasible=(len(all_entries) > 0 or len(packets) == 0),
        energy_stats={
            "scheduled_energy_mj": round(total_energy_mj, 3),
            "per_cycle_energy_mj": [c["energy_mj"] for c in cycle_results],
        },
        recovered_packet_ids=list(set(recovered_packet_ids)),
        unrecoverable_dropped_ids=list(set(unrecoverable_dropped_ids)),
        cycle_results=cycle_results,
        num_minor_cycles=num_cycles,
        minor_cycle_ms=cycle_durations_ms[0] if is_homogeneous else 0,
        minor_cycle_durations_ms=cycle_durations_ms,
        is_homogeneous=is_homogeneous,
        carryover_stats={
            "total_packets": len(packets),
            "scheduled_count": len(all_entries),
            "recovered_count": len(recovered_packet_ids),
            "unrecoverable_drop_count": len(set(unrecoverable_dropped_ids)),
            "recovery_rate_pct": round(
                100.0 * len(recovered_packet_ids) / max(1, len(recovered_packet_ids) + len(unrecoverable_dropped_ids)),
                2,
            ) if (len(recovered_packet_ids) + len(unrecoverable_dropped_ids)) > 0 else 100.0,
        },
    )

    if check_invariants and all_entries:
        check_schedule_validity(all_entries, machines, H_ms, max_demod)

    return result
