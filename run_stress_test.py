#!/usr/bin/env python3
"""
Stress Test & Worst-Case Benchmark Suite for LoRaWAN Packet Scheduling

Tests the GMW Combinatorial 2-Approximation Algorithm against heuristic baselines:
  - Random Assignment (Pure ALOHA baseline)
  - Greedy Least-Loaded (Graham 1966)
  - Min-Min Heuristic (Ibarra & Kim 1977)
  - Max-Min Heuristic (Ibarra & Kim 1977)

Across 5 comprehensive test suites:
  Suite 1: Scaled LoRaWAN Density (N = 25 to 400 devices, n = 142 to 1840 packets)
  Suite 2: Graham's List-Scheduling Worst-Case (m = 4, 8, 16, 32, 48 machines)
  Suite 3: Min-Min Job Starvation / Bottleneck Contention (unrelated channels)
  Suite 4: Max-Min Machine Heterogeneity Trap (asymmetric SF capabilities)
  Suite 5: Unrelated Machine Adversarial Suite (R || C_max heuristic degradation)

Outputs structured JSON to output/stress_test_results.json and prints summary tables.
"""

import sys
import os
import time
import json
import math
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_structures import INF
from config_loader import load_config
from packet_generator import create_machines, generate_packets
from lorawan_toa import compute_toa_matrix, compute_cost_matrix
from approximation.binary_search import find_2approx_assignment
from approximation.graph_utils import compute_loads
from baselines import run_all_baselines


def solve_instance(P: List[List[int]], m: int, n: int, H_ms: Optional[int] = None) -> Dict[str, Any]:
    """Run 2-approximation and all baselines on an instance matrix P."""
    b = 1.0 + 1.0 / m if m > 0 else 2.0
    C = compute_cost_matrix(P, m)

    # Upper bound for binary search
    if H_ms is None:
        finite_p = [P[i][j] for i in range(n) for j in range(m) if P[i][j] < INF]
        H_ms = sum(max(P[i][j] for j in range(m) if P[i][j] < INF) for i in range(n)) if finite_p else 10000

    # 2-Approximation
    t0 = time.time()
    alpha_2a, w_star = find_2approx_assignment(n, m, P, C, b, H_ms=H_ms)
    t_2a = time.time() - t0
    ms_2a = max(compute_loads(n, m, P, alpha_2a)) if alpha_2a else None

    # Baselines
    t0 = time.time()
    base_res = run_all_baselines(n, m, P)
    t_base = time.time() - t0

    result = {
        "n": n,
        "m": m,
        "w_star": w_star,
        "2_approx": {
            "makespan": ms_2a,
            "ratio_to_w_star": round(ms_2a / w_star, 3) if (ms_2a and w_star > 0) else None,
            "time_s": round(t_2a, 4),
            "feasible": ms_2a is not None,
        },
        "baselines": {}
    }

    for name in ["Greedy Least-Loaded", "Min-Min", "Max-Min", "Random Assignment"]:
        b_data = base_res[name]
        ms = b_data["makespan"]
        feas = b_data["feasible"]
        result["baselines"][name] = {
            "makespan": ms if feas else None,
            "ratio_to_w_star": round(ms / w_star, 3) if (feas and w_star > 0) else None,
            "feasible": feas,
        }

    return result


# ──────────────────────────────────────────────────────────────────────
# Suite Generators
# ──────────────────────────────────────────────────────────────────────

def run_suite_1_lorawan_scale(config_path: str = "config.json") -> List[Dict[str, Any]]:
    """Suite 1: Scaled LoRaWAN Density with 48 machines."""
    config = load_config(config_path)
    suite_results = []
    device_counts = [25, 50, 100, 200, 400]

    for dev_cnt in device_counts:
        config.traffic.num_end_devices = dev_cnt
        machines = create_machines(config)
        packets = generate_packets(config, machines)
        n = len(packets)
        m = len(machines)
        P = compute_toa_matrix(packets, machines, config)
        H_ms = config.network.hypercycle_duration_ms

        res = solve_instance(P, m, n, H_ms=H_ms)
        res["test_name"] = f"LoRaWAN Dense Scale ({dev_cnt} devices)"
        res["devices"] = dev_cnt
        suite_results.append(res)

    return suite_results


