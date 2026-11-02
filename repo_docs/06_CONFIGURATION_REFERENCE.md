# Configuration Reference

## config.json — Complete Schema

```json
{
    "network": {
        "num_channels": 8,              // N_ch: orthogonal LoRa channels
        "spreading_factors": [7,8,9,10,11,12], // N_sf: available SFs
        "hypercycle_duration_s": 100     // H: scheduling horizon in seconds
    },
    "gateway": {
        "max_concurrent_demodulations": 8  // SX1301/SX1302 hardware limit
    },
    "traffic": {
        "num_end_devices": 50,           // Number of end devices
        "payload_sizes_bytes": [10,20,30,50], // Payload options (bytes)
        "periods_s": [10,20,50,100],     // Transmission periods (MUST divide H)
        "priority_range": [1, 10],       // [Π_min, Π_max], higher = more important
        "seed": 42,                      // RNG seed for reproducibility
        "eligible_sf_mode": "all",       // "all" | "fastest" | "random"
        "deadline_slack_factor": 1.5     // D = r + slack × min_ToA
    },
    "lora_phy": {
        "bandwidth_hz": 125000,          // 125 kHz standard uplink
        "coding_rate": 1,                // 1→4/5, 2→4/6, 3→4/7, 4→4/8
        "preamble_symbols": 8,           // Standard LoRa preamble
        "crc_enabled": true,             // 16-bit CRC appended
        "explicit_header": true,         // Explicit header mode
        "low_data_rate_optimize": "auto" // "auto" | "on" | "off"
    },
    "toa_mode": "real",                  // "real" (Semtech formula) | "synthetic"
    "time_resolution_ms": 1,             // Discretization quantum
    "validation": {
        "run_ilp_comparison": false,     // Run exact solver for comparison
        "check_invariants": true         // Post-schedule validity checks
    },
    "output": {
        "schedule_file": "output/schedule.json",
        "stats_file": "output/stats.json"
    },
    "energy": {
        "enable_energy_optimization": true, // Enable Phase 1.5 downshifting
        "supply_voltage_v": 3.3,           // Transceiver voltage (V)
        "i_tx_a": 0.044,                   // Transmit current (44 mA)
        "i_rx_a": 0.0115,                  // Receive window current (11.5 mA)
        "i_stby_a": 0.0016,                // Standby current (1.6 mA)
        "i_sleep_a": 0.000002,             // Deep sleep current (2 uA)
        "i_mcu_a": 0.005,                  // MCU active current (5 mA)
        "t_mcu_s": 0.05,                   // MCU processing time (50 ms)
        "i_sens_a": 0.003,                 // Sensor acquisition current (3 mA)
        "t_sens_s": 0.1,                   // Sensor acquisition time (100 ms)
        "t_rx_s": 0.03,                    // RX preamble detection window (30 ms)
        "mac_header_bytes": 13             // LoRaWAN PHY payload header overhead
    },
    "cyclic_executive": {
        "enable_cyclic_mode": false,       // Master switch for cyclic executive wrapper
        "minor_cycle_duration_s": 10,      // Uniform minor cycle duration tau (if durations_s is null)
        "minor_cycle_durations_s": null,   // null (uniform) or list of variable durations [tau_0, tau_1, ...] summing to H
        "enable_packet_carryover": true,   // Carry dropped packets over to next cycle
        "max_carryover_cycles": 3,         // Max hops a packet can carry over
        "carryover_priority_boost": 1.5,   // Priority increment per hop to prevent starvation
        "deadline_mode": "period"          // "period" (D = r + T) or "slack"
    }
}
```

## Derived Values

| Derived | Formula | Default |
|---|---|---|
| `num_machines` (m) | num_channels × len(spreading_factors) | 48 |
| `hypercycle_duration_ms` | hypercycle_duration_s × 1000 | 100,000 |
| Total packets (n) | Σ_{dev} (H / T_dev) | ~234 |

## Harmonic Period Constraint

All periods in `periods_s` must divide `hypercycle_duration_s` (in ms):
```
H_ms % (period × 1000) == 0
```
With H = 100s: valid periods are 10s, 20s, 50s, 100s.

## Low Data Rate Optimization

Automatically enabled when symbol duration T_sym > 16 ms:
- SF11 at 125 kHz: T_sym = 16.384 ms → **enabled**
- SF12 at 125 kHz: T_sym = 32.768 ms → **enabled**
- SF7–10: disabled

## CLI Arguments

```bash
python main.py [--config path] [--cyclic] [--ilp] [--verbose]
```

- `--config`, `-c`: Path to JSON configuration file
- `--cyclic`, `-y`: Enable Cyclic Executive Mode (minor cycles under hypercycle with packet carryover)
- `--ilp`: Run exact ILP solver for comparison
- `--verbose`, `-v`: Print detailed scheduling logs

| Flag | Effect |
|---|---|
| `--config` / `-c` | Path to config JSON (default: config.json) |
| `--ilp` | Run exact ILP solver for comparison |
| `--verbose` / `-v` | Print per-SF ToA diagnostics |

