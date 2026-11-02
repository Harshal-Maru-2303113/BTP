#!/usr/bin/env python3
"""
Large-Scale Simulation Runner for LoRaWAN R||C_max Scheduling

Simulates all 5 scheduling algorithms across problem sizes n in [100, 10000].
For each n, runs 10 independent trials with varied random seeds, computing
the average and standard deviation of makespan, ratio to w*, and runtime.

Outputs:
  - output/large_scale_simulation.json: Complete raw and aggregated statistics
  - Generation of publication-quality comparative scaling plots
"""

import os
import sys
import time
import math
import json
import random
import argparse
import multiprocessing as mp
from typing import Dict, List, Any, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_structures import INF
from lorawan_toa import compute_toa_ms, compute_cost_matrix
from approximation.binary_search import find_2approx_assignment
from approximation.graph_utils import compute_loads
from baselines import (
    random_assignment,
    greedy_least_loaded,
    min_min,
    max_min,
)

# Standard LoRaWAN parameters (EU868 / US915 compliant)
CHANNELS = list(range(8))
SPREADING_FACTORS = [7, 8, 9, 10, 11, 12]
PAYLOAD_SIZES = [20, 50, 100, 200]
BANDWIDTH_HZ = 125000

# Precompute physical ToA table for fast instance construction
TOA_TABLE = {
    (L, sf): max(1, int(math.ceil(compute_toa_ms(L, sf, BANDWIDTH_HZ))))
    for L in PAYLOAD_SIZES
    for sf in SPREADING_FACTORS
}

# Machine layout: 8 channels x 6 SFs = 48 machines
MACHINES = [(ch, sf) for ch in CHANNELS for sf in SPREADING_FACTORS]
NUM_MACHINES = len(MACHINES)


def generate_instance(n: int, seed: int) -> List[List[int]]:
    """
    Generate an n x m LoRaWAN ToA matrix P with realistic heterogeneous devices.

    Each device has:
      - Random payload size from [20, 50, 100, 200] bytes
      - Path-loss-dependent minimum SF (devices further from gateway require higher SF)
    """
    rng = random.Random(seed)
    P = []
    for _ in range(n):
        L = rng.choice(PAYLOAD_SIZES)
        # Device link margin: closer nodes can reach SF7; edge nodes require SF9+
        min_sf = rng.choice([7, 7, 7, 8, 8, 9, 10])
        row = [
            TOA_TABLE[(L, sf)] if sf >= min_sf else INF
            for (ch, sf) in MACHINES
        ]
        P.append(row)
    return P


def evaluate_trial(args: Tuple[int, int, int]) -> Dict[str, Any]:
    """
    Execute 1 simulation trial for a given n and seed across all 5 algorithms.
    """
    n, seed, run_idx = args
    m = NUM_MACHINES
    P = generate_instance(n, seed)
    C = compute_cost_matrix(P, m)
    b = 1.0 + 1.0 / m

    trial_result = {
        "n": n,
        "run_idx": run_idx,
        "seed": seed,
        "algorithms": {}
    }

    # 1. 2-Approximation (Gairing-Monien-Woclaw)
    t0 = time.time()
    alpha_2ap, w_star = find_2approx_assignment(n, m, P, C, b)
    t_2ap = time.time() - t0
    if alpha_2ap is not None:
        ms_2ap = max(compute_loads(n, m, P, alpha_2ap))
    else:
        ms_2ap = None

    trial_result["w_star"] = w_star
    trial_result["algorithms"]["2-Approximation"] = {
        "makespan": ms_2ap,
        "time": t_2ap,
        "ratio": (ms_2ap / w_star) if (ms_2ap and w_star > 0) else None,
    }

    # 2. Greedy Least-Loaded (Graham)
    t0 = time.time()
    alpha_gr, ms_gr = greedy_least_loaded(n, m, P)
    t_gr = time.time() - t0
    trial_result["algorithms"]["Greedy Least-Loaded"] = {
        "makespan": ms_gr,
        "time": t_gr,
        "ratio": (ms_gr / w_star) if (ms_gr and w_star > 0) else None,
    }

    # 3. Min-Min (Ibarra & Kim)
    t0 = time.time()
    alpha_mm, ms_mm = min_min(n, m, P)
    t_mm = time.time() - t0
    trial_result["algorithms"]["Min-Min"] = {
        "makespan": ms_mm,
        "time": t_mm,
        "ratio": (ms_mm / w_star) if (ms_mm and w_star > 0) else None,
    }

    # 4. Max-Min (Ibarra & Kim)
    t0 = time.time()
    alpha_mx, ms_mx = max_min(n, m, P)
    t_mx = time.time() - t0
    trial_result["algorithms"]["Max-Min"] = {
        "makespan": ms_mx,
        "time": t_mx,
        "ratio": (ms_mx / w_star) if (ms_mx and w_star > 0) else None,
    }

    # 5. Random Assignment (Pure ALOHA)
    t0 = time.time()
    alpha_rnd, ms_rnd = random_assignment(n, m, P, seed=seed)
    t_rnd = time.time() - t0
    trial_result["algorithms"]["Random Assignment"] = {
        "makespan": ms_rnd,
        "time": t_rnd,
        "ratio": (ms_rnd / w_star) if (ms_rnd and w_star > 0) else None,
    }

    return trial_result


