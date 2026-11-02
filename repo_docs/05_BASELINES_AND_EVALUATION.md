# Baseline Algorithms & Evaluation Framework

## Baseline Algorithms (baselines.py)

### 1. Random Assignment (Pure ALOHA)
- **Strategy**: Each job picks a uniformly random feasible machine
- **Complexity**: O(n)
- **Guarantee**: None — can be arbitrarily bad
- **Relevance**: Models uncoordinated LoRaWAN Class A behavior

### 2. Greedy Least-Loaded (List Scheduling)
- **Reference**: Graham (1966), "Bounds for certain multiprocessor anomalies"
- **Strategy**: Process jobs in order; assign each to the feasible machine with lowest resulting load
- **Complexity**: O(n·m)
- **Guarantee**: 2-approx on **identical** machines; **no guarantee on unrelated** machines

### 3. Min-Min Heuristic
- **Reference**: Ibarra & Kim (1977), "Heuristic algorithms for scheduling independent tasks on nonidentical processors"
- **Strategy**: Iteratively select the unassigned job with the SMALLEST minimum completion time; assign to its best machine
- **Complexity**: O(n²·m) with heap optimisation
- **Intuition**: Place easy jobs first to leave room for hard ones
- **Weakness**: Large bottleneck jobs placed last when machines are loaded

### 4. Max-Min Heuristic
- **Reference**: Ibarra & Kim (1977)
- **Strategy**: Iteratively select the unassigned job with the LARGEST minimum completion time; assign to its best machine
- **Complexity**: O(n²·m) with heap optimisation
- **Intuition**: Place hard jobs first on empty machines; small jobs fill gaps
- **Strength**: Often best heuristic for heterogeneous environments

---

## Evaluation Results: Two Complementary Benchmarks

To avoid ambiguity, the project evaluates the 2-approximation algorithm across two distinct experimental settings:

### Benchmark A: Full Workload Allocation (`run_baseline_comparison.py`, $n=234, m=48$)
Evaluates Phase 1 load balancing directly on all $n=234$ packets across $m=48$ machines (without temporal drop):

| Algorithm | Makespan (ms) | Ratio to OPT | Ratio to $w^*$ | Guarantee | Runtime (s) |
|---|:---:|:---:|:---:|:---:|:---:|
| Exact OPT (ILP B&B) | 933 | 1.000 | 1.204 | exact | 30.23 |
| Max-Min | 933 | 1.000 | 1.204 | ❌ None | 0.058 |
| Greedy Least-Loaded | 989 | 1.060 | 1.276 | ❌ None | 0.001 |
| Min-Min | 990 | 1.061 | 1.277 | ❌ None | 0.071 |
| **★ 2-Approx (Ours)** | **1,545** | **1.656** | **1.994** | **✅ ≤ 2.0** | 0.212 |
| Random Assignment | 12,193 | 13.069 | 15.733 | ❌ None | 0.004 |

*Note: On this benign instance (5 packets/machine), simple heuristics achieve low makespans by greedily packing machines. The 2-approximation pays a modest constant overhead (1.656× OPT) to guarantee safety under adversarial distributions.*

#### Fleet Radio Energy Consumption (Casals et al. 2017 Class A Model)

| Algorithm | Total Energy (mJ) | Avg mJ/packet | vs. 2-Approx | Why This Happens |
|---|:---:|:---:|:---:|---|
| **★ 2-Approx (Phase 1.5)** | **6,493.8** | **27.8** | **1.00× (base)** | Confines load to lowest feasible SF (SF7) within $2w^*$ |
| Min-Min | 8,734.4 | 37.3 | 1.35× (+34.5%) | Offloads jobs to SF8 to reduce makespan, inflating energy |
| Greedy Least-Loaded | 9,261.2 | 39.6 | 1.43× (+42.6%) | Spreads jobs across all machines indiscriminately |
| Max-Min | 9,422.7 | 40.3 | 1.45× (+45.1%) | Distributes hard jobs to higher SFs, creating high energy burden |
| Random Assignment | 28,838.2 | 123.2 | 4.44× (+344.1%) | Catastrophic random placement onto SF10–SF12 |

