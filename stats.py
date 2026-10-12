"""
Simulation statistics computation.

Computes per-SF, per-channel, and aggregate metrics from the schedule.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from data_structures import Packet, Machine, ScheduleEntry, ScheduleResult


def compute_stats(
    result: ScheduleResult,
    packets: List[Packet],
    machines: List[Machine],
    P_full: List[List[int]],
    H_ms: int,
    max_demod: int,
    ilp_opt: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute comprehensive simulation statistics.

    Returns a dict ready for JSON serialisation.
    """
    m = len(machines)
    n_total = len(packets)
    n_scheduled = len(result.entries)
    n_dropped = len(result.dropped_packet_ids)

    stats: Dict[str, Any] = {}

    # ---- Summary ---- #
    stats["summary"] = {
        "total_packets": n_total,
        "scheduled_packets": n_scheduled,
        "dropped_packets": n_dropped,
        "drop_rate_pct": round(100.0 * n_dropped / max(n_total, 1), 2),
        "makespan_ms": result.makespan_ms,
        "machine_makespan_ms": result.machine_makespan_ms,
        "hypercycle_ms": H_ms,
        "makespan_utilisation_pct": round(
            100.0 * result.makespan_ms / max(H_ms, 1), 2
        ),
        "approx_w_star": result.approx_ratio_w,
        "feasible": result.feasible,
    }

    # ---- ILP / OPT comparison ---- #
    if ilp_opt is not None:
        target_makespan = (
            result.machine_makespan_ms
            if result.machine_makespan_ms > 0
            else result.makespan_ms
        )
        approx_ratio = (
            target_makespan / ilp_opt if ilp_opt > 0 else float("inf")
        )
        stats["ilp_comparison"] = {
            "ilp_optimal_makespan_ms": ilp_opt,
            "approx_machine_makespan_ms": target_makespan,
            "timeline_makespan_ms": result.makespan_ms,
            "empirical_approx_ratio": round(approx_ratio, 4),
            "within_2x_guarantee": approx_ratio <= 2.0 + 1e-9,
        }

    # ---- Per-SF load distribution ---- #
    sf_loads: Dict[int, int] = defaultdict(int)
    sf_counts: Dict[int, int] = defaultdict(int)
    for e in result.entries:
        sf_loads[e.sf] += (e.finish_time - e.start_time)
        sf_counts[e.sf] += 1

    stats["per_sf"] = {
        sf: {
            "num_packets": sf_counts.get(sf, 0),
            "total_airtime_ms": sf_loads.get(sf, 0),
            "avg_toa_ms": round(
                sf_loads.get(sf, 0) / max(sf_counts.get(sf, 0), 1), 1
            ),
        }
        for sf in sorted(set(mach.sf for mach in machines))
    }

    # ---- Per-channel utilisation ---- #
    ch_loads: Dict[int, int] = defaultdict(int)
    ch_counts: Dict[int, int] = defaultdict(int)
    for e in result.entries:
        ch_loads[e.channel] += (e.finish_time - e.start_time)
        ch_counts[e.channel] += 1

    stats["per_channel"] = {
        ch: {
            "num_packets": ch_counts.get(ch, 0),
            "total_airtime_ms": ch_loads.get(ch, 0),
            "utilisation_pct": round(
                100.0 * ch_loads.get(ch, 0) / max(H_ms, 1), 2
            ),
        }
        for ch in sorted(set(mach.channel for mach in machines))
    }

    # ---- Per-machine load ---- #
    mach_loads: Dict[int, int] = defaultdict(int)
    mach_counts: Dict[int, int] = defaultdict(int)
    for e in result.entries:
        mach_loads[e.machine_id] += (e.finish_time - e.start_time)
        mach_counts[e.machine_id] += 1

    stats["per_machine"] = {
        machines[mid].label: {
            "machine_id": mid,
            "num_packets": mach_counts.get(mid, 0),
            "total_airtime_ms": mach_loads.get(mid, 0),
            "utilisation_pct": round(
                100.0 * mach_loads.get(mid, 0) / max(H_ms, 1), 2
            ),
        }
        for mid in range(m)
    }

    # ---- Concurrent demodulation profile ---- #
    if result.entries:
        events = []
        for e in result.entries:
            events.append((e.start_time, +1))
            events.append((e.finish_time, -1))
        events.sort(key=lambda x: (x[0], x[1]))

        concurrent = 0
        max_concurrent = 0
        for _, delta in events:
            concurrent += delta
            max_concurrent = max(max_concurrent, concurrent)

        stats["demod_profile"] = {
            "max_concurrent": max_concurrent,
            "limit": max_demod,
            "within_limit": max_concurrent <= max_demod,
        }
    else:
        stats["demod_profile"] = {
            "max_concurrent": 0,
            "limit": max_demod,
            "within_limit": True,
        }

    # ---- Dropped packets detail ---- #
    pkt_by_id = {pkt.id: pkt for pkt in packets}
    stats["dropped_packets_detail"] = [
        {
            "packet_id": pid,
            "device_id": pkt_by_id[pid].device_id,
            "priority": pkt_by_id[pid].priority,
            "release_time_ms": pkt_by_id[pid].release_time,
            "deadline_ms": pkt_by_id[pid].deadline,
        }
        for pid in result.dropped_packet_ids
        if pid in pkt_by_id
    ]

    return stats