def run_simulations(
    n_values: List[int],
    num_runs: int = 10,
    num_workers: int = 8,
    base_seed: int = 2026,
    out_file: Optional[str] = "output/large_scale_simulation.json",
) -> Dict[str, Any]:
    """
    Run the complete simulation suite across all n values with multiprocessing,
    checkpointing results incrementally to out_file after each n.
    """
    print("=" * 76)
    print("  LARGE-SCALE SIMULATION: LoRaWAN R||C_max Schedulers")
    print(f"  Range: n = {min(n_values)} to {max(n_values)} ({len(n_values)} points)")
    print(f"  Repetitions per n: {num_runs} independent trials")
    print(f"  Workers: {num_workers} parallel CPU processes")
    print("=" * 76)

    algo_names = [
        "2-Approximation",
        "Greedy Least-Loaded",
        "Min-Min",
        "Max-Min",
        "Random Assignment",
    ]

    aggregated_data: Dict[str, Any] = {
        "n_values": n_values,
        "num_runs": num_runs,
        "num_machines": NUM_MACHINES,
        "results": {}
    }

    # Load existing checkpoint if available
    if out_file and os.path.exists(out_file):
        try:
            with open(out_file, "r") as f:
                existing = json.load(f)
                if "results" in existing:
                    aggregated_data["results"] = existing["results"]
                    print(f"  [Resume] Loaded {len(existing['results'])} checkpoints from {out_file}")
        except Exception:
            pass

    ctx = mp.get_context("fork")

    for n in n_values:
        if str(n) in aggregated_data["results"]:
            print(f"  [Cached] Skipping n = {n:>5} (already in checkpoint)")
            continue

        t_start_n = time.time()
        print(f"\n>>> Simulating n = {n:>5} ({num_runs} runs)...", flush=True)

        tasks = [
            (n, base_seed + run_idx * 1000 + n, run_idx)
            for run_idx in range(num_runs)
        ]

        if num_workers > 1:
            with ctx.Pool(processes=min(num_workers, num_runs)) as pool:
                run_outputs = pool.map(evaluate_trial, tasks)
        else:
            run_outputs = [evaluate_trial(task) for task in tasks]

        # Aggregate statistics for this n
        n_summary = {
            "w_star_mean": float(sum(r["w_star"] for r in run_outputs) / num_runs),
            "algorithms": {}
        }

        for algo in algo_names:
            makespans = [r["algorithms"][algo]["makespan"] for r in run_outputs if r["algorithms"][algo]["makespan"] is not None]
            ratios = [r["algorithms"][algo]["ratio"] for r in run_outputs if r["algorithms"][algo]["ratio"] is not None]
            times = [r["algorithms"][algo]["time"] for r in run_outputs]

            def calc_stats(vals: List[float]) -> Dict[str, float]:
                if not vals:
                    return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
                m_val = sum(vals) / len(vals)
                variance = sum((x - m_val) ** 2 for x in vals) / len(vals)
                return {
                    "mean": round(m_val, 2),
                    "std": round(math.sqrt(variance), 2),
                    "min": round(min(vals), 2),
                    "max": round(max(vals), 2),
                }

            n_summary["algorithms"][algo] = {
                "makespan": calc_stats(makespans),
                "ratio": calc_stats(ratios),
                "runtime": calc_stats(times),
            }

        aggregated_data["results"][str(n)] = n_summary
        elapsed_n = time.time() - t_start_n

        # Incremental save to prevent loss on interrupt
        if out_file:
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            with open(out_file, "w") as f:
                json.dump(aggregated_data, f, indent=2)

        # Concise console log
        approx_ms = n_summary["algorithms"]["2-Approximation"]["makespan"]["mean"]
        approx_ratio = n_summary["algorithms"]["2-Approximation"]["ratio"]["mean"]
        greedy_ms = n_summary["algorithms"]["Greedy Least-Loaded"]["makespan"]["mean"]
        rnd_ms = n_summary["algorithms"]["Random Assignment"]["makespan"]["mean"]
        print(f"    Completed in {elapsed_n:.1f}s | "
              f"2-Approx: {approx_ms:.0f} ms (ratio: {approx_ratio:.3f}) | "
              f"Greedy: {greedy_ms:.0f} ms | "
              f"Random: {rnd_ms:.0f} ms")

    return aggregated_data


def main():
    parser = argparse.ArgumentParser(description="Large-Scale LoRaWAN Scheduling Simulation")
    parser.add_argument("--runs", "-r", type=int, default=10, help="Number of repetitions per n")
    parser.add_argument("--workers", "-w", type=int, default=12, help="Number of CPU worker processes")
    parser.add_argument("--out", "-o", default="output/large_scale_simulation.json", help="Output JSON path")
    args = parser.parse_args()

    # Dense evaluation grid spanning 100 to 10,000
    n_values = [
        100, 250, 500, 750, 1000, 1500, 2000, 2500,
        3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000
    ]

    total_start = time.time()
    results = run_simulations(
        n_values=n_values,
        num_runs=args.runs,
        num_workers=args.workers,
        out_file=args.out,
    )

    total_time = time.time() - total_start
    print("\n" + "=" * 76)
    print(f"  SIMULATION COMPLETED in {total_time / 60:.2f} minutes")
    print(f"  Aggregated results saved to: {args.out}")
    print("=" * 76)


if __name__ == "__main__":
    main()
