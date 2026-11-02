# Data Structures Reference

## Core Types (data_structures.py)

### `Packet`
Represents a real-time packet to be scheduled within the hypercycle.

| Field | Type | Description |
|---|---|---|
| `id` | int | Unique packet identifier (0-indexed) |
| `release_time` | int (ms) | Earliest transmission start |
| `deadline` | int (ms) | Latest acceptable finish time |
| `priority` | float | Higher = more important (1.0 to 10.0) |
| `payload_size` | int (bytes) | Application payload size |
| `device_id` | int | Source end-device identifier |
| `period` | int (ms) | Repetition period of parent stream |

### `Machine`
A logical communication resource = (SF, Channel) pair.

| Field | Type | Description |
|---|---|---|
| `id` | int | Machine index (0 to m-1) |
| `sf` | int | Spreading factor (7–12) |
| `channel` | int | 0-based channel index |
| `label` | str (property) | e.g. "SF7_CH0" |

**Machine indexing**: Channel-major order. Machine ID = channel × N_sf + (SF - 7).

### `ScheduleEntry`
One scheduled transmission in the final output.

| Field | Type | Description |
|---|---|---|
| `packet_id` | int | Packet ID |
| `machine_id` | int | Assigned machine |
| `start_time` | int (ms) | Scheduled start |
| `finish_time` | int (ms) | Scheduled finish = start + ToA |
| `deadline` | int (ms) | Packet deadline |
| `deadline_met` | bool | Always True for scheduled packets |
| `sf` | int | Spreading factor used |
| `channel` | int | Channel used |

### `ScheduleResult`
Complete output of the scheduling algorithm.

| Field | Type | Description |
|---|---|---|
| `entries` | List[ScheduleEntry] | All scheduled transmissions |
| `dropped_packet_ids` | List[int] | IDs of dropped packets |
| `makespan_ms` | int | Timeline span (latest finish time) |
| `machine_makespan_ms` | int | Phase 1 machine load makespan (max Σ p_ij) |
| `approx_ratio_w` | int | The w* found by binary search |
| `feasible` | bool | Whether schedule is valid |
| `energy_stats` | dict | Phase 1.5 energy metrics |

### `CyclicScheduleResult` (extends `ScheduleResult`)
Output of the Cyclic Executive hypercycle wrapper.

