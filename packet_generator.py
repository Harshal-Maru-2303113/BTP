"""
Packet and input generator.

Generates harmonic periodic traffic for the LoRaWAN hypercycle scheduler.
Each end-device is assigned a random (period, payload_size, priority) tuple,
and all instances within the hypercycle [0, H) are expanded.
"""

import random
import math
from typing import List, Tuple

from data_structures import Packet, Machine
from config_loader import SimConfig


def create_machines(config: SimConfig) -> List[Machine]:
    """
    Create m = N_ch × N_sf machines, one per (SF, channel) pair.

    Machine ordering: channel-major (all SFs for CH0, then CH1, …).
    """
    machines: List[Machine] = []
    mid = 0
    for ch in range(config.network.num_channels):
        for sf in config.network.spreading_factors:
            machines.append(Machine(id=mid, sf=sf, channel=ch))
            mid += 1
    return machines


def generate_packets(config: SimConfig,
                     machines: List[Machine]) -> List[Packet]:
    """
    Generate all packet instances for one hypercycle [0, H).

    Workflow
    --------
    1. For each end-device, randomly pick (period, payload_size, priority).
    2. Verify the period divides H (harmonic constraint).
    3. Expand instances:  release = k * period, k = 0, 1, …, H/period − 1.
    4. Compute deadline = release + slack_factor × min feasible ToA.
       Clamp deadline to H.
    """
    rng = random.Random(config.traffic.seed)
    H_ms = config.network.hypercycle_duration_ms

    periods_ms = [int(p * 1000) for p in config.traffic.periods_s]
    # Filter to harmonic periods (must divide H)
    harmonic_periods = [p for p in periods_ms if H_ms % p == 0]
    if not harmonic_periods:
        raise ValueError(
            f"No period in {periods_ms} divides H = {H_ms} ms. "
            "Adjust periods_s or hypercycle_duration_s in config."
        )

    packets: List[Packet] = []
    pid = 0

    for dev in range(config.traffic.num_end_devices):
        period = rng.choice(harmonic_periods)
        payload = rng.choice(config.traffic.payload_sizes_bytes)
        lo, hi = config.traffic.priority_range
        priority = round(rng.uniform(lo, hi), 2)

        num_instances = H_ms // period

        # Compute minimum feasible ToA across all machines for this payload
        # (used for deadline calculation)
        from lorawan_toa import compute_toa_ms
        phy = config.lora_phy
        min_toa_ms = min(
            compute_toa_ms(
                payload_bytes=payload, sf=mach.sf,
                bw_hz=phy.bandwidth_hz,
                coding_rate=phy.coding_rate,
                preamble_symbols=phy.preamble_symbols,
                crc_enabled=phy.crc_enabled,
                explicit_header=phy.explicit_header,
                ldr_mode=phy.low_data_rate_optimize,
            )
            for mach in machines
        )
        min_toa_int = max(1, int(math.ceil(min_toa_ms)))

        for k in range(num_instances):
            release = k * period
            raw_deadline = release + int(
                config.traffic.deadline_slack_factor * min_toa_int
            )
            # Clamp to hypercycle boundary AND ensure at least within period
            deadline = min(raw_deadline, release + period, H_ms)
            # Deadline must be > release
            if deadline <= release:
                deadline = min(release + min_toa_int, H_ms)

            packets.append(Packet(
                id=pid,
                release_time=release,
                deadline=deadline,
                priority=priority,
                payload_size=payload,
                device_id=dev,
                period=period,
            ))
            pid += 1

    return packets
