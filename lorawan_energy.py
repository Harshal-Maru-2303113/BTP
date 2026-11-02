"""
LoRaWAN Energy Consumption Model and Exact Time-on-Air (ToA) Calculations.

References:
  1. Semtech SX1276/77/78/79 Datasheet §4.1.1.7 (Time-on-Air).
  2. LoRaWAN 1.0.3 Specification (PHY payload structure, Class A RX timing).
  3. Casals et al., "Modeling the Energy Performance of LoRaWAN," Sensors 17(10):2364, 2017.
  4. Bouguera et al., "Energy Consumption Model for Sensor Nodes Based on LoRa and LoRaWAN," Sensors 18(7):2104, 2018.

Key Models:
  - Exact Time-on-Air: incorporates 13-byte LoRaWAN MAC layer overhead (PL = 13 + N_FOpts + N_app).
  - Multi-state Class A cycle energy:
      E_cycle = V * sum(I_state * t_state)
      States: MCU active, Sensor read, Transmit (TX), Wait for RX1, RX1 window,
              Wait for RX2, RX2 window, and Deep Sleep.
"""

import math
from typing import List, Tuple, Dict, Optional
from data_structures import Packet, Machine, INF


def compute_phy_payload_len(app_payload_bytes: int, fopts_bytes: int = 0) -> int:
    """
    Calculate LoRaWAN PHY payload length (PL) in bytes:
      PL = 13 + N_FOpts + N_app (for N_app > 0)
         = 12 + N_FOpts         (for N_app == 0, FPort omitted)

    13 bytes overhead:
      - MHDR: 1 byte
      - DevAddr: 4 bytes
      - FCtrl: 1 byte
      - FCnt: 2 bytes
      - FPort: 1 byte
      - MIC: 4 bytes
    """
    if app_payload_bytes > 0:
        return 12 + fopts_bytes + 1 + app_payload_bytes  # 13 + fopts + app
    return 12 + fopts_bytes


def compute_semtech_toa_s(
    phy_payload_bytes: int,
    sf: int,
    bw_hz: float = 125000.0,
    coding_rate: int = 1,
    preamble_symbols: int = 8,
    crc_enabled: bool = True,
    explicit_header: bool = True,
) -> float:
    """
    Compute exact LoRaWAN Time-on-Air (seconds) according to Semtech SX1276 §4.1.1.7.

    Validation Cases (BW=125kHz, CR=1, n_pre=8, crc=1, ih=0, PL=23 bytes):
      SF7  -> 61.696 ms (0.061696 s)
      SF12 -> 1482.752 ms (1.482752 s)
    """
    t_sym = (2.0 ** sf) / bw_hz

    # Low data rate optimization is mandatory when symbol duration exceeds 16 ms
    de = 1 if t_sym > 0.016 else 0
    ih = 0 if explicit_header else 1
    crc = 1 if crc_enabled else 0

    numerator = 8 * phy_payload_bytes - 4 * sf + 28 + 16 * crc - 20 * ih
    denominator = 4 * (sf - 2 * de)

    if denominator <= 0:
        n_payload = 8
    else:
        n_payload = 8 + max(
            math.ceil(numerator / denominator) * (coding_rate + 4),
            0
        )

    t_preamble = (preamble_symbols + 4.25) * t_sym
    t_payload = n_payload * t_sym
    return t_preamble + t_payload


def compute_semtech_toa_ms(
    phy_payload_bytes: int,
    sf: int,
    bw_hz: float = 125000.0,
    coding_rate: int = 1,
    preamble_symbols: int = 8,
    crc_enabled: bool = True,
    explicit_header: bool = True,
) -> float:
    """Compute exact Time-on-Air in milliseconds."""
    return compute_semtech_toa_s(
        phy_payload_bytes, sf, bw_hz, coding_rate, preamble_symbols, crc_enabled, explicit_header
    ) * 1000.0