| Field | Type | Description |
|---|---|---|
| `recovered_packet_ids` | List[int] | IDs of packets saved and scheduled via carryover |
| `unrecoverable_dropped_ids` | List[int] | IDs of packets whose deadlines expired or exceeded hop limit |
| `cycle_results` | List[dict] | Per-cycle metrics (arrivals, carried-in, scheduled, recovered, drops, loads) |
| `num_minor_cycles` | int | Total number of minor cycles ($K = H // \tau$) |
| `minor_cycle_ms` | int | Minor cycle duration in ms ($\tau$) |
| `carryover_stats` | dict | Aggregated recovery rate % and carryover counts |

### `AlgorithmState`
Internal mutable state for the 2-approximation algorithm.

| Field | Type | Description |
|---|---|---|
| `n, m` | int | Jobs and machines count |
| `alpha` | List[int] | α[i] = machine index for job i |
| `pi_job, pi_mach` | List[int] | Node potentials |
| `loads` | List[int] | loads[j] = total ToA on machine j |
| `w` | int | Current candidate makespan |
| `b` | float | Rounding base = 1 + 1/m |
| `log_b_m` | float | Potential ceiling = log_b(m) |

Methods:
- `compute_loads(P)` — recompute loads from α and P
- `get_M_plus()` — machines with load ≥ 2w+1
- `get_M_zero()` — machines with load in [w+1, 2w]
- `get_M_minus()` — machines with load ≤ w

### Sentinel Value

```python
INF = 10**18  # Sentinel for infeasible ToA entries
```

---

## Configuration Types (config_loader.py)

### `SimConfig` (top-level)
| Field | Type |
|---|---|
| `network` | NetworkConfig |
| `gateway` | GatewayConfig |
| `traffic` | TrafficConfig |
| `lora_phy` | LoRaPhyConfig |
| `toa_mode` | str ("real" \| "synthetic") |
| `time_resolution_ms` | int |
| `validation` | ValidationConfig |
| `output` | OutputConfig |
| `energy` | EnergyConfig |
| `num_machines` (property) | int = num_channels × len(spreading_factors) |

### `EnergyConfig`
- `enable_energy_optimization`: true (activates Phase 1.5)
- `supply_voltage_v`: 3.3 V
- `i_tx_a`: 0.044 A (44 mA transmit)
- `i_rx_a`: 0.0115 A (11.5 mA receive)
- `i_stby_a`: 0.0016 A (1.6 mA standby)
- `i_sleep_a`: 2.0e-6 A (2 µA sleep)
- `i_mcu_a`: 0.005 A (5 mA MCU)
- `t_mcu_s`: 0.05 s (50 ms processing)
- `i_sens_a`: 0.003 A (3 mA sensor)
- `t_sens_s`: 0.1 s (100 ms sensing)
- `t_rx_s`: 0.03 s (30 ms preamble window)
- `mac_header_bytes`: 13 (LoRaWAN MAC overhead)

### `NetworkConfig`
- `num_channels`: 8
- `spreading_factors`: [7, 8, 9, 10, 11, 12]
- `hypercycle_duration_s`: 100 → `hypercycle_duration_ms`: 100000

### `TrafficConfig`
- `num_end_devices`: 50
- `payload_sizes_bytes`: [10, 20, 30, 50]
- `periods_s`: [10, 20, 50, 100] (must divide H)
- `priority_range`: [1, 10]
- `seed`: 42
- `deadline_slack_factor`: 1.5

### `LoRaPhyConfig`
- `bandwidth_hz`: 125000
- `coding_rate`: 1 (CR 4/5)
- `preamble_symbols`: 8
- `crc_enabled`: true
- `explicit_header`: true
- `low_data_rate_optimize`: "auto" (enabled when T_sym > 16 ms → SF11, SF12)

---

## Segment Tree (segment_tree.py)

Max segment tree with lazy propagation over integer domain [0, n-1].

- **4n nodes**, `__slots__` optimized
- `range_add(l, r, val)` — O(log n): add val to every position in [l, r]
- `range_max(l, r)` — O(log n): return max value in [l, r]
- `reset()` — zero out entire tree

Used in Phase 2 to track gateway demodulation occupancy Ω(t) across all H_ms = 100,000 time slots. Before placing a packet at [s, f), query `range_max(s, f-1)`. If peak ≥ 8, shift forward. Otherwise, `range_add(s, f-1, +1)`.

---

## ToA Matrix & Cost Matrix (lorawan_toa.py)

### `compute_toa_ms(payload_bytes, sf, bw_hz, ...)`
Implements the exact Semtech SX1276 formula:
- Symbol duration: T_sym = 2^SF / BW
- Preamble: T_preamble = (n_preamble + 4.25) × T_sym
- Payload symbols: N_payload = 8 + max(ceil((8L - 4·SF + 28 + CRC - 20·IH) / (4·(SF - 2·DE))) × (CR + 4), 0)
- Total: (T_preamble + N_payload × T_sym) × 1000 ms

### `compute_toa_matrix(packets, machines, config)` → P[n][m]
- P[i][j] = integer ToA in ms for packet i on machine j
- INF (10^18) if infeasible

### `compute_cost_matrix(P, m)` → C[n][m]
Truemper's logarithmic transformation:
- b = 1 + 1/m
- C[i][j] = floor(log_b(P[i][j]))
- C[i][j] = INF if P[i][j] = INF

### Representative ToA Values (125 kHz, CR 4/5, explicit header, CRC enabled)

The table below reflects the exact integer ceiling values ($p_{ij} = \lceil \text{ToA} \rceil$ ms) stored in matrix $P$ by `compute_toa_matrix` (with Low Data Rate Optimization automatically enabled on SF11 and SF12):

| SF | 10 B | 20 B | 30 B | 50 B | Raw Float (10 B / 50 B) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| SF7 | 42 ms | 57 ms | 72 ms | 98 ms | 41.2 ms / 97.5 ms |
| SF8 | 73 ms | 103 ms | 124 ms | 175 ms | 72.2 ms / 174.6 ms |
| SF9 | 145 ms | 186 ms | 227 ms | 329 ms | 144.4 ms / 328.7 ms |
| SF10 | 289 ms | 371 ms | 453 ms | 617 ms | 288.8 ms / 616.4 ms |
| SF11 | 578 ms | 742 ms | 906 ms | 1315 ms | 577.5 ms / 1314.8 ms |
| SF12 | 992 ms | 1319 ms | 1647 ms | 2302 ms | 991.2 ms / 2301.9 ms |

*Note: In simulation logs, Min ToA is 42 ms (SF7, 10 B) and Max ToA is 2302 ms (SF12, 50 B) with a mean of 508.8 ms across all packet-machine combinations.*

