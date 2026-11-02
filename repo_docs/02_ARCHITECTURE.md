# Architecture & Code Map

## Directory Structure

```
BTP/
├── main.py                         # Entry point — orchestrates the full pipeline
├── config.json                     # All simulation parameters
├── config_loader.py                # Parses config.json into typed dataclasses
├── data_structures.py              # Core data types (Packet, Machine, ScheduleEntry, etc.)
├── lorawan_toa.py                  # Semtech SX1276 ToA formula + cost matrix
├── lorawan_energy.py               # Casals et al. Class A energy model + Semtech §4.1.1.7 ToA
├── packet_generator.py             # Generates harmonic periodic traffic
├── segment_tree.py                 # Lazy-propagation max segment tree for demod tracking
├── stats.py                        # Per-SF, per-channel, energy, aggregate statistics
├── output_writer.py                # JSON output writer
├── baselines.py                    # 4 baseline heuristic algorithms
│
├── approximation/                  # Core 2-approximation algorithm
│   ├── __init__.py                 # Module docstring
│   ├── binary_search.py            # Outer binary search over candidate makespan w
│   ├── truemper.py                 # Algorithm 2: Unsplittable-Truemper (outer loop)
│   ├── blocking_flow.py            # Algorithm 1: Unsplittable-Blocking-Flow (inner loop)
│   └── graph_utils.py              # Dijkstra, BFS, admissible graph, load computation
│
├── scheduler/                      # Full scheduling pipeline
│   ├── __init__.py
│   ├── energy_optimizer.py         # Phase 1.5: Capacity-constrained energy downshift
│   └── lorawan_scheduler.py        # Algorithm 3: Phase 1 + Phase 1.5 + Phase 2 + Phase 3
│
├── validator/                      # Correctness verification
│   ├── __init__.py
│   ├── invariant_checker.py        # Schedule validity checks (overlaps, deadlines, demod)
│   ├── ilp_solver.py               # PuLP ILP solver for exact OPT
│   └── bruteforce_comparator.py    # Exact B&B + naive brute-force verifier
│
├── tests/
│   └── test_scheduler.py           # 8 unit/integration tests
│
├── run_baseline_comparison.py      # Single-instance baseline comparison runner
├── run_stress_test.py              # 5-suite adversarial stress testing
├── simulate_scaling.py             # Large-scale simulation (n=100 to 10,000)
├── plot_scaling_results.py         # Publication-quality scaling plots
├── plot_stress_test.py             # Adversarial worst-case bar charts
│
├── output/                         # Generated outputs
│   ├── schedule.json               # Full schedule
│   ├── stats.json                  # Statistics
│   ├── baseline_comparison.json
│   ├── stress_test_results.json
│   ├── large_scale_simulation.json
│   └── *.png                       # Generated plots
│
├── main.tex                        # Full BTP thesis (LaTeX source)
├── preamble.tex                    # LaTeX preamble
├── refr.bib                        # BibTeX references
├── main.pdf                        # Compiled thesis PDF
│
├── upper_bound_proof.md            # Complete 2-approximation proof
├── baseline_comparison.md          # Detailed baseline analysis
├── simulation_report.md            # Large-scale simulation results
├── input.md                        # Input specification guide
└── output.md                       # Output specification guide
```

## Data Flow Pipeline

```
config.json
    │
    ▼
config_loader.py ──→ SimConfig (typed dataclass)
    │
    ├──→ packet_generator.py ──→ List[Machine], List[Packet]
    │
    ├──→ lorawan_toa.py ──→ P[n×m] (ToA matrix), C[n×m] (cost matrix)
    │
    ├──→ lorawan_energy.py ──→ E[n×m] (Class A cycle energy matrix)
    │
    └──→ scheduler/lorawan_scheduler.py
              │
              ├── Phase 1: approximation/binary_search.py
              │       └── approximation/truemper.py
              │               └── approximation/blocking_flow.py
              │                       └── approximation/graph_utils.py
              │
              ├── Phase 1.5: scheduler/energy_optimizer.py
              │       (minimizes energy, preserves δ_j ≤ 2w* bound)
              │
              ├── Phase 2: EDF timeline + segment_tree.py (demod tracking)
              │
              └── Phase 3: Priority-based dropping
                      │
                      ▼
              ScheduleResult
                      │
    ┌───────────────────┴─────────────────────┐
    │                                         │
    ▼                                         ▼
validator/invariant_checker.py         stats.py + output_writer.py
    (correctness verification)          (JSON output files)
```

## Module Dependencies

| Module | Depends On |
|---|---|
| `main.py` | config_loader, packet_generator, lorawan_toa, scheduler, validator, stats, output_writer |
| `scheduler/lorawan_scheduler.py` | data_structures, segment_tree, approximation.binary_search, approximation.graph_utils, lorawan_toa |
| `approximation/binary_search.py` | data_structures, approximation.graph_utils, approximation.truemper |
| `approximation/truemper.py` | data_structures, approximation.graph_utils, approximation.blocking_flow |
| `approximation/blocking_flow.py` | data_structures, approximation.graph_utils |
| `approximation/graph_utils.py` | data_structures |
| `baselines.py` | data_structures |
| `validator/bruteforce_comparator.py` | data_structures, config_loader, packet_generator, lorawan_toa, approximation |

