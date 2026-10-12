import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from segment_tree import SegmentTree
from config_loader import load_config
from packet_generator import create_machines, generate_packets
from lorawan_toa import compute_toa_matrix, compute_cost_matrix, compute_toa_ms
from approximation.binary_search import find_2approx_assignment
from approximation.graph_utils import compute_loads
from scheduler.lorawan_scheduler import lorawan_hypercycle_scheduler
from validator.invariant_checker import check_schedule_validity, InvariantError


def test_segment_tree():
    st = SegmentTree(100)
    assert st.range_max(0, 99) == 0

    st.range_add(10, 20, 3)
    assert st.range_max(10, 20) == 3
    assert st.range_max(0, 9) == 0
    assert st.range_max(21, 99) == 0

    st.range_add(15, 25, 2)
    assert st.range_max(10, 14) == 3
    assert st.range_max(15, 20) == 5
    assert st.range_max(21, 25) == 2


def test_lorawan_toa_formula():
    # SF7, BW 125kHz, CR 4/5 (1), payload 10 bytes
    toa_ms = compute_toa_ms(
        payload_bytes=10,
        sf=7,
        bw_hz=125000,
        coding_rate=1,
        preamble_symbols=8,
        crc_enabled=True,
        explicit_header=True,
    )
    # Typical LoRaWAN SF7 10-byte ToA is ~41-42 ms
    assert 40 <= toa_ms <= 45


def test_2approximation_makespan_guarantee():
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)[:20]  # small subset
    n, m = len(packets), len(machines)
    P = compute_toa_matrix(packets, machines, config)
    C = compute_cost_matrix(P, m)
    b = 1.0 + 1.0 / m

    alpha, w_star = find_2approx_assignment(n, m, P, C, b, H_ms=config.network.hypercycle_duration_ms)
    assert alpha is not None
    assert len(alpha) == n

    loads = compute_loads(n, m, P, alpha)
    max_load = max(loads)
    # The 2-approximation guarantee: max_load <= 2 * w_star
    assert max_load <= 2 * w_star


def test_empty_packets():
    config = load_config("config.json")
    machines = create_machines(config)
    P = []
    result = lorawan_hypercycle_scheduler(
        packets=[],
        machines=machines,
        P_full=P,
        H_ms=config.network.hypercycle_duration_ms,
        max_demod=config.gateway.max_concurrent_demodulations,
    )
    assert result.feasible is False
    assert len(result.entries) == 0


def test_small_instance():
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)[:5]
    n = len(packets)
    P = compute_toa_matrix(packets, machines, config)

    result = lorawan_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        H_ms=config.network.hypercycle_duration_ms,
        max_demod=config.gateway.max_concurrent_demodulations,
    )
    assert result.feasible is True
    assert len(result.entries) == n
    assert len(result.dropped_packet_ids) == 0


def test_end_to_end_scheduler():
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    n, m = len(packets), len(machines)
    P = compute_toa_matrix(packets, machines, config)

    result = lorawan_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        H_ms=config.network.hypercycle_duration_ms,
        max_demod=config.gateway.max_concurrent_demodulations,
        check_invariants=True,
    )

    assert result.feasible is True
    assert len(result.entries) > 0
    assert len(result.entries) + len(result.dropped_packet_ids) == n

    val = check_schedule_validity(
        result.entries,
        machines,
        config.network.hypercycle_duration_ms,
        config.gateway.max_concurrent_demodulations,
    )
    assert val["per_channel_ok"] is True
    assert val["deadlines_ok"] is True
    assert val["demod_limit_ok"] is True
    assert val["max_concurrent_demod"] <= config.gateway.max_concurrent_demodulations
    assert result.machine_makespan_ms > 0


def test_exact_bruteforce_soundness():
    """Verify that exact_optimal_makespan matches naive_bruteforce_makespan 100% identically."""
    from validator.bruteforce_comparator import naive_bruteforce_makespan, exact_optimal_makespan
    import random
    rng = random.Random(12345)

    for _ in range(15):
        n = rng.randint(3, 6)
        m = rng.randint(2, 4)
        P = [[rng.choice([15, 30, 45, 60, 10**18]) for _ in range(m)] for _ in range(n)]
        # Ensure feasibility
        for i in range(n):
            if all(P[i][j] >= 10**18 for j in range(m)):
                P[i][rng.randint(0, m - 1)] = rng.randint(15, 45)

        naive_opt, _, _ = naive_bruteforce_makespan(n, m, P)
        exact_opt, _, _ = exact_optimal_makespan(n, m, P)
        assert naive_opt == exact_opt, f"Mismatch: naive={naive_opt}, exact={exact_opt}"


def test_exact_bruteforce_makespan_guarantee():
    """Verify that 2-approximation makespan is <= 2 * OPT across multiple test subsets."""
    from validator.bruteforce_comparator import exact_optimal_makespan
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)[:12]
    n, m = len(packets), len(machines)
    P = compute_toa_matrix(packets, machines, config)
    C = compute_cost_matrix(P, m)
    b = 1.0 + 1.0 / m

    alpha, w_star = find_2approx_assignment(n, m, P, C, b, H_ms=config.network.hypercycle_duration_ms)
    assert alpha is not None
    approx_cmax = max(compute_loads(n, m, P, alpha))

    opt_cmax, _, _ = exact_optimal_makespan(n, m, P, initial_ub=approx_cmax + 1)
    ratio = approx_cmax / opt_cmax
    assert ratio <= 2.0 + 1e-9