def compute_class_a_cycle_energy(
    app_payload_bytes: int,
    sf: int,
    t_cycle_s: float,
    v_supply: float = 3.3,
    i_tx: float = 0.044,      # 44 mA transmit current
    i_rx: float = 0.0115,     # 11.5 mA receive current
    i_stby: float = 0.0016,   # 1.6 mA standby current
    i_sleep: float = 2.0e-6,  # 2 uA deep sleep current
    i_mcu: float = 0.005,     # 5 mA MCU active current
    t_mcu_s: float = 0.05,    # 50 ms MCU processing time
    i_sens: float = 0.003,    # 3 mA sensor active current
    t_sens_s: float = 0.1,    # 100 ms sensor acquisition time
    t_rx_s: float = 0.03,     # 30 ms RX window (preamble detection)
    fopts_bytes: int = 0,
    bw_hz: float = 125000.0,
    coding_rate: int = 1,
    preamble_symbols: int = 8,
) -> Tuple[float, float, float, float]:
    """
    Compute Class A operational cycle energy, transmit energy, average current, and battery life.

    Parameters
    ----------
    app_payload_bytes : int
        Sensor data payload size in bytes.
    sf : int
        Spreading factor (7..12).
    t_cycle_s : float
        End-device transmission period / cycle time in seconds.
    v_supply : float
        Supply voltage (typically 3.3 V).

    Returns
    -------
    (t_tx_s, e_tx_j, e_cycle_j, i_avg_a)
        t_tx_s: Time-on-Air in seconds
        e_tx_j: Transmit energy in Joules
        e_cycle_j: Total cycle energy in Joules
        i_avg_a: Average current draw in Amperes
    """
    pl_phy = compute_phy_payload_len(app_payload_bytes, fopts_bytes)
    t_tx = compute_semtech_toa_s(
        pl_phy, sf, bw_hz, coding_rate, preamble_symbols
    )

    # Class A timeline states:
    # 1. MCU wake & processing
    # 2. Sensor measurement
    # 3. Packet Transmission (TX)
    # 4. Wait for RX1 (default delay: 1.0 s)
    # 5. RX1 window (t_rx)
    # 6. Wait for RX2 (default delay: 1.0 s - t_rx)
    # 7. RX2 window (t_rx)
    # 8. Sleep remainder of the cycle
    states = [
        (i_mcu, t_mcu_s),
        (i_sens, t_sens_s),
        (i_tx, t_tx),
        (i_stby, 1.0),
        (i_rx, t_rx_s),
        (i_stby, max(0.0, 1.0 - t_rx_s)),
        (i_rx, t_rx_s),
    ]

    t_active = sum(t for _, t in states)
    t_sleep = max(0.0, t_cycle_s - t_active)
    states.append((i_sleep, t_sleep))

    # Electric charge Q in Ampere-seconds (Coulombs)
    q_coulombs = sum(i * t for i, t in states)

    # Total cycle energy: E = V * Q (Joules)
    e_cycle_j = v_supply * q_coulombs

    # TX-only energy: E_tx = V * I_tx * ToA
    e_tx_j = v_supply * i_tx * t_tx

    # Average current
    total_time = max(t_cycle_s, t_active)
    i_avg_a = q_coulombs / total_time

    return t_tx, e_tx_j, e_cycle_j, i_avg_a


def estimate_battery_life_years(
    i_avg_a: float,
    battery_capacity_mah: float = 2400.0,
    derating_factor: float = 0.85,
) -> float:
    """
    Estimate device battery lifetime in years.
      Life (hours) = (C_nominal * k_derate) / I_avg
    """
    if i_avg_a <= 0:
        return float("inf")
    usable_capacity_ah = (battery_capacity_mah / 1000.0) * derating_factor
    hours = usable_capacity_ah / i_avg_a
    return hours / (24.0 * 365.25)


def compute_energy_matrix(
    packets: List[Packet],
    machines: List[Machine],
    config,
    P: List[List[int]],
) -> List[List[float]]:
    """
    Build the n × m energy matrix E, where E[i][j] is the transmission
    cycle energy in millijoules (mJ) consumed by packet i if transmitted on machine j.

    If packet i cannot be transmitted on machine j (P[i][j] == INF), E[i][j] = INF.
    """
    n = len(packets)
    m = len(machines)
    E = [[float(INF)] * m for _ in range(n)]

    # Fetch configuration parameters or fall back to standard defaults
    energy_cfg = getattr(config, "energy", None)
    v_supply = getattr(energy_cfg, "supply_voltage_v", 3.3) if energy_cfg else 3.3
    i_tx = getattr(energy_cfg, "i_tx_a", 0.044) if energy_cfg else 0.044
    i_rx = getattr(energy_cfg, "i_rx_a", 0.0115) if energy_cfg else 0.0115
    i_stby = getattr(energy_cfg, "i_stby_a", 0.0016) if energy_cfg else 0.0016
    i_sleep = getattr(energy_cfg, "i_sleep_a", 2.0e-6) if energy_cfg else 2.0e-6
    i_mcu = getattr(energy_cfg, "i_mcu_a", 0.005) if energy_cfg else 0.005
    t_mcu = getattr(energy_cfg, "t_mcu_s", 0.05) if energy_cfg else 0.05
    i_sens = getattr(energy_cfg, "i_sens_a", 0.003) if energy_cfg else 0.003
    t_sens = getattr(energy_cfg, "t_sens_s", 0.1) if energy_cfg else 0.1
    t_rx = getattr(energy_cfg, "t_rx_s", 0.03) if energy_cfg else 0.03

    phy = config.lora_phy
    bw_hz = float(phy.bandwidth_hz)
    coding_rate = phy.coding_rate
    preamble_symbols = phy.preamble_symbols

    # Cache energy per (payload_size, sf, period_s)
    cache: Dict[Tuple[int, int, float], float] = {}

    for i, pkt in enumerate(packets):
        period_s = max(1.0, pkt.period / 1000.0)
        for j, mach in enumerate(machines):
            if P[i][j] >= INF:
                continue

            key = (pkt.payload_size, mach.sf, period_s)
            if key not in cache:
                _, _, e_cycle_j, _ = compute_class_a_cycle_energy(
                    app_payload_bytes=pkt.payload_size,
                    sf=mach.sf,
                    t_cycle_s=period_s,
                    v_supply=v_supply,
                    i_tx=i_tx,
                    i_rx=i_rx,
                    i_stby=i_stby,
                    i_sleep=i_sleep,
                    i_mcu=i_mcu,
                    t_mcu_s=t_mcu,
                    i_sens=i_sens,
                    t_sens_s=t_sens,
                    t_rx_s=t_rx,
                    fopts_bytes=0,
                    bw_hz=bw_hz,
                    coding_rate=coding_rate,
                    preamble_symbols=preamble_symbols,
                )
                cache[key] = e_cycle_j * 1000.0  # Convert to millijoules (mJ)

            E[i][j] = cache[key]

    return E

