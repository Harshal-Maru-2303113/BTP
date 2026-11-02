#!/usr/bin/env python3
"""
Plotting Script for Large-Scale Scheduling Simulation Results

Reads output/large_scale_simulation.json and generates high-resolution,
publication-quality figures:
  1. output/makespan_scaling.png       — All 5 algorithms
  2. output/makespan_zoom_scaling.png  — 4 high-performance algorithms
  3. output/ratio_scaling.png          — Empirical ratio to w* vs theoretical 2.0
  4. output/runtime_scaling.png        — Execution time scaling (log-log)
  5. output/simulation_dashboard.png   — Comprehensive 2x2 dashboard
"""

import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Configure clean aesthetic matplotlib styling
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

ALGO_COLORS = {
    "2-Approximation": "#1f77b4",       # Solid Blue
    "Greedy Least-Loaded": "#2ca02c",   # Forest Green
    "Min-Min": "#ff7f0e",               # Bright Orange
    "Max-Min": "#9467bd",               # Royal Purple
    "Random Assignment": "#d62728",     # Crimson Red
}

ALGO_MARKERS = {
    "2-Approximation": "o",
    "Greedy Least-Loaded": "s",
    "Min-Min": "^",
    "Max-Min": "D",
    "Random Assignment": "x",
}

ALGO_LINESTYLES = {
    "2-Approximation": "-",
    "Greedy Least-Loaded": "--",
    "Min-Min": "-.",
    "Max-Min": ":",
    "Random Assignment": "--",
}


def load_data(json_path: str):
    with open(json_path, "r") as f:
        return json.load(f)


def plot_all_makespans(data, out_dir):
    """Plot 1: Makespan vs n for all 5 algorithms with error bands."""
    n_vals = [int(n) for n in data["n_values"]]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    for algo, color in ALGO_COLORS.items():
        means = []
        stds = []
        for n_str in [str(n) for n in n_vals]:
            stats = data["results"][n_str]["algorithms"][algo]["makespan"]
            means.append(stats["mean"] / 1000.0)  # convert ms to seconds
            stds.append(stats["std"] / 1000.0)

        means = np.array(means)
        stds = np.array(stds)

        ax.plot(
            n_vals, means,
            label=algo,
            color=color,
            marker=ALGO_MARKERS[algo],
            linestyle=ALGO_LINESTYLES[algo],
            linewidth=2,
            markersize=6,
        )
        ax.fill_between(n_vals, means - stds, means + stds, color=color, alpha=0.15)

    ax.set_xlabel("Number of Packets ($n$)")
    ax.set_ylabel("Average Makespan $C_{\\max}$ (seconds)")
    ax.set_title("Makespan Scaling: $n = 100$ to $10,000$ (10 Trials per $n$)")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    path = os.path.join(out_dir, "makespan_scaling.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved: {path}")


def plot_zoomed_makespans(data, out_dir):
    """Plot 2: Makespan vs n comparing the 4 coordinated algorithms."""
    n_vals = [int(n) for n in data["n_values"]]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    algos = ["2-Approximation", "Greedy Least-Loaded", "Min-Min", "Max-Min"]

    for algo in algos:
        color = ALGO_COLORS[algo]
        means = []
        stds = []
        for n_str in [str(n) for n in n_vals]:
            stats = data["results"][n_str]["algorithms"][algo]["makespan"]
            means.append(stats["mean"] / 1000.0)  # seconds
            stds.append(stats["std"] / 1000.0)

        means = np.array(means)
        stds = np.array(stds)

        ax.plot(
            n_vals, means,
            label=algo,
            color=color,
            marker=ALGO_MARKERS[algo],
            linestyle=ALGO_LINESTYLES[algo],
            linewidth=2,
            markersize=6,
        )
        ax.fill_between(n_vals, means - stds, means + stds, color=color, alpha=0.15)

    ax.set_xlabel("Number of Packets ($n$)")
    ax.set_ylabel("Average Makespan $C_{\\max}$ (seconds)")
    ax.set_title("Makespan Comparison (Coordinated Algorithms): $n = 100$ to $10,000$")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    path = os.path.join(out_dir, "makespan_zoom_scaling.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved: {path}")


def plot_empirical_ratios(data, out_dir):
    """Plot 3: Approximation ratio to w* with theoretical bound 2.0."""
    n_vals = [int(n) for n in data["n_values"]]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    for algo, color in ALGO_COLORS.items():
        if algo == "Random Assignment":
            continue  # Random ratio is ~15-20, plot on inset or skip to keep graph focused
        means = []
        stds = []
        for n_str in [str(n) for n in n_vals]:
            stats = data["results"][n_str]["algorithms"][algo]["ratio"]
            means.append(stats["mean"])
            stds.append(stats["std"])

        means = np.array(means)
        stds = np.array(stds)

        ax.plot(
            n_vals, means,
            label=algo,
            color=color,
            marker=ALGO_MARKERS[algo],
            linestyle=ALGO_LINESTYLES[algo],
            linewidth=2,
            markersize=6,
        )
        ax.fill_between(n_vals, means - stds, means + stds, color=color, alpha=0.15)

    # Theoretical bound line
    ax.axhline(2.0, color="black", linestyle=":", linewidth=2, label="Theoretical Bound ($2.0 \\times \\text{OPT}$)")

    ax.set_xlabel("Number of Packets ($n$)")
    ax.set_ylabel("Empirical Ratio to $w^*$ ($C_{\\max} / w^*$)")
    ax.set_title("Approximation Ratio Scaling Relative to Lower Bound $w^*$")
    ax.set_ylim(0.8, 2.3)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, loc="center right")
    plt.tight_layout()
    path = os.path.join(out_dir, "ratio_scaling.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved: {path}")


