# Function Index

## Entry Points

| File | Function | Description |
|---|---|---|
| `main.py` | `main()` | Full simulation pipeline: config → generate → schedule → validate → output |
| `run_baseline_comparison.py` | `main()` | Compare all algorithms on single instance |
| `run_stress_test.py` | `main()` | 5-suite adversarial stress testing |
| `simulate_scaling.py` | `main()` | Large-scale simulation n=100 to 10,000 |
| `plot_scaling_results.py` | `main()` | Generate publication plots from simulation data |
| `plot_stress_test.py` | `main()` | Generate adversarial bar charts |

---

## Core Algorithm Functions

### approximation/binary_search.py
| Function | Signature | Returns |
|---|---|---|
| `find_2approx_assignment` | `(n, m, P, C, b, H_ms)` | `(alpha, w_star)` or `(None, 0)` |

### approximation/truemper.py
| Function | Signature | Returns |
|---|---|---|
| `unsplittable_truemper` | `(n, m, P, C, w, b, alpha?)` | `List[int]` (assignment) or `None` |

### approximation/blocking_flow.py
| Function | Signature | Returns |
|---|---|---|
| `_build_helpful_path` | `(n, m, v0_j, adj, h, loads, P, w)` | `List[int]` (path) or `None` |
| `unsplittable_blocking_flow` | `(n, m, alpha, loads, adj, P, w)` | `(alpha, phases)` |

### approximation/graph_utils.py
| Function | Signature | Returns |
|---|---|---|
| `compute_loads` | `(n, m, P, alpha)` | `List[int]` — machine loads |
| `dijkstra_to_sinks` | `(n, m, P, C, w, alpha, pi_job, pi_mach, sinks)` | `(d_job, d_mach)` distances |
| `build_admissible_graph` | `(n, m, P, C, w, alpha, pi_job, pi_mach)` | `Dict[int, List[int]]` adjacency |
| `bfs_heights` | `(total, n, adj, sinks)` | `List[float]` heights |
| `get_admissible_successors` | `(u, adj, h)` | `List[int]` sorted successors |

---

## Scheduler

### scheduler/energy_optimizer.py
| Function | Signature | Returns |
|---|---|---|
| `energy_optimal_downshift` | `(n, m, P, E, alpha, w_star, machines, H_ms?)` | `(alpha_star, energy_stats)` |

### scheduler/lorawan_scheduler.py
| Function | Signature | Returns |
|---|---|---|
| `_build_edf_timeline_with_demod` | `(packets, machines, P, alpha, H_ms, max_demod, candidate_ids)` | `(entries, deadline_viols, demod_viols)` |
| `lorawan_hypercycle_scheduler` | `(packets, machines, P_full, H_ms, max_demod, check_invariants, E_full?, enable_energy_opt?)` | `ScheduleResult` |

### scheduler/cyclic_hypercycle_wrapper.py
| Function | Signature | Returns |
|---|---|---|
| `run_cyclic_hypercycle_scheduler` | `(packets, machines, P_full, config, E_full?, check_invariants?, enable_energy_opt?)` | `CyclicScheduleResult` |

---

## Data & Config

### lorawan_energy.py
| Function | Signature | Returns |
|---|---|---|
| `compute_phy_payload_len` | `(app_payload_bytes, fopts_bytes?)` | `int` (bytes) |
| `compute_semtech_toa_s` | `(phy_payload_bytes, sf, bw_hz?, ...)` | `float` (seconds) |
| `compute_semtech_toa_ms` | `(phy_payload_bytes, sf, bw_hz?, ...)` | `float` (milliseconds) |
| `compute_class_a_cycle_energy` | `(app_payload_bytes, sf, t_cycle_s, ...)` | `(t_tx_s, e_tx_j, e_cycle_j, i_avg_a)` |
| `estimate_battery_life_years` | `(i_avg_a, battery_capacity_mah?, derating_factor?)` | `float` (years) |
| `compute_energy_matrix` | `(packets, machines, config, P)` | `List[List[float]]` E[n][m] (mJ) |

