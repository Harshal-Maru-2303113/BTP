"""
Configuration loader with validation.

Reads config.json and converts raw values into typed objects that the rest
of the codebase consumes.
"""

import json
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class NetworkConfig:
    num_channels: int
    spreading_factors: List[int]
    hypercycle_duration_s: float
    hypercycle_duration_ms: int = 0  # derived

    def __post_init__(self):
        self.hypercycle_duration_ms = int(self.hypercycle_duration_s * 1000)


@dataclass
class GatewayConfig:
    max_concurrent_demodulations: int


@dataclass
class TrafficConfig:
    num_end_devices: int
    payload_sizes_bytes: List[int]
    periods_s: List[float]
    priority_range: List[float]
    seed: int
    eligible_sf_mode: str         # "all" | "random"
    deadline_slack_factor: float  # deadline = release + slack * ToA_min


@dataclass
class LoRaPhyConfig:
    bandwidth_hz: int
    coding_rate: int           # 1–4 (maps to 4/5 .. 4/8)
    preamble_symbols: int
    crc_enabled: bool
    explicit_header: bool
    low_data_rate_optimize: str  # "auto" | "on" | "off"


@dataclass
class ValidationConfig:
    run_ilp_comparison: bool
    check_invariants: bool


@dataclass
class OutputConfig:
    schedule_file: str
    stats_file: str


@dataclass
class SimConfig:
    """Top-level configuration container."""
    network: NetworkConfig
    gateway: GatewayConfig
    traffic: TrafficConfig
    lora_phy: LoRaPhyConfig
    toa_mode: str                 # "real" | "synthetic"
    time_resolution_ms: int
    validation: ValidationConfig
    output: OutputConfig

    @property
    def num_machines(self) -> int:
        return self.network.num_channels * len(self.network.spreading_factors)


def load_config(path: str = "config.json") -> SimConfig:
    """Load and validate simulation configuration from a JSON file."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = json.load(f)

    net = raw["network"]
    gw = raw["gateway"]
    traf = raw["traffic"]
    phy = raw["lora_phy"]
    val = raw.get("validation", {})
    out = raw.get("output", {})

    config = SimConfig(
        network=NetworkConfig(
            num_channels=net["num_channels"],
            spreading_factors=net["spreading_factors"],
            hypercycle_duration_s=net["hypercycle_duration_s"],
        ),
        gateway=GatewayConfig(
            max_concurrent_demodulations=gw["max_concurrent_demodulations"],
        ),
        traffic=TrafficConfig(
            num_end_devices=traf["num_end_devices"],
            payload_sizes_bytes=traf["payload_sizes_bytes"],
            periods_s=traf["periods_s"],
            priority_range=traf["priority_range"],
            seed=traf["seed"],
            eligible_sf_mode=traf.get("eligible_sf_mode", "all"),
            deadline_slack_factor=traf.get("deadline_slack_factor", 1.5),
        ),
        lora_phy=LoRaPhyConfig(
            bandwidth_hz=phy["bandwidth_hz"],
            coding_rate=phy["coding_rate"],
            preamble_symbols=phy["preamble_symbols"],
            crc_enabled=phy["crc_enabled"],
            explicit_header=phy["explicit_header"],
            low_data_rate_optimize=phy.get("low_data_rate_optimize", "auto"),
        ),
        toa_mode=raw.get("toa_mode", "real"),
        time_resolution_ms=raw.get("time_resolution_ms", 1),
        validation=ValidationConfig(
            run_ilp_comparison=val.get("run_ilp_comparison", False),
            check_invariants=val.get("check_invariants", True),
        ),
        output=OutputConfig(
            schedule_file=out.get("schedule_file", "output/schedule.json"),
            stats_file=out.get("stats_file", "output/stats.json"),
        ),
    )

    # ---- basic sanity checks ---- #
    assert config.network.num_channels > 0, "num_channels must be > 0"
    assert all(7 <= sf <= 12 for sf in config.network.spreading_factors), \
        "Spreading factors must be in [7, 12]"
    assert config.network.hypercycle_duration_s > 0, "H must be > 0"
    assert config.gateway.max_concurrent_demodulations > 0
    assert config.traffic.num_end_devices > 0
    assert len(config.traffic.periods_s) > 0
    assert config.traffic.deadline_slack_factor >= 1.0, \
        "deadline_slack_factor must be >= 1.0"

    return config