def plot_runtimes(data, out_dir):
    """Plot 4: Execution time vs n on log-log scale."""
    n_vals = [int(n) for n in data["n_values"]]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    for algo, color in ALGO_COLORS.items():
        means = []
        for n_str in [str(n) for n in n_vals]:
            stats = data["results"][n_str]["algorithms"][algo]["runtime"]
            means.append(max(stats["mean"], 1e-4))

        ax.plot(
            n_vals, means,
            label=algo,
            color=color,
            marker=ALGO_MARKERS[algo],
            linestyle=ALGO_LINESTYLES[algo],
            linewidth=2,
            markersize=6,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Number of Packets ($n$, log scale)")
    ax.set_ylabel("Average Execution Time (seconds, log scale)")
    ax.set_title("Runtime Scaling: $n = 100$ to $10,000$ (Log-Log Scale)")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    path = os.path.join(out_dir, "runtime_scaling.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved: {path}")


def plot_dashboard(data, out_dir):
    """Plot 5: 2x2 comprehensive publication dashboard."""
    n_vals = [int(n) for n in data["n_values"]]
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 11))

    # Panel (a): All Makespans
    for algo, color in ALGO_COLORS.items():
        means = [data["results"][str(n)]["algorithms"][algo]["makespan"]["mean"] / 1000.0 for n in n_vals]
        ax1.plot(n_vals, means, label=algo, color=color, marker=ALGO_MARKERS[algo], linewidth=1.8, markersize=5)
    ax1.set_title("(a) Overall Makespan ($C_{\\max}$ in seconds)")
    ax1.set_xlabel("Number of Packets ($n$)")
    ax1.set_ylabel("Makespan (s)")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=8, loc="upper left")

    # Panel (b): Zoomed Makespan
    for algo in ["2-Approximation", "Greedy Least-Loaded", "Min-Min", "Max-Min"]:
        means = [data["results"][str(n)]["algorithms"][algo]["makespan"]["mean"] / 1000.0 for n in n_vals]
        ax2.plot(n_vals, means, label=algo, color=ALGO_COLORS[algo], marker=ALGO_MARKERS[algo], linewidth=1.8, markersize=5)
    ax2.set_title("(b) Coordinated Schedulers Detail")
    ax2.set_xlabel("Number of Packets ($n$)")
    ax2.set_ylabel("Makespan (s)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=8, loc="upper left")

    # Panel (c): Approximation Ratio
    for algo in ["2-Approximation", "Greedy Least-Loaded", "Min-Min", "Max-Min"]:
        means = [data["results"][str(n)]["algorithms"][algo]["ratio"]["mean"] for n in n_vals]
        ax3.plot(n_vals, means, label=algo, color=ALGO_COLORS[algo], marker=ALGO_MARKERS[algo], linewidth=1.8, markersize=5)
    ax3.axhline(2.0, color="black", linestyle=":", linewidth=2, label="Theoretical Bound (2.0)")
    ax3.set_title("(c) Empirical Ratio to Lower Bound $w^*$")
    ax3.set_xlabel("Number of Packets ($n$)")
    ax3.set_ylabel("Ratio ($C_{\\max} / w^*$)")
    ax3.set_ylim(0.8, 2.2)
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(fontsize=8, loc="lower right")

    # Panel (d): Runtime
    for algo, color in ALGO_COLORS.items():
        means = [max(data["results"][str(n)]["algorithms"][algo]["runtime"]["mean"], 1e-4) for n in n_vals]
        ax4.plot(n_vals, means, label=algo, color=color, marker=ALGO_MARKERS[algo], linewidth=1.8, markersize=5)
    ax4.set_xscale("log")
    ax4.set_yscale("log")
    ax4.set_title("(d) Execution Time Scaling (Log-Log)")
    ax4.set_xlabel("Number of Packets ($n$)")
    ax4.set_ylabel("Execution Time (s)")
    ax4.grid(True, which="both", linestyle="--", alpha=0.5)
    ax4.legend(fontsize=8, loc="upper left")

    plt.suptitle("Large-Scale LoRaWAN Scheduling Performance Evaluation ($n = 100$ to $10,000$)", fontsize=16, y=0.99)
    plt.tight_layout()
    path = os.path.join(out_dir, "simulation_dashboard.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved: {path}")


def main():
    parser = argparse.ArgumentParser(description="Plot Simulation Results")
    parser.add_argument("--json", "-j", default="output/large_scale_simulation.json")
    parser.add_argument("--outdir", "-o", default="output")
    args = parser.parse_args()

    if not os.path.exists(args.json):
        print(f"Error: {args.json} does not exist. Run simulate_scaling.py first.")
        return

    os.makedirs(args.outdir, exist_ok=True)
    data = load_data(args.json)

    plot_all_makespans(data, args.outdir)
    plot_zoomed_makespans(data, args.outdir)
    plot_empirical_ratios(data, args.outdir)
    plot_runtimes(data, args.outdir)
    plot_dashboard(data, args.outdir)
    print("\nAll plots successfully generated in:", args.outdir)


if __name__ == "__main__":
    main()
