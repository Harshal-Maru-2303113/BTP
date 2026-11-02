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
class EnergyConfig:
    """LoRaWAN Class A energy consumption parameters (Casals et al. 2017)."""
    enable_energy_optimization: bool = True
    supply_voltage_v: float = 3.3
    i_tx_a: float = 0.044       # 44 mA
    i_rx_a: float = 0.0115      # 11.5 mA
    i_stby_a: float = 0.0016    # 1.6 mA
    i_sleep_a: float = 2.0e-6   # 2 uA
    i_mcu_a: float = 0.005      # 5 mA
    t_mcu_s: float = 0.05       # 50 ms
    i_sens_a: float = 0.003     # 3 mA
    t_sens_s: float = 0.1       # 100 ms
    t_rx_s: float = 0.03        # 30 ms
    mac_header_bytes: int = 13  # LoRaWAN PHY overhead


@dataclass
class OutputConfig:
    schedule_file: str
    stats_file: str


@dataclass
class CyclicExecutiveConfig:
    """Multi-cycle executive configuration nested under the major hypercycle."""
    enable_cyclic_mode: bool = False
    minor_cycle_duration_s: float = 10.0
    minor_cycle_durations_s: Optional[List[float]] = None  # None for uniform cycles, or list of durations for variable-length cycles
    enable_packet_carryover: bool = True
    max_carryover_cycles: int = 3
    carryover_priority_boost: float = 1.5
    deadline_mode: str = "period"  # "period" (D = r + T) | "slack" (D = r + slack * min_ToA)
    minor_cycle_duration_ms: int = 0  # derived (default / uniform duration)
    minor_cycle_durations_ms: List[int] = field(default_factory=list)  # derived (heterogeneous durations if specified)

    def __post_init__(self):
        self.minor_cycle_duration_ms = int(round(self.minor_cycle_duration_s * 1000))
        if self.minor_cycle_durations_s:
            self.minor_cycle_durations_ms = [
                int(round(d * 1000)) for d in self.minor_cycle_durations_s
            ]
        else:
            self.minor_cycle_durations_ms = []


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
    energy: EnergyConfig = field(default_factory=EnergyConfig)
    cyclic_executive: CyclicExecutiveConfig = field(default_factory=CyclicExecutiveConfig)

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
    nrg = raw.get("energy", {})
    cyc = raw.get("cyclic_executive", {})

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
        energy=EnergyConfig(
            enable_energy_optimization=nrg.get("enable_energy_optimization", True),
            supply_voltage_v=nrg.get("supply_voltage_v", 3.3),
            i_tx_a=nrg.get("i_tx_a", 0.044),
            i_rx_a=nrg.get("i_rx_a", 0.0115),
            i_stby_a=nrg.get("i_stby_a", 0.0016),
            i_sleep_a=nrg.get("i_sleep_a", 2.0e-6),
            i_mcu_a=nrg.get("i_mcu_a", 0.005),
            t_mcu_s=nrg.get("t_mcu_s", 0.05),
            i_sens_a=nrg.get("i_sens_a", 0.003),
            t_sens_s=nrg.get("t_sens_s", 0.1),
            t_rx_s=nrg.get("t_rx_s", 0.03),
            mac_header_bytes=nrg.get("mac_header_bytes", 13),
        ),
        cyclic_executive=CyclicExecutiveConfig(
            enable_cyclic_mode=cyc.get("enable_cyclic_mode", False),
            minor_cycle_duration_s=cyc.get("minor_cycle_duration_s", 10.0),
            minor_cycle_durations_s=cyc.get("minor_cycle_durations_s", None),
            enable_packet_carryover=cyc.get("enable_packet_carryover", True),
            max_carryover_cycles=cyc.get("max_carryover_cycles", 3),
            carryover_priority_boost=cyc.get("carryover_priority_boost", 1.5),
            deadline_mode=cyc.get("deadline_mode", "period"),
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

    if config.cyclic_executive.enable_cyclic_mode:
        if config.cyclic_executive.minor_cycle_durations_ms:
            assert all(d > 0 for d in config.cyclic_executive.minor_cycle_durations_ms), \
                "All minor cycle durations must be > 0"
            total_dur_ms = sum(config.cyclic_executive.minor_cycle_durations_ms)
            assert total_dur_ms == config.network.hypercycle_duration_ms, \
                f"Sum of heterogeneous minor cycle durations ({total_dur_ms} ms) must equal hypercycle duration ({config.network.hypercycle_duration_ms} ms)"
        else:
            assert config.cyclic_executive.minor_cycle_duration_s > 0, "minor_cycle_duration_s must be > 0"
            assert config.network.hypercycle_duration_ms % config.cyclic_executive.minor_cycle_duration_ms == 0, \
                f"Hypercycle duration ({config.network.hypercycle_duration_ms} ms) must be evenly divisible by minor cycle ({config.cyclic_executive.minor_cycle_duration_ms} ms)"

    return config
