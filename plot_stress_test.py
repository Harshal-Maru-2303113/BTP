#!/usr/bin/env python3
"""
Plot Adversarial Worst-Case Benchmark Results

Visualizes the scenarios where heuristic baselines (Min-Min, Greedy, Random)
degrade up to 3.31x OPT, while the 2-Approximation scheme strictly maintains
its <= 2.0x OPT bound.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

def main():
    json_path = "output/stress_test_results.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    # 1. Plot Suite 3: Min-Min Bottleneck Contention
    suite3 = data["suite_3_min_min_starvation"]
    labels3 = [f"m={inst['m']}\n(n={inst['n']})" for inst in suite3]
    
    ratios_2a_3 = [inst["2_approx"]["ratio_to_w_star"] for inst in suite3]
    ratios_mm_3 = [inst["baselines"]["Min-Min"]["ratio_to_w_star"] for inst in suite3]
    ratios_gr_3 = [inst["baselines"]["Greedy Least-Loaded"]["ratio_to_w_star"] for inst in suite3]
    ratios_mx_3 = [inst["baselines"]["Max-Min"]["ratio_to_w_star"] for inst in suite3]

    x = np.arange(len(labels3))
    width = 0.2

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(x - 1.5 * width, ratios_2a_3, width, label="2-Approx (Ours)", color="#1f77b4", edgecolor="black")
    ax.bar(x - 0.5 * width, ratios_mm_3, width, label="Min-Min", color="#ff7f0e", edgecolor="black")
    ax.bar(x + 0.5 * width, ratios_gr_3, width, label="Greedy Least-Loaded", color="#2ca02c", edgecolor="black")
    ax.bar(x + 1.5 * width, ratios_mx_3, width, label="Max-Min", color="#9467bd", edgecolor="black")

    ax.axhline(2.0, color="red", linestyle="--", linewidth=1.8, label="Theoretical Bound (2.0× OPT)")

    ax.set_ylabel("Empirical Ratio to $w^*$ (Lower Bound)")
    ax.set_title("Suite 3: Min-Min Bottleneck Contention (Heuristics Degrade to 2.79× OPT)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels3)
    ax.set_ylim(0, 3.2)
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, loc="upper left")
    plt.tight_layout()
    plt.savefig("output/adversarial_min_min_failure.png")
    plt.close()
    print("Saved output/adversarial_min_min_failure.png")

    # 2. Plot Suite 5: Unrelated Machines Adversary
    suite5 = data["suite_5_unrelated_adversarial"]
    labels5 = [f"m={inst['m']}\n(n={inst['n']})" for inst in suite5]
    
    ratios_2a_5 = [inst["2_approx"]["ratio_to_w_star"] for inst in suite5]
    ratios_mm_5 = [inst["baselines"]["Min-Min"]["ratio_to_w_star"] for inst in suite5]
    ratios_gr_5 = [inst["baselines"]["Greedy Least-Loaded"]["ratio_to_w_star"] for inst in suite5]
    ratios_mx_5 = [inst["baselines"]["Max-Min"]["ratio_to_w_star"] for inst in suite5]

    x5 = np.arange(len(labels5))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(x5 - 1.5 * width, ratios_2a_5, width, label="2-Approx (Ours)", color="#1f77b4", edgecolor="black")
    ax.bar(x5 - 0.5 * width, ratios_mm_5, width, label="Min-Min", color="#ff7f0e", edgecolor="black")
    ax.bar(x5 + 0.5 * width, ratios_gr_5, width, label="Greedy Least-Loaded", color="#2ca02c", edgecolor="black")
    ax.bar(x5 + 1.5 * width, ratios_mx_5, width, label="Max-Min", color="#9467bd", edgecolor="black")

    ax.axhline(2.0, color="red", linestyle="--", linewidth=1.8, label="Theoretical Bound (2.0× OPT)")

    ax.set_ylabel("Empirical Ratio to $w^*$ (Lower Bound)")
    ax.set_title("Suite 5: Unrelated Machine Contention (Heuristics Degrade to 3.31× OPT)")
    ax.set_xticks(x5)
    ax.set_xticklabels(labels5)
    ax.set_ylim(0, 3.7)
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, loc="upper left")
    plt.tight_layout()
    plt.savefig("output/adversarial_unrelated_failure.png")
    plt.close()
    print("Saved output/adversarial_unrelated_failure.png")


if __name__ == "__main__":
    main()