### lorawan_toa.py
| Function | Signature | Returns |
|---|---|---|
| `compute_toa_ms` | `(payload_bytes, sf, bw_hz, ...)` | `float` (ms) |
| `compute_toa_matrix` | `(packets, machines, config)` | `List[List[int]]` P[n][m] |
| `compute_cost_matrix` | `(P, m)` | `List[List[int]]` C[n][m] |

### packet_generator.py
| Function | Signature | Returns |
|---|---|---|
| `create_machines` | `(config)` | `List[Machine]` |
| `generate_packets` | `(config, machines)` | `List[Packet]` |

### config_loader.py
| Function | Signature | Returns |
|---|---|---|
| `load_config` | `(path)` | `SimConfig` |

---

## Baselines

### baselines.py
| Function | Signature | Returns |
|---|---|---|
| `random_assignment` | `(n, m, P, seed)` | `(alpha, makespan)` or `(None, 0)` |
| `greedy_least_loaded` | `(n, m, P)` | `(alpha, makespan)` or `(None, 0)` |
| `min_min` | `(n, m, P)` | `(alpha, makespan)` or `(None, 0)` |
| `max_min` | `(n, m, P)` | `(alpha, makespan)` or `(None, 0)` |
| `run_all_baselines` | `(n, m, P, seed)` | `dict` of results |

---

## Validation

### validator/invariant_checker.py
| Function | Signature | Returns |
|---|---|---|
| `check_assignment_feasibility` | `(n, m, P, alpha, w)` | raises `InvariantError` |
| `check_reduced_cost_optimality` | `(n, m, P, C, w, alpha, pi_job, pi_mach)` | raises `InvariantError` |
| `check_load_bounds` | `(m, loads, w, label)` | `dict` info |
| `check_schedule_validity` | `(entries, machines, H_ms, max_demod)` | `dict` or raises `InvariantError` |

### validator/ilp_solver.py
| Function | Signature | Returns |
|---|---|---|
| `ilp_optimal_makespan` | `(n, m, P, time_limit_s)` | `(opt, alpha)` or `(None, None)` |

### validator/feasibility_certificate.py
| Function | Signature | Returns |
|---|---|---|
| `compute_schedulability_certificate` | `(packets, machines, P, H_ms, E?, tau_ms?)` | `dict` (LB, X_tight, safety margin, verdict) |

### validator/bruteforce_comparator.py
| Function | Signature | Returns |
|---|---|---|
| `naive_bruteforce_makespan` | `(n, m, P)` | `(cmax, assignment, elapsed)` |
| `theoretical_lower_bound` | `(n, m, P)` | `int` |
| `compute_greedy_lpt_ub` | `(n, m, P)` | `(ub, assignment)` |
| `exact_optimal_makespan` | `(n, m, P, machines?, initial_ub?, time_limit_s?)` | `(cmax, assignment, elapsed)` |
| `verify_bruteforce_soundness` | `(num_trials)` | `bool` |
| `run_makespan_comparison_benchmark` | `(config_path)` | `dict` of results |
| `compare_scheduled_packets_opt` | `(config_path)` | `dict` of results |

---

## Utilities

### segment_tree.py — `SegmentTree`
| Method | Complexity | Description |
|---|---|---|
| `__init__(n)` | O(n) | Create tree over [0, n-1] |
| `range_add(l, r, val)` | O(log n) | Add val to [l, r] |
| `range_max(l, r)` | O(log n) | Max value in [l, r] |
| `reset()` | O(n) | Zero entire tree |

### stats.py
| Function | Signature | Returns |
|---|---|---|
| `compute_stats` | `(result, packets, machines, P_full, H_ms, max_demod, ilp_opt?)` | `dict` |

### output_writer.py
| Function | Signature | Returns |
|---|---|---|
| `write_schedule` | `(result, path)` | writes JSON |
| `write_stats` | `(stats, path)` | writes JSON |

