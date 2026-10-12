"""
Core data structures for the LoRaWAN Hypercycle Scheduler.

All time values are in milliseconds (integer) internally.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


INF = 10**18  # Sentinel for infeasible ToA entries


@dataclass
class Packet:
    """A real-time packet to be scheduled within the hypercycle."""
    id: int
    release_time: int       # ms – earliest transmission start
    deadline: int            # ms – latest acceptable finish time
    priority: float          # higher = more important
    payload_size: int        # bytes
    device_id: int
    period: int              # ms – repetition period of the parent stream


@dataclass
class Machine:
    """A logical communication resource = (SF, Channel) pair."""
    id: int
    sf: int                  # 7–12
    channel: int             # 0-based channel index

    @property
    def label(self) -> str:
        return f"SF{self.sf}_CH{self.channel}"


@dataclass
class ScheduleEntry:
    """One scheduled transmission in the final output."""
    packet_id: int
    machine_id: int
    start_time: int          # ms
    finish_time: int         # ms
    deadline: int            # ms
    deadline_met: bool
    sf: int
    channel: int


@dataclass
class ScheduleResult:
    """Complete output of the scheduling algorithm."""
    entries: List[ScheduleEntry] = field(default_factory=list)
    dropped_packet_ids: List[int] = field(default_factory=list)
    makespan_ms: int = 0         # Timeline span (latest finish time in ms)
    machine_makespan_ms: int = 0 # Phase 1 machine load makespan (max sum_i p_ij in ms)
    approx_ratio_w: int = 0      # the w* found by binary search
    feasible: bool = False

    def add_entry(self, entry: ScheduleEntry):
        self.entries.append(entry)

    def add_drop(self, packet_id: int):
        self.dropped_packet_ids.append(packet_id)


@dataclass
class AlgorithmState:
    """
    Internal mutable state for the 2-approximation algorithm.
    Kept separate so functions can remain mostly pure.
    """
    n: int                          # number of jobs (packets)
    m: int                          # number of machines
    alpha: List[int]                # alpha[i] = machine index for job i
    pi_job: List[int]               # potential for each job node
    pi_mach: List[int]              # potential for each machine node
    loads: List[int]                # loads[j] = total ToA on machine j
    w: int                          # current candidate makespan parameter

    # Precomputed constants
    b: float = 1.0                  # rounding base  = 1 + 1/m
    log_b_m: float = 0.0           # log_b(m) – potential ceiling

    def compute_loads(self, P: List[List[int]]):
        """Recompute loads from assignment and ToA matrix."""
        self.loads = [0] * self.m
        for i in range(self.n):
            j = self.alpha[i]
            self.loads[j] += P[i][j]

    def get_M_plus(self) -> List[int]:
        """Overloaded machines: load >= 2w + 1."""
        return [j for j in range(self.m) if self.loads[j] >= 2 * self.w + 1]

    def get_M_zero(self) -> List[int]:
        """Medium machines: w + 1 <= load <= 2w."""
        return [j for j in range(self.m)
                if self.w + 1 <= self.loads[j] <= 2 * self.w]

    def get_M_minus(self) -> List[int]:
        """Underloaded machines (sinks): load <= w."""
        return [j for j in range(self.m) if self.loads[j] <= self.w]
