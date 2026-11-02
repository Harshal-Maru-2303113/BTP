# Project Overview

## What This Project Is

**LoRaWAN Hypercycle Scheduler** — a Bachelor's Thesis Project (BTP) implementing a **combinatorial 2-approximation algorithm** for real-time packet scheduling in LoRaWAN networks.

### The Core Problem

Schedule **n** real-time LoRa packets across **m = 48** logical machines (8 channels × 6 spreading factors) to minimise the maximum machine load (makespan), subject to:

- **Unrelated processing times** — Time-on-Air depends on (payload, SF) via the Semtech SX1276 formula (ranging from 42 ms on SF7/10 B to 2302 ms on SF12/50 B under ceiling integer discretization; 41.2 ms to 2301.95 ms continuous)
- **Deadline constraints** — each packet must finish before its deadline
- **Non-preemption** — no two transmissions overlap on the same (SF, channel) pair
- **Gateway demodulation limit** — at most 8 concurrent transmissions network-wide

This is formally the **R || C_max** problem (scheduling on unrelated parallel machines to minimize makespan), which is NP-hard.

### The Solution

A 4-phase algorithm:

| Phase | What It Does | Guarantee |
|---|---|---|
| **Phase 1** | 2-Approximation makespan minimisation using Gairing–Monien–Woclaw (2007) | C_max ≤ 2 · OPT |
| **Phase 1.5** | Energy-optimal capacity-constrained downshifting (Casals et al. 2017) | Minimizes radio Joules while preserving C_max ≤ 2 · OPT |
| **Phase 2** | Per-channel EDF timeline + segment tree for 8-demod tracking | Non-preemption + Ω(t) ≤ 8 |
| **Phase 3** | Priority-based packet dropping for infeasible packets | Graceful degradation |

### Key Results

- **Theoretical guarantee**: Machine load makespan ≤ 2 × OPT, always (unconditionally preserved by Phase 1.5).
- **Radio Energy Optimization**: Fleet-wide energy consumption is minimized by aggressively downshifting to lowest feasible SFs:
  - 2-Approx (Phase 1.5): **6,493.8 mJ** across all 234 packets ($27.8\text{ mJ/pkt}$).
  - Baselines consume up to **+45.1% more energy** (Min-Min: 8,734 mJ, Max-Min: 9,422 mJ) by dispersing traffic to higher SFs.
- **End-to-End Scheduled Subset** (`main.py`, thesis §6):
  - 234 packets generated, 101 scheduled, 133 dropped (due to $t=0$ synchronous hardware saturation).
  - Machine load makespan: **1,302 ms** vs exact OPT: **800 ms** → **Empirical ratio: 1.6275** (18.6% safety margin below 2.0).
  - Timeline span: 90,072 ms / 100,000 ms.
  - Radio energy scheduled: **2,649.6 mJ** ($26.2\text{ mJ/pkt}$).
- **Full Workload Allocation** (`run_baseline_comparison.py`, all 234 packets without temporal drop):
  - Machine load makespan: **1,545 ms** vs exact OPT: **933 ms** → **Empirical ratio: 1.656** ($w^* = 775\text{ ms}$).

---

## Base Paper

> M. Gairing, B. Monien, A. Woclaw, *"A faster combinatorial approximation algorithm for scheduling unrelated parallel machines"*, Theoretical Computer Science 380, 2007, pp. 87–99.

This paper provides the core algorithmic framework (binary search + Unsplittable-Truemper + Unsplittable-Blocking-Flow). The BTP extends it with LoRaWAN-specific constraints (EDF timeline, segment tree demod tracking, priority-based dropping).

---

## Quick Start

```bash
# Run the simulation
python main.py

# Run with exact OPT comparison
python main.py --ilp

# Run with Cyclic Executive Mode (minor cycles + packet carryover buffer)
python main.py --cyclic

# Run tests
python -m pytest tests/ -v

# Run baseline comparison
python run_baseline_comparison.py

# Run stress tests
python run_stress_test.py

# Run large-scale simulation (100 to 10,000 packets)
python simulate_scaling.py
```

### Dependencies

- **Python 3.8+**
- **No external packages** required for core simulation
- **Optional**: `pulp` for ILP comparison, `numpy`/`matplotlib` for plotting
- See `requirements.txt`: `numpy>=1.24.0`, `PuLP>=2.7.0`