def run_suite_2_graham_anomalies() -> List[Dict[str, Any]]:
    """
    Suite 2: Graham (1966) Worst-Case List-Scheduling Instances.
    Identical machines: m*(m-1) jobs of size 1, followed by 1 job of size m.
    Theoretical lower bound for Greedy: (2 - 1/m) * OPT.
    """
    machine_counts = [4, 8, 16, 32, 48]
    suite_results = []

    for m in machine_counts:
        n = m * (m - 1) + 1
        P = [[1] * m for _ in range(n - 1)]
        P.append([m] * m)  # large job

        res = solve_instance(P, m, n, H_ms=m * 4)
        res["test_name"] = f"Graham Anomaly (m={m})"
        res["exact_opt"] = m
        res["graham_bound"] = round(2.0 - 1.0 / m, 3)
        suite_results.append(res)

    return suite_results


def run_suite_3_min_min_starvation() -> List[Dict[str, Any]]:
    """
    Suite 3: Min-Min Job Starvation / Bottleneck Contention.
    Machine 0 is shared/fast for small jobs, but is the ONLY feasible machine
    for several large bottleneck jobs.
    Min-Min floods Machine 0 with small jobs first, leaving large jobs to pile up.
    """
    configs = [
        {"m": 4, "k": 15, "large_sz": 100, "n_large": 3},
        {"m": 6, "k": 20, "large_sz": 150, "n_large": 4},
        {"m": 8, "k": 30, "large_sz": 200, "n_large": 5},
        {"m": 12, "k": 40, "large_sz": 250, "n_large": 6},
    ]
    suite_results = []

    for cfg in configs:
        m, k, l_sz, n_l = cfg["m"], cfg["k"], cfg["large_sz"], cfg["n_large"]
        n_small = (m - 1) * k
        n = n_small + n_l
        P = []

        # Small jobs: arrive first, cost 5 on M0, cost 15 on M_j
        for j in range(1, m):
            for _ in range(k):
                row = [INF] * m
                row[0] = 5
                row[j] = 15
                P.append(row)

        # Large bottleneck jobs: cost l_sz on M0, INF elsewhere
        for _ in range(n_l):
            row = [INF] * m
            row[0] = l_sz
            P.append(row)

        res = solve_instance(P, m, n)
        res["test_name"] = f"Min-Min Bottleneck Starvation (m={m}, n={n})"
        suite_results.append(res)

    return suite_results


def run_suite_4_max_min_traps() -> List[Dict[str, Any]]:
    """
    Suite 4: Max-Min Machine Heterogeneity Trap.
    Asymmetric machine speeds (e.g. SF7 fast channel vs SF12 slow channels).
    Max-Min assigns large jobs to fast machines, pushing subsequent jobs
    into slow machines or starving dedicated channels.
    """
    configs = [
        {"m": 3, "n_large": 4, "n_small": 80, "skew": 10},
        {"m": 4, "n_large": 5, "n_small": 120, "skew": 12},
        {"m": 6, "n_large": 8, "n_small": 200, "skew": 15},
    ]
    suite_results = []

    for cfg in configs:
        m, n_l, n_s, skew = cfg["m"], cfg["n_large"], cfg["n_small"], cfg["skew"]
        P = []
        # Large jobs: 50 on M0, 50 * skew on M1..M_m-1
        for _ in range(n_l):
            P.append([50] + [50 * skew] * (m - 1))
        # Small jobs: 2 on M0, 2 * skew on M1..M_m-1
        for _ in range(n_s):
            P.append([2] + [2 * skew] * (m - 1))

        n = len(P)
        res = solve_instance(P, m, n)
        res["test_name"] = f"Max-Min Heterogeneity Trap (m={m}, n={n}, skew={skew}x)"
        suite_results.append(res)

    return suite_results


def run_suite_5_unrelated_adversarial() -> List[Dict[str, Any]]:
    """
    Suite 5: Unrelated Machines Hard Contention (R || C_max Adversary).
    Restricted machine subsets with coupled channel dependencies where
    myopic greedy heuristics trigger severe cascading overloads.
    """
    configs = [
        {"m": 4, "k": 10},
        {"m": 6, "k": 20},
        {"m": 8, "k": 30},
        {"m": 10, "k": 40},
    ]
    suite_results = []

    for cfg in configs:
        m, k = cfg["m"], cfg["k"]
        P = []
        # Small coupled jobs
        for i in range(1, m):
            for _ in range(k):
                row = [INF] * m
                row[0] = 1
                row[i] = 2
                P.append(row)
        # Dedicated jobs for M0
        for _ in range(k):
            row = [INF] * m
            row[0] = 2
            P.append(row)

        n = len(P)
        res = solve_instance(P, m, n)
        res["test_name"] = f"Unrelated Machine Contention (m={m}, n={n})"
        suite_results.append(res)

    return suite_results


