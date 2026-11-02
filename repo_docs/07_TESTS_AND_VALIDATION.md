# Tests & Validation

## Test Suite (tests/test_scheduler.py)

18 tests covering unit, integration, correctness, energy, and homogeneous/heterogeneous cyclic executive verification.

### Test Descriptions

| # | Test | What It Verifies |
|---|---|---|
| 1 | `test_segment_tree` | Segment tree range_add/range_max correctness (overlap accumulation) |
| 2 | `test_lorawan_toa_formula` | ToA formula produces realistic values (SF7, 10B → 40–45 ms) |
| 3 | `test_2approximation_makespan_guarantee` | 2-approx on 20 packets: max_load ≤ 2·w_star |
| 4 | `test_empty_packets` | Empty input: feasible=False, 0 entries |
| 5 | `test_small_instance` | 5 packets: all scheduled, none dropped |
| 6 | `test_end_to_end_scheduler` | Full 234-packet run: feasible, entries + drops = n, all invariants pass |
| 7 | `test_exact_bruteforce_soundness` | 15 random instances: naive brute force == B&B (100% exact match in CI test) |
| 8 | `test_exact_bruteforce_makespan_guarantee` | 12 packets: 2-approx ratio ≤ 2.0 vs exact OPT |
| 9 | `test_lorawan_energy_model_datasheet_values` | Exact Semtech SX1276 datasheet verification: SF7 ToA = 61.696 ms, SF12 ToA = 1482.752 ms; Casals Class A cycle energy (~27.4 mJ vs ~233.7 mJ) |
| 10 | `test_energy_optimizer_preserves_2approximation` | Phase 1.5 strictly preserves makespan ≤ 2·w* and individual feasibility P[i][j] ≤ w* while decreasing energy |
| 11 | `test_end_to_end_energy_scheduler` | Full pipeline execution with energy optimization enabled; valid metrics & invariants |
| 12 | `test_cyclic_divisibility_validation` | Enforces harmonic divisibility: raises ValueError if H % tau != 0 |
| 13 | `test_cyclic_carryover_active_recovery_under_congestion` | Transient drops under congestion in cycle 0 carried over and recovered in cycle 1 |
| 14 | `test_cyclic_scheduler_preserves_2approximation_per_cycle` | In every minor cycle k, machine makespan C_max^(k) <= 2 * w_k* strictly holds |
| 15 | `test_cyclic_executive_end_to_end_validation` | Full 10-minor-cycle end-to-end execution, global demod limit <= 8, non-preemption and deadlines valid |
| 16 | `test_heterogeneous_cyclic_duration_sum_validation` | Enforces partition invariant: raises ValueError if sum(durations) != H |
| 17 | `test_heterogeneous_cyclic_scheduler_end_to_end` | End-to-end execution with variable-length frames [10s, 15s, 25s, 50s], 2-approx bound holds in every frame |
| 18 | `test_heterogeneous_carryover_active_recovery` | Carryover and active recovery between variable-length frames (300 ms -> 700 ms) |

### Running Tests

```bash
python -m pytest tests/ -v
```

---

## Invariant Checker (validator/invariant_checker.py)

### 4 Invariants Checked

#### 1. Assignment Feasibility
Every job must be assigned to a machine with ToA ≤ w:
```
P[i][α(i)] ≤ w  for all i
```

#### 2. Reduced-Cost Optimality
All reduced costs in the residual graph must be ≥ 0:
- Backward: -C[i][j] - π_mach[j] + π_job[i] ≥ -1
- Forward: C[i][j] - π_job[i] + π_mach[j] ≥ -1

#### 3. Load Bounds (informational)
Reports M⁺/M⁰/M⁻ partition sizes and max load.

#### 4. Schedule Validity (final check)
- **Per-channel non-preemption**: No overlaps on same machine
- **Deadline compliance**: finish_time ≤ deadline for all scheduled
- **Demod limit**: Max concurrent demodulations ≤ 8 (event sweep)

### Error Handling

```python
class InvariantError(Exception):
    """Raised when an algorithm invariant is violated."""
```

---

## Bruteforce Verification (validator/bruteforce_comparator.py)

### Naive Brute Force (`naive_bruteforce_makespan`)
- **Zero heuristics, zero pruning** — evaluates every possible assignment
- Cartesian product: Π_{i=0}^{n-1} {j : P[i][j] < INF}
- Used as absolute mathematical ground truth

### Exact Branch-and-Bound (`exact_optimal_makespan`)
- LPT (Longest Processing Time first) greedy seed for tight upper bound
- Pruning: capacity check (loads[j] + P[i][j] ≥ best_cmax) and volume lower bound
- Column-signature symmetry breaking: skip isomorphic empty machines
- Time limit: configurable (default 120s)

### Soundness Verification (`verify_bruteforce_soundness`)
- 25 randomised trials (n=3–7, m=2–4) in standalone function (`test_exact_bruteforce_soundness` runs 15 in pytest)
- Confirms naive == B&B on every trial
- Gives mathematical proof that the B&B solver is exact

### Benchmark Runner (`run_makespan_comparison_benchmark`)
- Tests n = 5, 8, 10, 12, 15, 18, 20 from the full packet set
- Compares 2-approx vs exact OPT on each size
- All ratios confirmed ≤ 2.0

### Scheduled Packet Comparison (`compare_scheduled_packets_opt`)
- Takes the 101 scheduled packets from output/schedule.json
- Computes theoretical lower bound, LPT upper bound, exact B&B OPT
- Reports empirical approximation ratio

---

## Validation Flow in main.py

```
1. Run scheduler → ScheduleResult
2. If config.validation.check_invariants and entries exist:
   → check_schedule_validity(entries, machines, H_ms, max_demod)
   → Reports: non-preemption OK, deadlines OK, max concurrent demod X/8
3. If --ilp:
   → ilp_optimal_makespan(n, m, P)
   → Reports: exact OPT, ratio, ≤ 2.0 guarantee
```

