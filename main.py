#!/usr/bin/env python3
"""
LoRaWAN Hypercycle Scheduler — Main Entry Point

Orchestrates the full simulation pipeline:
  1. Load configuration
  2. Generate machines and packets
  3. Compute ToA matrix
  4. Run the LoRaWAN Hypercycle Scheduler (Algorithm 3)
  5. (Optional) Validate with ILP solver
  6. Validate schedule invariants
  7. Compute statistics
  8. Write output
"""

import sys
import os
import time
import argparse
import json

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config
from packet_generator import create_machines, generate_packets
from lorawan_toa import compute_toa_matrix
from scheduler.lorawan_scheduler import lorawan_hypercycle_scheduler
from validator.invariant_checker import check_schedule_validity, InvariantError
from stats import compute_stats
from output_writer import write_schedule, write_stats


def main():
    parser = argparse.ArgumentParser(
        description="LoRaWAN Hypercycle Scheduler Simulation"
    )
    parser.add_argument(
        "--config", "-c", default="config.json",
        help="Path to configuration JSON file (default: config.json)",
    )
    parser.add_argument(
        "--ilp", action="store_true",
        help="Run ILP optimal solver for comparison (slow for n > 50)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print detailed progress information",
    )
    args = parser.parse_args()

    # ================================================================ #
    # 1. Load Configuration                                            #
    # ================================================================ #
    print("=" * 60)
    print("  LoRaWAN Hypercycle Scheduler Simulation")
    print("=" * 60)

    config = load_config(args.config)
    H_ms = config.network.hypercycle_duration_ms
    max_demod = config.gateway.max_concurrent_demodulations

    print(f"\n[Config]")
    print(f"  Channels       : {config.network.num_channels}")
    print(f"  SFs            : {config.network.spreading_factors}")
    print(f"  Machines (m)   : {config.num_machines}")
    print(f"  Hypercycle (H) : {config.network.hypercycle_duration_s}s "
          f"({H_ms} ms)")
    print(f"  Max demod      : {max_demod}")
    print(f"  ToA mode       : {config.toa_mode}")

    # ================================================================ #
    # 2. Generate Machines and Packets                                  #
    # ================================================================ #
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    n = len(packets)
    m = len(machines)

    print(f"\n[Traffic Generation]")
    print(f"  End devices    : {config.traffic.num_end_devices}")
    print(f"  Total packets  : {n}")
    print(f"  Machines       : {m}")

    if n == 0:
        print("\n  No packets generated. Check config. Exiting.")
        return

    # ================================================================ #
    # 3. Compute ToA Matrix                                            #
    # ================================================================ #
    t0 = time.time()
    P = compute_toa_matrix(packets, machines, config)
    t_toa = time.time() - t0

    # Report ToA range
    finite_toas = [P[i][j] for i in range(n) for j in range(m)
                   if P[i][j] < 10**18]
    if finite_toas:
        print(f"\n[ToA Matrix]  ({n} × {m})")
        print(f"  Min ToA  : {min(finite_toas)} ms")
        print(f"  Max ToA  : {max(finite_toas)} ms")
        print(f"  Mean ToA : {sum(finite_toas)/len(finite_toas):.1f} ms")
        print(f"  Computed in {t_toa:.3f}s")

    if args.verbose:
        # Print ToA per SF (one representative)
        for sf in config.network.spreading_factors:
            toas_for_sf = [
                P[0][j] for j in range(m)
                if machines[j].sf == sf and P[0][j] < 10**18
            ]
            if toas_for_sf:
                print(f"    SF{sf}: {toas_for_sf[0]} ms "
                      f"(payload={packets[0].payload_size}B)")

    # ================================================================ #
    # 4. Run Scheduler                                                  #
    # ================================================================ #
    print(f"\n[Scheduling] Running LoRaWAN Hypercycle Scheduler...")
    t0 = time.time()

    result = lorawan_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        H_ms=H_ms,
        max_demod=max_demod,
        check_invariants=config.validation.check_invariants,
    )

    t_sched = time.time() - t0
    print(f"  Completed in {t_sched:.3f}s")
    print(f"  Feasible     : {result.feasible}")
    print(f"  Scheduled    : {len(result.entries)}/{n}")
    print(f"  Dropped      : {len(result.dropped_packet_ids)}")
    print(f"  Makespan     : {result.makespan_ms} ms")
    print(f"  w* (approx)  : {result.approx_ratio_w}")

    # ================================================================ #
    # 5. Optional ILP Comparison                                        #
    # ================================================================ #
    ilp_opt = None
    run_ilp = args.ilp or config.validation.run_ilp_comparison

    if run_ilp:
        print(f"\n[ILP Solver] Computing optimal makespan (may be slow)...")

        from validator.ilp_solver import ilp_optimal_makespan

        # Use the candidate set that was actually scheduled
        scheduled_ids = {e.packet_id for e in result.entries}
        if scheduled_ids:
            # Active machines that actually support these packets within their deadline
            active_mach_ids = sorted({e.machine_id for e in result.entries})
            m_ilp = len(active_mach_ids)
            id_list = sorted(scheduled_ids)
            n_ilp = len(id_list)
            # Build reduced P for scheduled packets across eligible active machines
            P_ilp = [[P[pid][mid] for mid in active_mach_ids] for pid in id_list]

            if n_ilp <= 200:  # reasonable limit
                t0 = time.time()
                ilp_opt, ilp_alpha = ilp_optimal_makespan(n_ilp, m_ilp, P_ilp, time_limit_s=5)
                t_ilp = time.time() - t0

                if ilp_opt is not None:
                    target_makespan = (
                        result.machine_makespan_ms
                        if result.machine_makespan_ms > 0
                        else result.makespan_ms
                    )
                    ratio = target_makespan / ilp_opt if ilp_opt > 0 else 0
                    print(f"  Exact OPT Makespan  : {ilp_opt} ms")
                    print(f"  2-Approx Load       : {target_makespan} ms")
                    print(f"  Timeline Span       : {result.makespan_ms} ms")
                    print(f"  Ratio (Load / OPT)  : {ratio:.4f}")
                    print(f"  ≤ 2.0 Guarantee     : {'YES' if ratio <= 2.0 + 1e-9 else 'NO'}")
                    print(f"  Solved in           : {t_ilp:.3f}s")
                else:
                    print(f"  ILP solver returned no solution.")
            else:
                print(f"  Skipped: {n_ilp} packets exceeds ILP limit of 200.")

    # ================================================================ #
    # 6. Validate Schedule                                              #
    # ================================================================ #
    if config.validation.check_invariants and result.entries:
        print(f"\n[Validation]")
        try:
            val_info = check_schedule_validity(
                result.entries, machines, H_ms, max_demod,
            )
            print(f"  Per-channel non-preemption : OK")
            print(f"  Deadline compliance        : OK")
            print(f"  Max concurrent demod       : "
                  f"{val_info.get('max_concurrent_demod', val_info.get('max_concurrent', 0))}/{max_demod}")
            print(f"  Demod limit OK             : {val_info['demod_limit_ok']}")
        except InvariantError as e:
            print(f"  VALIDATION FAILED:\n  {e}")

    # ================================================================ #
    # 7. Compute Statistics                                             #
    # ================================================================ #
    sim_stats = compute_stats(
        result=result,
        packets=packets,
        machines=machines,
        P_full=P,
        H_ms=H_ms,
        max_demod=max_demod,
        ilp_opt=ilp_opt,
    )
    sim_stats["timing"] = {
        "toa_computation_s": round(t_toa, 4),
        "scheduling_s": round(t_sched, 4),
    }

    # ================================================================ #
    # 8. Write Output                                                   #
    # ================================================================ #
    print(f"\n[Output]")
    write_schedule(result, config.output.schedule_file)
    write_stats(sim_stats, config.output.stats_file)

    # ---- Console summary ---- #
    print(f"\n{'=' * 60}")
    print(f"  SIMULATION COMPLETE")
    print(f"{'=' * 60}")
    drop_pct = 100.0 * len(result.dropped_packet_ids) / max(n, 1)
    print(f"  Packets: {len(result.entries)} scheduled, "
          f"{len(result.dropped_packet_ids)} dropped ({drop_pct:.1f}%)")
    print(f"  Timeline Span: {result.makespan_ms} ms / {H_ms} ms "
          f"({100.0*result.makespan_ms/max(H_ms,1):.1f}%)")
    print(f"  Machine Load Makespan: {result.machine_makespan_ms} ms")
    if ilp_opt:
        target_makespan = (
            result.machine_makespan_ms
            if result.machine_makespan_ms > 0
            else result.makespan_ms
        )
        print(f"  Approximation ratio: "
              f"{target_makespan/ilp_opt:.4f} (guarantee ≤ 2.0)")
    print()


if __name__ == "__main__":
    main()
