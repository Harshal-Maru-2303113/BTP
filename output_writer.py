"""
Structured JSON output writer.

Writes the full schedule and statistics to separate JSON files.
"""

import json
import os
from typing import Dict, Any

from data_structures import ScheduleResult


def write_schedule(result: ScheduleResult, path: str):
    """Write the complete schedule to a JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    data = {
        "feasible": result.feasible,
        "makespan_ms": result.makespan_ms,
        "machine_makespan_ms": result.machine_makespan_ms,
        "approx_w_star": result.approx_ratio_w,
        "num_scheduled": len(result.entries),
        "num_dropped": len(result.dropped_packet_ids),
        "schedule": [
            {
                "packet_id": e.packet_id,
                "machine_id": e.machine_id,
                "sf": e.sf,
                "channel": e.channel,
                "start_time_ms": e.start_time,
                "finish_time_ms": e.finish_time,
                "deadline_ms": e.deadline,
                "deadline_met": e.deadline_met,
            }
            for e in sorted(result.entries, key=lambda e: (e.machine_id, e.start_time))
        ],
        "dropped_packet_ids": result.dropped_packet_ids,
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Schedule written to {path}")


def write_stats(stats: Dict[str, Any], path: str):
    """Write simulation statistics to a JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    with open(path, "w") as f:
        json.dump(stats, f, indent=2, default=str)

    print(f"  Stats written to {path}")
