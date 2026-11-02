# Input Specification & Configuration Guide

This document describes all inputs, configuration options, data structures, and physical parameters used by the **LoRaWAN Hypercycle Scheduler**.

---

## Table of Contents
1. [Command-Line Interface (CLI)](#1-command-line-interface-cli)
2. [Configuration File (`config.json`)](#2-configuration-file-configjson)
3. [Gateway Machine Model](#3-gateway-machine-model)
4. [Traffic and Packet Generation Model](#4-traffic-and-packet-generation-model)
5. [Physical Time-on-Air (ToA) Matrix Calculation](#5-physical-time-on-air-toa-matrix-calculation)
6. [Input Validation and Invariants](#6-input-validation-and-invariants)

---

## 1. Command-Line Interface (CLI)

The simulation is executed via `main.py`. It accepts the following command-line flags:

```bash
python main.py [OPTIONS]
```

### Supported Arguments

| Flag | Long Option | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-c` | `--config` | `string` | `config.json` | Path to the JSON configuration file. |
| | `--ilp` | `flag` | `False` | Run the exact optimal solver (Branch-and-Bound / PuLP) to benchmark the 2-approximation makespan. |
| `-v` | `--verbose` | `flag` | `False` | Enable verbose diagnostic logging (per-SF ToA values, detailed progress). |

### Example Invocations

```bash
# Standard run using default config.json
python main.py

# Run with custom configuration
python main.py --config configs/heavy_traffic.json

# Run with exact optimum benchmarking and verbose logging
python main.py --ilp --verbose
```

---

## 2. Configuration File (`config.json`)

The entire simulation is parameterized through `config.json`. Below is the complete schema breakdown:

### Complete Annotated Example

```json
{
    "network": {
        "num_channels": 8,
        "spreading_factors": [7, 8, 9, 10, 11, 12],
        "hypercycle_duration_s": 100
    },
    "gateway": {
        "max_concurrent_demodulations": 8
    },
    "traffic": {
        "num_end_devices": 50,
        "payload_sizes_bytes": [10, 20, 30, 50],
        "periods_s": [10, 20, 50, 100],
        "priority_range": [1, 10],
        "seed": 42,
        "eligible_sf_mode": "all",
        "deadline_slack_factor": 1.5
    },
    "lora_phy": {
        "bandwidth_hz": 125000,
        "coding_rate": 1,
        "preamble_symbols": 8,
        "crc_enabled": true,
        "explicit_header": true,
        "low_data_rate_optimize": "auto"
    },
    "toa_mode": "real",
    "time_resolution_ms": 1,
    "validation": {
        "run_ilp_comparison": false,
        "check_invariants": true
    },
    "output": {
        "schedule_file": "output/schedule.json",
        "stats_file": "output/stats.json"
    }
}
```

### Detailed Field Descriptions

#### `network`
* **`num_channels`** (`int`, default: `8`):
  Number of orthogonal carrier frequency channels (N_ch). Standard multi-channel LoRaWAN gateways (e.g., Semtech SX1301/SX1302) support 8 concurrent radio channels.
* **`spreading_factors`** (`List[int]`, default: `[7, 8, 9, 10, 11, 12]`):
  List of supported spreading factors (N_sf). LoRa supports SF7 through SF12.
* **`hypercycle_duration_s`** (`int` or `float`, default: `100`):
  Duration of the scheduling hypercycle H in seconds. Converted internally to integer milliseconds (H_ms = H × 1000 = 100,000 ms).

#### `gateway`
* **`max_concurrent_demodulations`** (`int`, default: `8`):
  Maximum number of simultaneous packet receptions (N_demod_max) the gateway baseband DSP can process concurrently across all channels. Hardware limit for SX1301/SX1302 chips.

#### `traffic`
* **`num_end_devices`** (`int`, default: `50`):
  Number of active end-devices communicating with the gateway.
* **`payload_sizes_bytes`** (`List[int]`, default: `[10, 20, 30, 50]`):
  List of allowable application payload sizes in bytes. Devices sample uniformly from this set.
* **`periods_s`** (`List[int]`, default: `[10, 20, 50, 100]`):
  Allowable periodic transmission intervals in seconds. **Must divide H** to satisfy harmonic periodicity.
* **`priority_range`** (`[float, float]`, default: `[1, 10]`):
  Interval [Π_min, Π_max] from which device priorities are uniformly sampled. Higher numbers denote higher priority.
* **`seed`** (`int`, default: `42`):
  RNG seed for deterministic, reproducible traffic generation.
* **`eligible_sf_mode`** (`string`, default: `"all"`):
  Controls which SFs an end-device is eligible to transmit on:
  * `"all"`: Device can use any SF in [7, 12].
  * `"fastest"`: Device is restricted to SF7 only.
  * `"random"`: Device is assigned a random subset of SFs.
* **`deadline_slack_factor`** (`float`, default: `1.5`):
  Multiplier applied to the minimum feasible ToA to define relative packet deadlines:
  `Deadline = r_i + ceil(1.5 × min_j(p_ij))`

#### `lora_phy` (LoRa Physical Layer)
* **`bandwidth_hz`** (`int`, default: `125000`):
  Channel bandwidth BW in Hertz (125 kHz standard uplink).
* **`coding_rate`** (`int`, default: `1`):
  Error correction coding rate indicator:
  * `1`: CR 4/5
  * `2`: CR 4/6
  * `3`: CR 4/7
  * `4`: CR 4/8
* **`preamble_symbols`** (`int`, default: `8`):
  Number of unmodulated preamble symbols N_preamble (standard LoRa preamble is 8 symbols).
* **`crc_enabled`** (`bool`, default: `true`):
  Whether the 16-bit payload CRC is appended.
* **`explicit_header`** (`bool`, default: `true`):
  Whether explicit header mode is enabled (`IH = 0`).
* **`low_data_rate_optimize`** (`string` or `bool`, default: `"auto"`):
  Low Data Rate Optimization (LDRO):
  * `"auto"`: Automatically enabled when symbol duration T_sym > 16 ms (SF11 and SF12 at 125 kHz BW).
  * `true` / `false`: Explicitly force enabled/disabled.

#### `toa_mode` & `time_resolution_ms`
* **`toa_mode`** (`string`, default: `"real"`):
  * `"real"`: Calculates exact airtime using Semtech SX1276 mathematical equations.
  * `"synthetic"`: Assigns pre-configured synthetic processing times for testing.
* **`time_resolution_ms`** (`int`, default: `1`):
  Integer millisecond time discretization quantum.

#### `validation`
* **`run_ilp_comparison`** (`bool`, default: `false`):
  If `true`, executes Branch-and-Bound solver to compute exact optimum makespan.
* **`check_invariants`** (`bool`, default: `true`):
  If `true`, validates non-preemption, deadline compliance, and peak demodulation ≤ 8 after scheduling.

#### `output`
* **`schedule_file`** (`string`, default: `"output/schedule.json"`): Output path for the detailed packet schedule.
* **`stats_file`** (`string`, default: `"output/stats.json"`): Output path for simulation statistics.

---

## 3. Gateway Machine Model

The gateway physical receiver is modeled as an array of m unrelated parallel machines:
```
m = N_ch × N_sf = 8 × 6 = 48 machines
```

### Machine Indexing Scheme
Machines are indexed in **channel-major order**:
```
Machine ID j = channel × N_sf + (SF - 7)
```

| Machine ID | Channel | Spreading Factor | Label |
| :---: | :---: | :---: | :---: |
| `0` | `0` | SF7 | `SF7_CH0` |
| `1` | `0` | SF8 | `SF8_CH0` |
| `2` | `0` | SF9 | `SF9_CH0` |
| `3` | `0` | SF10 | `SF10_CH0` |
| `4` | `0` | SF11 | `SF11_CH0` |
| `5` | `0` | SF12 | `SF12_CH0` |
| `6` | `1` | SF7 | `SF7_CH1` |
| `...` | `...` | `...` | `...` |
| `47` | `7` | SF12 | `SF12_CH7` |

Each machine M_j operates as an independent, non-preemptive communication resource. Transmissions assigned to the same machine M_j cannot overlap in time.

---

## 4. Traffic and Packet Generation Model

### End-Device Profile
For each device d in {0, ..., N_dev - 1}, the generator samples:
1. **Period** T_d: Sampled uniformly from `periods_s` (filtered to divisors of H).
2. **Payload Size** L_d: Sampled uniformly from `payload_sizes_bytes`.
3. **Priority** Π_d: Sampled uniformly from `[priority_range[0], priority_range[1]]`.

### Packet Instance Expansion
Because traffic is periodic, each device d emits packets at regular intervals T_d across [0, H):
```
K_d = H / T_d  (packet instances)
```

For the k-th instance (k = 0, 1, ..., K_d - 1):
* **Release Time (r_i):**
  `r_i = k · T_d × 1000 ms`
* **Relative Deadline (D_i):**
  `D_i = min(r_i + ceil(slack_factor × min_j(p_ij)), H_ms)`
* **Priority (Π_i):** Inherited from parent device.
* **Payload (L_i):** Inherited from parent device.

### Default Traffic Workload Summary
With 50 end-devices, H = 100 s, and periods {10, 20, 50, 100} s:
* 10s period: generates 10 instances per device
* 20s period: generates 5 instances per device
* 50s period: generates 2 instances per device
* 100s period: generates 1 instance per device
* **Total generated packets:** n = 234 packets.

---

## 5. Physical Time-on-Air (ToA) Matrix Calculation

When `toa_mode = "real"`, processing times p_ij are derived from the Semtech SX1276 LoRa physical layer specifications:

### Symbol Duration
```
T_sym = 2^SF / BW  (seconds)
```

### Preamble Duration
```
T_preamble = (N_preamble + 4.25) × T_sym
```

### Payload Symbol Count
```
N_payload = 8 + max(ceil((8 · L_i - 4 · SF + 28 + CRC - 20 · IH) / (4 · (SF - 2 · DE))) · (CR + 4), 0)
```
where:
* `CRC = 16` (if `crc_enabled`), else `0`
* `IH = 0` (explicit header enabled)
* `CR = 1` (coding rate 4/5)
* `DE = 1` if `T_sym > 16 ms` (Low Data Rate Optimization), else `0`

### Total Airtime Matrix Entry (p_ij)
```
p_ij = ceil((T_preamble + N_payload × T_sym) × 1000) ms
```

If packet J_i cannot be scheduled on machine M_j (e.g., SF not eligible or p_ij > D_i - r_i), `p_ij = INF` (represented as `10**18`).

### Representative Time-on-Air Values (125 kHz Bandwidth, CR 4/5)

| SF | Symbol Time (T_sym) | 10 Bytes | 20 Bytes | 30 Bytes | 50 Bytes |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **SF7** | 1.024 ms | 41.2 ms | 61.7 ms | 72.0 ms | 102.7 ms |
| **SF8** | 2.048 ms | 72.2 ms | 102.9 ms | 123.4 ms | 174.6 ms |
| **SF9** | 4.096 ms | 144.4 ms | 185.3 ms | 226.3 ms | 328.7 ms |
| **SF10** | 8.192 ms | 268.3 ms | 350.2 ms | 432.1 ms | 636.9 ms |
| **SF11** | 16.384 ms | 536.6 ms | 700.4 ms | 864.3 ms | 1273.9 ms |
| **SF12** | 32.768 ms | 991.2 ms | 1318.9 ms | 1646.6 ms | 2465.8 ms |

---

## 6. Input Validation and Invariants

Before execution, the configuration and generated data must satisfy:

1. **Harmonicity Invariant:**
   `For all T_k in periods_s:  (H_ms % (T_k × 1000)) == 0`  
   Guarantees all periodic streams repeat cleanly within the hypercycle without boundary wraparound.
2. **Release and Deadline Invariant:**
   `For all i:  0 ≤ r_i < D_i ≤ H_ms`
3. **Hardware Capacity Invariant:**
   `N_ch ≥ 1,  N_demod_max ≥ 1,  N_sf ≥ 1`
4. **Feasible Transmission Invariant:**
   `For all i in J: exists j in M such that p_ij ≤ D_i - r_i`  
   Every packet must possess at least one physical configuration where its transmission duration is less than or equal to its relative deadline.
