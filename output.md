# Output Specification & Verification Guide

This document describes all output formats, schemas, diagnostic metrics, and validation logs produced by the **LoRaWAN Hypercycle Scheduler**.

---

## Table of Contents
1. [Overview of Output Deliverables](#1-overview-of-output-deliverables)
2. [Schedule File (`output/schedule.json`)](#2-schedule-file-outputschedulejson)
3. [Statistics File (`output/stats.json`)](#3-statistics-file-outputstatsjson)
4. [Terminal Console Output](#4-terminal-console-output)
5. [Schedule Validity and System Invariants](#5-schedule-validity-and-system-invariants)
6. [Metric Interpretation: Machine Load vs. Timeline Span](#6-metric-interpretation-machine-load-vs-timeline-span)

---

## 1. Overview of Output Deliverables

The scheduler generates three primary forms of output:

1. **`output/schedule.json`**:
   The exact, deterministic transmission plan for every successfully scheduled packet, including assigned logical machine, channel, spreading factor, transmission start time, and finish time in milliseconds.
2. **`output/stats.json`**:
   Comprehensive quantitative analysis covering drop rates, makespan, exact Branch-and-Bound benchmarking, per-SF and per-channel utilization, concurrent demodulation profiles, and dropped packet forensics.
3. **Standard Console Output (`stdout`)**:
   Human-readable execution log displaying configuration, phase timings, invariant checks, and performance summaries.

---

## 2. Schedule File (`output/schedule.json`)

The schedule file contains the exact placement of all scheduled packets and the list of dropped packet IDs.

### Top-Level Schema

| Field | Type | Description |
| :--- | :--- | :--- |
| `feasible` | `bool` | `true` if all candidate packets in the final schedule satisfy non-preemption, deadlines, and demodulation ceilings. |
| `makespan_ms` | `int` | **Timeline Calendar Span** (C_max_time): The latest completion time of any transmission along the hypercycle timeline (0 ≤ C_max_time ≤ H). |
| `machine_makespan_ms` | `int` | **Machine Load Makespan** (C_max_mach): The maximum cumulative transmission duration assigned to any single channel resource. |
| `approx_w_star` | `int` | The critical candidate makespan parameter w* converged upon by the Phase 1 binary search. |
| `num_scheduled` | `int` | Total count of packets successfully assigned and scheduled. |
| `num_dropped` | `int` | Total count of packets dropped due to physical hardware/deadline conflicts. |
| `schedule` | `List[Object]` | Array of individual packet transmission assignments (ordered by channel and start time). |
| `dropped_packet_ids`| `List[int]` | Sorted list of unique packet IDs that could not be scheduled. |

### Schedule Entry Schema

Each object within the `schedule` array represents one transmission slot:

| Field | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `packet_id` | `int` | — | Unique packet instance identifier (0 ≤ id < n). |
| `machine_id` | `int` | — | Logical resource identifier (0 ≤ mid < m). |
| `sf` | `int` | — | Spreading factor utilized (SF in [7, 12]). |
| `channel` | `int` | — | Carrier frequency channel index (0 ≤ ch < N_ch). |
| `start_time_ms`| `int` | ms | Scheduled transmission start instant (s_i ≥ r_i). |
| `finish_time_ms`| `int` | ms | Scheduled transmission completion instant (f_i = s_i + p_ij). |
| `deadline_ms` | `int` | ms | Absolute deadline boundary (D_i). |
| `deadline_met` | `bool` | — | Verification invariant (f_i ≤ D_i). Always `true` for scheduled entries. |

### Concrete JSON Example

```json
{
  "feasible": true,
  "makespan_ms": 90072,
  "machine_makespan_ms": 1302,
  "approx_w_star": 775,
  "num_scheduled": 101,
  "num_dropped": 133,
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
    },
    {
      "packet_id": 232,
      "machine_id": 0,
      "sf": 7,
      "channel": 0,
      "start_time_ms": 42,
      "finish_time_ms": 140,
      "deadline_ms": 147,
      "deadline_met": true
    },
    {
      "packet_id": 203,
      "machine_id": 0,
      "sf": 7,
      "channel": 0,
      "start_time_ms": 20000,
      "finish_time_ms": 20042,
      "deadline_ms": 20063,
      "deadline_met": true
    }
  ],
  "dropped_packet_ids": [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
  ]
}
```

---

## 3. Statistics File (`output/stats.json`)

The statistics file provides a complete quantitative breakdown across multiple system dimensions.

### Section Breakdown

#### 1. `summary`
High-level KPIs for the simulation:
* `total_packets`: Total packet instances generated across the hypercycle.
* `scheduled_packets`: Successfully scheduled packet count.
* `dropped_packets`: Dropped packet count.
* `drop_rate_pct`: Percentage of dropped packets ((dropped / total) × 100%).
* `makespan_ms`: Latest chronological completion time along the timeline (C_max_time).
* `machine_makespan_ms`: Maximum accumulated load on any single machine (C_max_mach).
* `hypercycle_ms`: Configured hypercycle horizon (H).
* `makespan_utilisation_pct`: Hypercycle timeline usage ((C_max_time / H) × 100%).
* `approx_w_star`: Candidate makespan w* identified by binary search.
* `feasible`: Overall schedule feasibility flag.

#### 2. `ilp_comparison`
Validation against the exact optimum solver:
* `ilp_optimal_makespan_ms`: Exact optimum machine load makespan OPT(P) computed via Branch-and-Bound.
* `approx_machine_makespan_ms`: Machine load makespan achieved by the 2-approximation algorithm.
* `timeline_makespan_ms`: Calendar finish span of the schedule.
* `empirical_approx_ratio`: Observed approximation ratio:
  ```
  Ratio = C_max_mach / OPT(P)
  ```
* `within_2x_guarantee`: Boolean assertion confirming Ratio ≤ 2.0000.

#### 3. `per_sf`
Breakdown across spreading factors SF7 through SF12:
* `num_packets`: Count of packets scheduled on this spreading factor.
* `total_airtime_ms`: Cumulative transmission airtime consumed.
* `avg_toa_ms`: Average packet airtime on this SF.

#### 4. `per_channel`
Breakdown across frequency channels CH0 through CH7:
* `num_packets`: Count of packets assigned to this RF channel.
* `total_airtime_ms`: Total airtime scheduled on this channel.
* `utilisation_pct`: Channel duty cycle utilization ((airtime / H) × 100%).

#### 5. `per_machine`
Fine-grained load distribution for all m = 48 logical machines (`SF7_CH0` to `SF12_CH7`):
* `machine_id`: Integer machine index.
* `num_packets`: Packets assigned to this specific machine.
* `total_airtime_ms`: Cumulative airtime on this machine.
* `utilisation_pct`: Duty cycle utilization of this machine.

#### 6. `demod_profile`
Gateway concurrent demodulation analysis:
* `max_concurrent`: Peak observed concurrent demodulations across [0, H]. Strictly ≤ 8.
* `histogram`: Frequency distribution of concurrent transmissions (number of millisecond slots where k concurrent packets were active).

#### 7. `dropped_packets_detail`
Exhaustive forensic record of every dropped packet, listing:
* `packet_id`: Unique identifier.
* `device_id`: Generating device identifier.
* `release_time_ms`: Packet release instant.
* `deadline_ms`: Absolute deadline.
* `priority`: Criticality level.
* `payload_bytes`: Application payload size.
* `drop_reason`: Cause of drop (e.g. `synchronous_release_bottleneck_t0`, `sf_deadline_infeasible`, `demod_ceiling_exceeded`).

#### 8. `timing`
Wall-clock profiling for simulation stages:
* `toa_computation_s`: Time taken to build the n × m airtime matrix.
* `scheduling_s`: Time taken to execute Phase 1, Phase 2, and Phase 3.

---

## 4. Terminal Console Output

When running `main.py --ilp`, the scheduler produces structured console output:

```text
============================================================
  LoRaWAN Hypercycle Scheduler Simulation
============================================================

[Config]
  Channels       : 8
  SFs            : [7, 8, 9, 10, 11, 12]
  Machines (m)   : 48
  Hypercycle (H) : 100s (100000 ms)
  Max demod      : 8
  ToA mode       : real

[Traffic Generation]
  End devices    : 50
  Total packets  : 234
  Machines       : 48

[ToA Matrix]  (234 × 48)
  Min ToA  : 41 ms
  Max ToA  : 2466 ms
  Mean ToA : 438.2 ms
  Computed in 0.002s

[Scheduling] Running LoRaWAN Hypercycle Scheduler...
  Completed in 0.412s
  Feasible     : True
  Scheduled    : 101/234
  Dropped      : 133
  Makespan     : 90072 ms
  w* (approx)  : 775

[ILP Solver] Computing optimal makespan (may be slow)...
  Exact OPT Makespan  : 800 ms
  2-Approx Load       : 1302 ms
  Timeline Span       : 90072 ms
  Ratio (Load / OPT)  : 1.6275
  ≤ 2.0 Guarantee     : YES
  Solved in           : 0.084s

[Validation]
  Per-channel non-preemption : OK
  Deadline compliance        : OK
  Max concurrent demod       : 8/8
  Demod limit OK             : True

[Output]
  Writing schedule to: output/schedule.json
  Writing stats to: output/stats.json

============================================================
  SIMULATION COMPLETE
============================================================
  Packets: 101 scheduled, 133 dropped (56.8%)
  Timeline Span: 90072 ms / 100000 ms (90.1%)
  Machine Load Makespan: 1302 ms
  Approximation ratio: 1.6275 (guarantee ≤ 2.0)
```

---

## 5. Schedule Validity and System Invariants

Every generated schedule is verified against four strict invariants before acceptance:

### 1. Per-Channel Non-Preemption Invariant
No two packets assigned to the same machine M_j = <SF_j, CH_j> may overlap in time:
```
For all i ≠ k with alpha(i) = alpha(k) = j:  [s_i, f_i) ∩ [s_k, f_k) = empty
```

### 2. Real-Time Deadline Compliance Invariant
Every scheduled packet must finish transmission on or before its absolute deadline:
```
For all i in J_sched:  s_i ≥ r_i  and  f_i ≤ D_i
```

### 3. Gateway Demodulation Capacity Invariant
Across all m = 48 logical channels, the instantaneous number of active demodulations Omega(t) must never exceed the modem hardware capacity (N_demod_max = 8):
```
For all t in [0, H]:  Omega(t) ≤ 8
```
Verified efficiently in O(log H) time per packet using a lazy-propagated Segment Tree.

### 4. Approximation Guarantee Invariant
The machine load makespan C_max_mach produced by Phase 1 must not exceed twice the optimal makespan OPT(P) of the scheduled packets:
```
C_max_mach / OPT(P) ≤ 2.0000
```
Verified empirically against the exact Branch-and-Bound solver (ratio = 1.6275 ≤ 2.0).

---

## 6. Metric Interpretation: Machine Load vs. Timeline Span

It is essential to understand the distinction between the two makespan definitions reported by the simulation:

```text
Timeline Span:         |--------- Packet 1 ---------| ... [idle] ... |--- Packet 101 ---|   -> 90,072 ms
(Calendar hypercycle)  0                                                                H = 100,000 ms

Machine Load Makespan: |== Pkt 1 ==|== Pkt 2 ==|== Pkt 3 ==| ... |== Pkt 19 ==|              -> 1,302 ms
(Accumulated airtime)  0                                                      max channel
```

* **Machine Load Makespan (C_max_mach = 1,302 ms):**
  This measures **channel load concentration**—the cumulative airtime scheduled on the most heavily loaded channel (Channel 4). The combinatorial 2-approximation theorem of Gairing et al. applies directly to this metric, proving that no possible packet distribution could achieve a maximum channel load lower than 1302 / 2 = 651 ms (exact OPT is 800 ms, ratio is 1.6275).
* **Timeline Calendar Span (C_max_time = 90,072 ms):**
  This represents the latest chronological finish time across the 100-second hypercycle. Because packets are released periodically throughout the entire [0, 100 s] timeline (e.g. at t = 20 s, 50 s, 90 s), packets scheduled toward the end of the hypercycle naturally finish near 90 s.
