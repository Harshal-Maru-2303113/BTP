"""
LoRaWAN Time-on-Air (ToA) computation.

Implements the Semtech SX1276 ToA formula exactly as described in the
datasheet (AN1200.13) and adds a synthetic mode for algorithmic testing.

Reference
---------
Semtech, "LoRa Modem Designer's Guide", AN1200.13, §4.1.
"""

import math
from typing import List

from data_structures import Machine, INF
from config_loader import SimConfig


def _should_enable_low_data_rate(sf: int, bw_hz: int, mode: str) -> bool:
    """Low data rate optimisation is mandatory when symbol duration > 16 ms."""
    if mode == "on":
        return True
    if mode == "off":
        return False
    # "auto": enable when T_sym > 16 ms
    t_sym_ms = (2 ** sf / bw_hz) * 1000
    return t_sym_ms > 16.0


def compute_toa_ms(payload_bytes: int, sf: int, bw_hz: int,
                   coding_rate: int = 1, preamble_symbols: int = 8,
                   crc_enabled: bool = True, explicit_header: bool = True,
                   ldr_mode: str = "auto") -> float:
    """
    Compute the Time-on-Air in **milliseconds** for a single LoRa packet.

    Parameters
    ----------
    payload_bytes : int
        Application-layer payload size in bytes.
    sf : int
        Spreading factor (7–12).
    bw_hz : int
        Bandwidth in Hz (typically 125000).
    coding_rate : int
        Coding rate denominator offset: CR = 4/(4+coding_rate).
        1 → 4/5,  2 → 4/6,  3 → 4/7,  4 → 4/8.
    preamble_symbols : int
        Number of programmed preamble symbols.
    crc_enabled : bool
        Whether the CRC field is appended.
    explicit_header : bool
        Explicit header mode (True) vs implicit (False).
    ldr_mode : str
        Low data rate optimise: "auto" | "on" | "off".

    Returns
    -------
    float
        Transmission duration in milliseconds.
    """
    # Symbol duration
    t_sym = (2 ** sf) / bw_hz  # seconds

    # Preamble duration (datasheet: n_preamble + 4.25 symbols)
    t_preamble = (preamble_symbols + 4.25) * t_sym

    # Payload symbol count
    de = 1 if _should_enable_low_data_rate(sf, bw_hz, ldr_mode) else 0
    ih = 0 if explicit_header else 1
    crc_bits = 16 if crc_enabled else 0

    numerator = 8 * payload_bytes - 4 * sf + 28 + crc_bits - 20 * ih
    denominator = 4 * (sf - 2 * de)

    if denominator <= 0:
        # Degenerate case – shouldn't happen for SF >= 7
        n_payload = 8
    else:
        n_payload = 8 + max(math.ceil(numerator / denominator) * (coding_rate + 4), 0)

    t_payload = n_payload * t_sym
    toa_s = t_preamble + t_payload
    return toa_s * 1000.0  # → milliseconds


def compute_toa_matrix(packets, machines: List[Machine],
                       config: SimConfig) -> List[List[int]]:
    """
    Build the n × m Time-on-Air matrix P.

    P[i][j] = integer ToA in ms for packet i on machine j,
              or INF if packet i cannot use machine j's SF.
    """
    n = len(packets)
    m = len(machines)
    phy = config.lora_phy

    # Pre-compute ToA per (payload_size, sf) to avoid redundant work
    toa_cache: dict = {}

    P = [[INF] * m for _ in range(n)]

    for i, pkt in enumerate(packets):
        for j, mach in enumerate(machines):
            key = (pkt.payload_size, mach.sf)
            if key not in toa_cache:
                if config.toa_mode == "real":
                    raw = compute_toa_ms(
                        payload_bytes=pkt.payload_size,
                        sf=mach.sf,
                        bw_hz=phy.bandwidth_hz,
                        coding_rate=phy.coding_rate,
                        preamble_symbols=phy.preamble_symbols,
                        crc_enabled=phy.crc_enabled,
                        explicit_header=phy.explicit_header,
                        ldr_mode=phy.low_data_rate_optimize,
                    )
                else:
                    # Synthetic mode: ToA proportional to 2^SF
                    raw = (2 ** mach.sf) / (2 ** 7) * 50.0  # SF7 → 50 ms baseline

                toa_cache[key] = max(1, int(math.ceil(raw)))  # at least 1 ms

            P[i][j] = toa_cache[key]

    return P


def compute_cost_matrix(P: List[List[int]], m: int) -> List[List[int]]:
    """
    Build the cost matrix C using Truemper's logarithmic transformation.

    C[i][j] = floor(log_b(P[i][j]))  where  b = 1 + 1/m.

    For infeasible entries (P[i][j] == INF), C[i][j] = INF.
    """
    n = len(P)
    b = 1.0 + 1.0 / m
    ln_b = math.log(b)

    C = [[INF] * m for _ in range(n)]

    for i in range(n):
        for j in range(m):
            p = P[i][j]
            if p >= INF:
                continue
            if p <= 0:
                C[i][j] = 0
                continue

            c = int(math.floor(math.log(p) / ln_b))
            # Guard against floating-point drift: ensure b^c <= p
            while b ** (c + 1) <= p + 1e-9:
                c += 1
            while c > 0 and b ** c > p + 1e-9:
                c -= 1
            C[i][j] = max(c, 0)

    return C
