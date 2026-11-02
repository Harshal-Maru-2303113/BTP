"""
LoRaWAN Hypercycle Scheduler package.

Integrates the 2-approximation makespan minimisation with:
  - Phase 1.5: Energy-optimal downshifting (Algorithm 4)
  - Phase 2: Per-channel EDF timeline construction
  - Demod-aware packet placement (sweep-line segment tree)
  - Phase 3: Priority-based packet dropping
  - Cyclic Executive Wrapper with Carryover Buffer
"""

from scheduler.lorawan_scheduler import lorawan_hypercycle_scheduler
from scheduler.energy_optimizer import energy_optimal_downshift
from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler

__all__ = [
    "lorawan_hypercycle_scheduler",
    "energy_optimal_downshift",
    "run_cyclic_hypercycle_scheduler",
]