# ──────────────────────────────────────────────────────────────────────
# Main Runner & Formatter
# ──────────────────────────────────────────────────────────────────────

def print_suite_table(title: str, results: List[Dict[str, Any]]):
    print(f"\n{'='*90}")
    print(f"  {title}")
    print(f"{'='*90}")
    hdr = f"{'Instance / Configuration':<36} {'w* (ms)':>8} {'2-Approx':>10} {'Greedy LL':>11} {'Min-Min':>10} {'Max-Min':>10} {'Random':>10}"
    print(hdr)
    print("─" * len(hdr))

    for r in results:
        tname = r["test_name"]
        w_star = r["w_star"]
        a2 = r["2_approx"]
        a2_str = f"{a2['makespan']} ({a2['ratio_to_w_star']:.2f}x)" if a2["feasible"] else "FAIL"

        b = r["baselines"]
        gll = b["Greedy Least-Loaded"]
        gll_str = f"{gll['makespan']} ({gll['ratio_to_w_star']:.2f}x)" if gll["feasible"] else "FAIL"

        mmin = b["Min-Min"]
        mmin_str = f"{mmin['makespan']} ({mmin['ratio_to_w_star']:.2f}x)" if mmin["feasible"] else "FAIL"

        mmax = b["Max-Min"]
        mmax_str = f"{mmax['makespan']} ({mmax['ratio_to_w_star']:.2f}x)" if mmax["feasible"] else "FAIL"

        rnd = b["Random Assignment"]
        rnd_str = f"{rnd['makespan']} ({rnd['ratio_to_w_star']:.1f}x)" if rnd["feasible"] else "FAIL"

        print(f"{tname:<36} {w_star:>8} {a2_str:>10} {gll_str:>11} {mmin_str:>10} {mmax_str:>10} {rnd_str:>10}")


def main():
    print("=" * 90)
    print("  MULTIPLE INPUT STRESS TESTING — ALGORITHM WORST-CASE EVALUATION")
    print("=" * 90)

    all_data = {}

    print("\n[1/5] Running Suite 1: Scaled LoRaWAN Density...")
    s1 = run_suite_1_lorawan_scale()
    print_suite_table("SUITE 1: SCALED LORAWAN NETWORK DENSITY", s1)
    all_data["suite_1_lorawan_scale"] = s1

    print("\n[2/5] Running Suite 2: Graham's List-Scheduling Worst-Case...")
    s2 = run_suite_2_graham_anomalies()
    print_suite_table("SUITE 2: GRAHAM (1966) LIST-SCHEDULING ANOMALY (Identical Machines)", s2)
    all_data["suite_2_graham_anomalies"] = s2

    print("\n[3/5] Running Suite 3: Min-Min Job Starvation / Bottleneck...")
    s3 = run_suite_3_min_min_starvation()
    print_suite_table("SUITE 3: MIN-MIN JOB STARVATION & BOTTLENECK CONTENTION", s3)
    all_data["suite_3_min_min_starvation"] = s3

    print("\n[4/5] Running Suite 4: Max-Min Machine Heterogeneity Trap...")
    s4 = run_suite_4_max_min_traps()
    print_suite_table("SUITE 4: MAX-MIN HETEROGENEITY TRAP (SF7 vs SF12 Skew)", s4)
    all_data["suite_4_max_min_traps"] = s4

    print("\n[5/5] Running Suite 5: Unrelated Machine Contention...")
    s5 = run_suite_5_unrelated_adversarial()
    print_suite_table("SUITE 5: UNRELATED MACHINE CONTENTION (R || C_max Adversary)", s5)
    all_data["suite_5_unrelated_adversarial"] = s5

    # Save to JSON
    os.makedirs("output", exist_ok=True)
    out_path = "output/stress_test_results.json"
    with open(out_path, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n{'='*90}")
    print(f"  All stress tests complete! Results saved to {out_path}")
    print(f"{'='*90}\n")


if __name__ == "__main__":
    main()
