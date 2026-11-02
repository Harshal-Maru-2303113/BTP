# Output Format Reference

## Generated Files

### output/schedule.json

```json
{
  "feasible": true,
  "makespan_ms": 90072,              // Timeline span (latest finish time)
  "machine_makespan_ms": 1302,       // Max machine load (Phase 1 output)
  "approx_w_star": 775,              // Binary search threshold
  "num_scheduled": 101,
  "num_dropped": 133,
  "energy_stats": {                  // Phase 1.5 energy metrics
    "initial_energy_mj": 6493.8,
    "optimized_energy_mj": 6493.8,
    "energy_saved_mj": 0.0,
    "energy_reduction_pct": 0.0,
    "downshift_moves": 320,
    "scheduled_energy_mj": 2649.6
  },
  "schedule": [
    {
      "packet_id": 202,
      "machine_id": 0,
      "sf": 7,
      "channel": 0,
      "start_time_ms": 0,
      "finish_time_ms": 42,
      "deadline_ms": 63,
      "deadline_met": true
    }
  ],
  "dropped_packet_ids": [0, 1, 2, ...]
}
```

### output/stats.json

Sections:
1. **`summary`**: total/scheduled/dropped counts, makespans, utilisation
2. **`ilp_comparison`**: exact OPT, empirical ratio, within_2x_guarantee
3. **`per_sf`**: packets/airtime/avg_toa per SF (7–12)
4. **`per_channel`**: packets/airtime/utilisation per channel (0–7)
5. **`per_machine`**: load per (SF, CH) pair (48 entries)
6. **`demod_profile`**: max concurrent, limit, within_limit
7. **`dropped_packets_detail`**: per-packet drop forensics
8. **`energy`**: Phase 1.5 initial/optimized energy, savings, scheduled radio energy
9. **`timing`**: toa_computation_s, scheduling_s

### output/baseline_comparison.json
Algorithm comparison results with makespans, ratios, times.

### output/stress_test_results.json
5 suites of adversarial benchmark results.

### output/large_scale_simulation.json
Aggregated statistics across n=100 to n=10,000 with 10 trials each.

### output/*.png
Publication-quality plots:
- `makespan_scaling.png` — all 5 algorithms
- `makespan_zoom_scaling.png` — coordinated schedulers only
- `ratio_scaling.png` — approximation ratio vs 2.0 bound
- `runtime_scaling.png` — log-log execution time
- `simulation_dashboard.png` — 2×2 composite
- `adversarial_min_min_failure.png` — Suite 3 bar chart
- `adversarial_unrelated_failure.png` — Suite 5 bar chart

---

## Console Output (main.py)

Structured sections:
```
[Config]      — channels, SFs, machines, hypercycle, max demod
[Traffic]     — end devices, total packets, machines
[ToA Matrix]  — min/max/mean ToA, computation time
[Scheduling]  — completion time, feasible, scheduled/dropped, makespan, w*
[ILP Solver]  — (if --ilp) exact OPT, ratio, ≤ 2.0 check
[Validation]  — non-preemption, deadlines, demod limit
[Output]      — file paths
SUMMARY       — final counts, timeline span, machine makespan, ratio
```

---

## Key Metrics to Understand

| Metric | What It Means |
|---|---|
| `makespan_ms` | Latest chronological finish time across the timeline (calendar span, 90,072 ms / 100,000 ms) |
| `machine_makespan_ms` | Maximum total airtime assigned to any single machine (1,302 ms for 101 scheduled packets; 1,545 ms for all 234 packets in baseline runner) |
| `approx_w_star` | Lower bound certificate: OPT ≥ w* (binary search critical threshold = 775 ms) |
| `machine_makespan / OPT` | Empirical approximation ratio (1,302 / 800 = 1.6275 on scheduled subset; 1,545 / 933 = 1.656 on full set; guaranteed ≤ 2.0) |
| `max_concurrent_demod` | Peak simultaneous receptions (must be ≤ 8; default run reaches exactly 8/8) |
| `drop_rate_pct` | Percentage of packets dropped (56.84%, 133/234 dropped due to $t=0$ synchronous release hardware saturation) |