### Benchmark B: End-to-End Scheduled Subset (`main.py`, thesis §6, $n=101, m=48$)
Evaluates the full 3-phase pipeline with temporal placement, deadline enforcement, and 8-demod tracking:

| Metric | 2-Approx Result | Exact OPT | Status |
|---|:---:|:---:|:---:|
| Packets Scheduled | 101 / 234 | 101 | 133 dropped due to $t=0$ synchronous hardware saturation |
| Machine Load Makespan | **1,302 ms** | **800 ms** | **Ratio = 1.6275 ≤ 2.0 ✅ (18.6% margin)** |
| Timeline Calendar Span | 90,072 ms | — | Clamped within hypercycle horizon (100,000 ms) |
| Concurrent Demodulations | 8 / 8 | ≤ 8 | Hard hardware constraint satisfied |

---

## Stress Testing (run_stress_test.py)

5 adversarial benchmark suites demonstrating where heuristics fail:

### Suite 1: Scaled LoRaWAN Density (25 to 400 devices)
- 2-Approx: strict 2.00× across all sizes
- Random: catastrophic 10.8× to 22.1×

### Suite 2: Graham (1966) Anomaly (identical machines)
- Greedy/Min-Min approach 2.00× as m grows (Graham's classical bound)
- Max-Min finds OPT on these instances

### Suite 3: Min-Min Bottleneck Starvation
- **Min-Min and Greedy degrade to 2.79×** (exceeds 2× bound by 40%)
- 2-Approx stays at 2.00×

### Suite 4: Max-Min Heterogeneity Trap
- Min-Min degrades to 2.27×
- Random explodes to 10.5×
- 2-Approx: 2.00×

### Suite 5: Unrelated Machine Contention
- **Greedy and Min-Min degrade to 3.31×** (ratio grows with m!)
- 2-Approx: strict 2.00×

### Cross-Suite Worst-Case Summary

| Algorithm | Best Ratio | Worst Ratio | Bound |
|---|:---:|:---:|:---:|
| **2-Approx** | 1.66× | **2.00×** | **≤ 2.00×** |
| Greedy LL | 1.01× | **3.31×** | Unbounded |
| Min-Min | 1.00× | **3.31×** | Unbounded |
| Max-Min | 0.99× | 2.00× | Unbounded |
| Random | 1.8× | **22.1×** | Unbounded |

---

## Large-Scale Simulation (simulate_scaling.py)

- 16 problem sizes from n=100 to n=10,000
- 10 independent trials per size
- 48 LoRaWAN machines, realistic heterogeneous traffic

Key findings:
- **2-Approx ratio exactly 2.000 across all sizes** (from n=100 to n=10,000)
- Runtime: ~25–35 seconds at n=10,000
- Random Assignment: makespan inflates to 1,092 seconds at n=10,000
- All coordinated algorithms complete under 170 seconds

---

## Exact Solvers (validator/)

### ILP Solver (`ilp_solver.py`)
- Uses PuLP with CBC/GLPK/HiGHS backend
- Formulation: min C_max, s.t. ∑_j x_ij = 1, ∑_i p_ij·x_ij ≤ C_max
- Falls back to pure Python B&B if no solver binary found
- Feasible for n ≤ 200

### Branch-and-Bound (`bruteforce_comparator.py`)
- **Naive brute force**: Exhaustive enumeration (mathematical ground truth)
- **Exact B&B**: LPT-seeded with symmetry breaking (column signature pruning)
- **Soundness verification**: 25 randomised trials confirming B&B matches naive 100%
- **Theoretical lower bound**: LB = max(max_i min_j P_ij, ceil(∑ min_j P_ij / m))

---

## Plotting Scripts

### `plot_scaling_results.py`
Generates 5 publication-quality figures:
1. `makespan_scaling.png` — all 5 algorithms
2. `makespan_zoom_scaling.png` — 4 coordinated algorithms
3. `ratio_scaling.png` — empirical ratio vs theoretical 2.0
4. `runtime_scaling.png` — execution time (log-log)
5. `simulation_dashboard.png` — 2×2 comprehensive dashboard

### `plot_stress_test.py`
Generates 2 adversarial bar charts:
1. `adversarial_min_min_failure.png` — Suite 3 results
2. `adversarial_unrelated_failure.png` — Suite 5 results

