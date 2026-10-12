# LoRaWAN Hypercycle Scheduler — BTP Project

A combinatorial 2-approximation framework for real-time packet scheduling in LoRaWAN networks. Implements the Gairing–Monien–Woclaw (2007) algorithm adapted to LoRaWAN's physical-layer constraints: multi-SF/multi-channel machines, gateway demodulation limits, and harmonic periodic traffic.

## Problem

Schedule **n** real-time LoRa packets across **m = N_ch × N_sf** logical machines (channel × spreading factor pairs) to minimise the maximum machine load (makespan), subject to:

- **Unrelated processing times** — Time-on-Air depends on (payload, SF) via the Semtech SX1276 formula
- **Deadline constraints** — each packet must finish before its deadline
- **Non-preemption** — no two transmissions overlap on the same (SF, channel) pair
- **Gateway demodulation limit** — at most 8 concurrent transmissions network-wide

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        main.py                          │
│  Orchestrates: Config → Generate → Schedule → Validate  │
└──────┬──────────────┬───────────────┬───────────────────┘
       │              │               │
       ▼              ▼               ▼
 ┌───────────┐ ┌─────────────┐ ┌──────────────┐
 │ config_   │ │ packet_     │ │ lorawan_     │
 │ loader.py │ │ generator.py│ │ toa.py       │
 │           │ │             │ │ ToA formula  │
 └───────────┘ └─────────────┘ │ + cost matrix│
                               └──────────────┘
       ┌───────────────────────────────────────┐
       │       scheduler/lorawan_scheduler.py  │
       │  Phase 1: 2-Approx Makespan (below)   │
       │  Phase 2: EDF Timeline + Demod Check   │
       │  Phase 3: Priority-Based Dropping      │
       └──────┬────────────────────────────────┘
              │
       ┌──────▼──────────────────────────┐
       │      approximation/             │
       │  binary_search.py  — outer loop │
       │  truemper.py       — Algorithm 2│
       │  blocking_flow.py  — Algorithm 1│
       │  graph_utils.py    — Dijkstra,  │
       │                      BFS, loads │
       └─────────────────────────────────┘
       ┌─────────────────────────────────┐
       │      validator/                 │
       │  invariant_checker.py           │
       │  ilp_solver.py (PuLP / B&B)     │
       │  bruteforce_comparator.py       │
       └─────────────────────────────────┘
```

## Algorithm

### Phase 1 — Makespan Minimisation (2-Approximation)

Binary search over candidate makespan `w`, calling **Unsplittable-Truemper** at each step:

1. Compute shortest-path distances via Dijkstra on the residual network with reduced costs
2. Build the admissible subgraph (zero reduced-cost edges)
3. Run **Unsplittable-Blocking-Flow** to push jobs from overloaded machines (M⁺) to underloaded machines (M⁻) along helpful paths
4. Update node potentials and repeat

**Guarantee:** The returned assignment has `max_load ≤ 2 · OPT`.

### Phase 2 — EDF Timeline Construction

Per-channel Earliest Deadline First placement with a **segment tree** tracking global demodulation occupancy. Before placing a packet, the segment tree is queried; if the 8-demod limit is reached, the start time is shifted forward.

### Phase 3 — Priority-Based Dropping

Packets that violate deadlines or the demod constraint are dropped in order of `(lowest priority, latest deadline, highest ID)`.

## Quick Start

### Prerequisites

- Python 3.8+
- No external packages required for core simulation
- Optional: `pulp` for ILP comparison (`pip install pulp`)

### Run the Simulation

```bash
python main.py
```

### Run with Exact OPT Comparison

```bash
python main.py --ilp
```

### Run Tests

```bash
python -m pytest tests/ -v
```

### Run Bruteforce Verification

```bash
python -m validator.bruteforce_comparator
```

## Configuration

All parameters are in [`config.json`](config.json):

| Parameter | Default | Description |
|---|---|---|
| `num_channels` | 8 | Number of orthogonal LoRa channels |
| `spreading_factors` | [7–12] | Available spreading factors |
| `hypercycle_duration_s` | 100 | Hypercycle duration in seconds |
| `max_concurrent_demodulations` | 8 | Gateway demod limit |
| `num_end_devices` | 50 | Number of end devices |
| `deadline_slack_factor` | 1.5 | Deadline = release + slack × min_ToA |
| `toa_mode` | "real" | "real" (Semtech formula) or "synthetic" |

## Results (Default Configuration)

| Metric | Value |
|---|---|
| Total packets | 234 |
| Scheduled | 101 (43.2%) |
| Dropped | 133 (56.8%) |
| Timeline span | 90,072 ms / 100,000 ms |
| Machine load makespan | 1,302 ms |
| Exact OPT (Branch-and-Bound) | 800 ms |
| **Approximation ratio** | **1.6275 ≤ 2.0 ✅** |
| Max concurrent demod | 8/8 ✅ |

## Project Structure

```
BTP/
├── config.json                  # Simulation parameters
├── main.py                      # Entry point
├── config_loader.py             # Config parsing and validation
├── data_structures.py           # Packet, Machine, ScheduleResult
├── lorawan_toa.py               # Semtech SX1276 ToA formula + cost matrix
├── packet_generator.py          # Harmonic periodic traffic generation
├── segment_tree.py              # Lazy-propagation max segment tree
├── stats.py                     # Per-SF, per-channel, aggregate metrics
├── output_writer.py             # JSON output
├── scheduler/
│   └── lorawan_scheduler.py     # Algorithm 3: full scheduling pipeline
├── approximation/
│   ├── binary_search.py         # Outer binary search over w
│   ├── truemper.py              # Algorithm 2: Unsplittable-Truemper
│   ├── blocking_flow.py         # Algorithm 1: Unsplittable-Blocking-Flow
│   └── graph_utils.py           # Dijkstra, BFS, admissible graph
├── validator/
│   ├── invariant_checker.py     # Schedule validity checks
│   ├── ilp_solver.py            # PuLP ILP solver with B&B fallback
│   └── bruteforce_comparator.py # Exact B&B + naive brute-force verifier
├── tests/
│   └── test_scheduler.py        # 8 unit/integration tests
└── output/
    ├── schedule.json             # Generated schedule
    └── stats.json                # Generated statistics
```

## References

- M. Gairing, B. Monien, A. Woclaw, *"A faster combinatorial approximation algorithm for scheduling unrelated parallel machines"*, Theoretical Computer Science, 2007.
- Semtech, *"LoRa Modem Designer's Guide"*, AN1200.13, §4.1.
