#!/usr/bin/env python3
"""
Baseline Comparison Runner

Runs all four baseline algorithms and the 2-approximation algorithm on the
same LoRaWAN scheduling instance, computes metrics, and prints a comparison
table. Optionally runs the ILP solver for the exact optimum.

Usage:
    python run_baseline_comparison.py [--ilp] [--config config.json]
"""

import sys
import os
import time
import argparse
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config
from packet_generator import create_machines, generate_packets
from lorawan_toa import compute_toa_matrix, compute_cost_matrix
from lorawan_energy import compute_energy_matrix
from approximation.binary_search import find_2approx_assignment
from scheduler.energy_optimizer import energy_optimal_downshift
from approximation.graph_utils import compute_loads
from baselines import run_all_baselines, ALL_BASELINES
from data_structures import INF


def main():
    parser = argparse.ArgumentParser(description="Baseline Comparison Runner")
    parser.add_argument("--config", "-c", default="config.json")
    parser.add_argument("--ilp", action="store_true", help="Run ILP for exact OPT")
    parser.add_argument("--multi", action="store_true",
                        help="Run multiple instance sizes for scalability")
    args = parser.parse_args()

    config = load_config(args.config)

    print("=" * 72)
    print("  BASELINE COMPARISON — LoRaWAN Hypercycle Scheduler")
    print("=" * 72)

    # ── Generate instance ─────────────────────────────────────────────
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    n = len(packets)
    m = len(machines)

    P = compute_toa_matrix(packets, machines, config)
    C = compute_cost_matrix(P, m)
    E = compute_energy_matrix(packets, machines, config, P)
    b = 1.0 + 1.0 / m if m > 0 else 2.0
    H_ms = config.network.hypercycle_duration_ms

    print(f"\n  Instance: n={n} packets, m={m} machines")
    print(f"  Hypercycle: {H_ms} ms")

    finite_toas = [P[i][j] for i in range(n) for j in range(m) if P[i][j] < INF]
    if finite_toas:
        print(f"  ToA range: [{min(finite_toas)}, {max(finite_toas)}] ms")
        print(f"  Mean ToA:  {sum(finite_toas)/len(finite_toas):.1f} ms")

    # ── Run 2-Approximation (our algorithm) ───────────────────────────
    print(f"\n{'─'*72}")
    print(f"  Running 2-Approximation (Gairing–Monien–Woclaw + Phase 1.5 Energy Opt)...")
    t0 = time.time()
    alpha_2approx, w_star = find_2approx_assignment(n, m, P, C, b, H_ms=H_ms)
    if alpha_2approx is not None and getattr(config.energy, "enable_energy_optimization", True):
        alpha_2approx, energy_stats = energy_optimal_downshift(
            n, m, P, E, alpha_2approx, w_star, machines, H_ms=H_ms
        )
    t_2approx = time.time() - t0

    if alpha_2approx is not None:
        makespan_2approx = max(compute_loads(n, m, P, alpha_2approx))
        energy_2approx = sum(E[i][alpha_2approx[i]] for i in range(n) if E[i][alpha_2approx[i]] < INF)
    else:
        makespan_2approx = None
        energy_2approx = None

    print(f"  Makespan: {makespan_2approx} ms   w*={w_star}   Time: {t_2approx:.4f}s")

    # ── Run all baselines ─────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  Running baseline algorithms...\n")

    baseline_results = {}
    for name in ALL_BASELINES:
        t0 = time.time()
        if name == "Random Assignment":
            from baselines import random_assignment
            alpha, makespan = random_assignment(n, m, P, seed=42)
            # Also run 10 random seeds and take average
            random_makespans = []
            for seed in range(10):
                a, ms = random_assignment(n, m, P, seed=seed)
                if a is not None:
                    random_makespans.append(ms)
        elif name == "Greedy Least-Loaded":
            from baselines import greedy_least_loaded
            alpha, makespan = greedy_least_loaded(n, m, P)
            random_makespans = None
        elif name == "Min-Min":
            from baselines import min_min
            alpha, makespan = min_min(n, m, P)
            random_makespans = None
        elif name == "Max-Min":
            from baselines import max_min
            alpha, makespan = max_min(n, m, P)
            random_makespans = None

        elapsed = time.time() - t0
        baseline_results[name] = {
            "alpha": alpha,
            "makespan": makespan,
            "feasible": alpha is not None,
            "time_s": elapsed,
            "random_makespans": random_makespans,
        }
        if alpha is not None:
            loads = [0] * m
            for i in range(n):
                loads[alpha[i]] += P[i][alpha[i]]
            used_machines = sum(1 for l in loads if l > 0)
            max_load = max(loads)
            min_load = min(l for l in loads if l > 0) if used_machines > 0 else 0
            baseline_results[name]["used_machines"] = used_machines
            baseline_results[name]["max_load"] = max_load
            baseline_results[name]["min_nonzero_load"] = min_load
            baseline_results[name]["energy_mj"] = sum(
                E[i][alpha[i]] for i in range(n) if E[i][alpha[i]] < INF
            )

    # ── Optional ILP ──────────────────────────────────────────────────
    ilp_opt = None
    if args.ilp:
        print(f"{'─'*72}")
        print(f"  Running ILP solver for exact OPT...")
        try:
            from validator.ilp_solver import ilp_optimal_makespan
            t0 = time.time()
            ilp_opt, _ = ilp_optimal_makespan(n, m, P, time_limit_s=30)
            t_ilp = time.time() - t0
            print(f"  Exact OPT: {ilp_opt} ms   Time: {t_ilp:.3f}s")
        except Exception as e:
            print(f"  ILP failed: {e}")

    # ── Print comparison table ────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  COMPARISON RESULTS")
    print(f"{'='*72}\n")

    # Header
    if ilp_opt:
        header = f"{'Algorithm':<28} {'Makespan (ms)':>14} {'Ratio (w*)':>12} {'vs OPT':>10} {'Time (s)':>10}"
    else:
        header = f"{'Algorithm':<28} {'Makespan (ms)':>14} {'Ratio (w*)':>12} {'Time (s)':>10}"
    print(header)
    print("─" * len(header))

    # Reference: OPT
    if ilp_opt:
        print(f"{'Exact OPT (ILP)':.<28} {ilp_opt:>14} {'1.000':>12} {'1.000':>10} {'—':>10}")

    # Our algorithm
    if makespan_2approx is not None:
        ratio_str = f"{makespan_2approx / w_star:.3f}" if w_star > 0 else "—"
        if ilp_opt:
            opt_str = f"{makespan_2approx / ilp_opt:.4f}"
            print(f"{'★ 2-Approx (Ours)':.<28} {makespan_2approx:>14} {ratio_str:>12} {opt_str:>10} {t_2approx:>10.4f}")
        else:
            print(f"{'★ 2-Approx (Ours)':.<28} {makespan_2approx:>14} {ratio_str:>12} {t_2approx:>10.4f}")
    else:
        print(f"{'★ 2-Approx (Ours)':.<28} {'INFEASIBLE':>14}")

    # Baselines
    for name in ["Min-Min", "Max-Min", "Greedy Least-Loaded", "Random Assignment"]:
        res = baseline_results[name]
        if res["feasible"]:
            ms = res["makespan"]
            ratio = ms / w_star if w_star > 0 else 0
            ratio_str = f"{ratio:.3f}"
            time_str = f"{res['time_s']:.4f}"
            extra = ""
            if name == "Random Assignment" and res.get("random_makespans"):
                avg_ms = sum(res["random_makespans"]) / len(res["random_makespans"])
                extra = f"  (avg 10 seeds: {avg_ms:.0f} ms)"
            if ilp_opt:
                opt_str = f"{ms / ilp_opt:.4f}"
                print(f"{'  ' + name:.<28} {ms:>14} {ratio_str:>12} {opt_str:>10} {time_str:>10}{extra}")
            else:
                print(f"{'  ' + name:.<28} {ms:>14} {ratio_str:>12} {time_str:>10}{extra}")
        else:
            print(f"{'  ' + name:.<28} {'INFEASIBLE':>14}")

    # ── Energy Comparison Table ───────────────────────────────────────
    if energy_2approx is not None:
        print(f"\n{'='*72}")
        print(f"  RADIO ENERGY CONSUMPTION (Casals et al. 2017)")
        print(f"{'='*72}\n")
        e_header = f"{'Algorithm':<28} {'Energy (mJ)':>14} {'Avg mJ/pkt':>12} {'vs 2-Approx':>14}"
        print(e_header)
        print("─" * len(e_header))
        print(f"{'★ 2-Approx (Phase 1.5)':.<28} {energy_2approx:>14.1f} {energy_2approx/n:>12.1f} {'1.00× (base)':>14}")

        for name in ["Min-Min", "Max-Min", "Greedy Least-Loaded", "Random Assignment"]:
            res = baseline_results[name]
            if res.get("energy_mj") is not None:
                e_val = res["energy_mj"]
                ratio_e = e_val / energy_2approx
                print(f"{'  ' + name:.<28} {e_val:>14.1f} {e_val/n:>12.1f} {f'{ratio_e:.2f}× (+{(ratio_e-1)*100:.1f}%)':>14}")

    # ── Improvement summary ───────────────────────────────────────────
    if makespan_2approx is not None:
        print(f"\n{'─'*72}")
        print(f"  IMPROVEMENT OF 2-APPROX OVER BASELINES")
        print(f"{'─'*72}")
        for name in ["Min-Min", "Max-Min", "Greedy Least-Loaded", "Random Assignment"]:
            res = baseline_results[name]
            if res["feasible"] and res["makespan"] > 0:
                improvement = (res["makespan"] - makespan_2approx) / res["makespan"] * 100
                speedup = res["makespan"] / makespan_2approx
                print(f"  vs {name:.<26} {improvement:>6.1f}% better   ({speedup:.2f}× lower makespan)")

    # ── Save results to JSON ──────────────────────────────────────────
    output = {
        "instance": {"n": n, "m": m, "H_ms": H_ms},
        "algorithms": {},
    }
    if ilp_opt:
        output["exact_opt_ms"] = ilp_opt

    if makespan_2approx is not None:
        output["algorithms"]["2-Approx (Ours)"] = {
            "makespan_ms": makespan_2approx,
            "w_star": w_star,
            "time_s": round(t_2approx, 4),
            "ratio_to_opt": round(makespan_2approx / ilp_opt, 4) if ilp_opt else None,
            "guarantee": "≤ 2.0",
        }

    for name, res in baseline_results.items():
        output["algorithms"][name] = {
            "makespan_ms": res["makespan"] if res["feasible"] else None,
            "time_s": round(res.get("time_s", 0), 4),
            "ratio_to_opt": round(res["makespan"] / ilp_opt, 4) if (ilp_opt and res["feasible"]) else None,
            "guarantee": "None",
        }
        if name == "Random Assignment" and res.get("random_makespans"):
            output["algorithms"][name]["avg_makespan_10seeds"] = round(
                sum(res["random_makespans"]) / len(res["random_makespans"]), 1
            )

    os.makedirs("output", exist_ok=True)
    with open("output/baseline_comparison.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to output/baseline_comparison.json")

    print(f"\n{'='*72}")
    print(f"  COMPARISON COMPLETE")
    print(f"{'='*72}\n")


if __name__ == "__main__":
    main()
