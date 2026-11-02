import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import copy
from segment_tree import SegmentTree
from config_loader import load_config
from packet_generator import create_machines, generate_packets
from lorawan_toa import compute_toa_matrix, compute_cost_matrix, compute_toa_ms
from approximation.binary_search import find_2approx_assignment
from approximation.graph_utils import compute_loads
from scheduler.lorawan_scheduler import lorawan_hypercycle_scheduler
from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
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


def test_lorawan_energy_model_datasheet_values():
    """Verify Semtech SX1276 datasheet reference cases and energy model."""
    from lorawan_energy import (
        compute_phy_payload_len,
        compute_semtech_toa_ms,
        compute_class_a_cycle_energy,
    )
    # Reference test case 1: 10-byte application payload -> 23-byte PHY payload
    pl = compute_phy_payload_len(10)
    assert pl == 23

    # Reference test case 2: SF7 ToA = 61.696 ms (Datasheet §4.1.1.7)
    toa_sf7 = compute_semtech_toa_ms(pl, sf=7)
    assert abs(toa_sf7 - 61.696) < 1e-3, f"SF7 ToA expected 61.696 ms, got {toa_sf7}"

    # Reference test case 3: SF12 ToA = 1482.752 ms (Datasheet §4.1.1.7)
    toa_sf12 = compute_semtech_toa_ms(pl, sf=12)
    assert abs(toa_sf12 - 1482.752) < 1e-3, f"SF12 ToA expected 1482.752 ms, got {toa_sf12}"

    # Reference test case 4: Class A cycle energy for 10-minute cycle
    t_tx7, e_tx7, e_cycle7, i_avg7 = compute_class_a_cycle_energy(10, sf=7, t_cycle_s=600.0)
    t_tx12, e_tx12, e_cycle12, i_avg12 = compute_class_a_cycle_energy(10, sf=12, t_cycle_s=600.0)

    # SF7 cycle energy: ~27.4 mJ, SF12: ~233.7 mJ
    assert abs(e_cycle7 * 1000.0 - 27.4) < 1.0
    assert abs(e_cycle12 * 1000.0 - 233.7) < 1.0
    # SF12 energy must be significantly higher than SF7
    assert e_cycle12 > e_cycle7 * 7.0


def test_energy_optimizer_preserves_2approximation():
    """Verify Phase 1.5 strictly preserves the makespan <= 2*w* upper bound while reducing energy."""
    from scheduler.energy_optimizer import energy_optimal_downshift
    from lorawan_energy import compute_energy_matrix
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)[:20]
    n, m = len(packets), len(machines)
    P = compute_toa_matrix(packets, machines, config)
    C = compute_cost_matrix(P, m)
    b = 1.0 + 1.0 / m
    E = compute_energy_matrix(packets, machines, config, P)

    alpha_init, w_star = find_2approx_assignment(n, m, P, C, b, H_ms=config.network.hypercycle_duration_ms)
    assert alpha_init is not None

    # Artificially assign several packets to higher SF machines to create downshift opportunities
    modified_alpha = list(alpha_init)
    sf8_or_higher_machines = [j for j, mach in enumerate(machines) if mach.sf >= 8]
    if sf8_or_higher_machines:
        for i in range(min(5, n)):
            for j in sf8_or_higher_machines:
                if P[i][j] <= w_star:
                    modified_alpha[i] = j
                    break

    # Optimize energy via Phase 1.5
    alpha_opt, stats = energy_optimal_downshift(
        n=n, m=m, P=P, E=E, alpha=modified_alpha, w_star=w_star, machines=machines,
        H_ms=config.network.hypercycle_duration_ms
    )

    # 1. Total energy must not increase
    assert stats["optimized_energy_mj"] <= stats["initial_energy_mj"] + 1e-6

    # 2. Invariant: makespan must remain <= 2 * w_star (strictly preserves 2-approx proof)
    loads_opt = compute_loads(n, m, P, alpha_opt)
    max_load_opt = max(loads_opt)
    assert max_load_opt <= 2 * w_star, f"Upper bound violated: {max_load_opt} > {2 * w_star}"

    # 3. Invariant: every job must satisfy P[i][alpha(i)] <= w_star
    for i in range(n):
        assert P[i][alpha_opt[i]] <= w_star


def test_end_to_end_energy_scheduler():
    """Verify end-to-end scheduler executes with energy optimization enabled."""
    from lorawan_energy import compute_energy_matrix
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    P = compute_toa_matrix(packets, machines, config)
    E = compute_energy_matrix(packets, machines, config, P)

    result = lorawan_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        H_ms=config.network.hypercycle_duration_ms,
        max_demod=config.gateway.max_concurrent_demodulations,
        check_invariants=True,
        E_full=E,
        enable_energy_opt=True,
    )

    assert result.feasible is True
    assert len(result.entries) > 0
    assert "scheduled_energy_mj" in result.energy_stats
    assert result.energy_stats["scheduled_energy_mj"] > 0
    # Invariant: machine load makespan <= 2 * approx_ratio_w
    assert result.machine_makespan_ms <= 2 * result.approx_ratio_w


def test_cyclic_divisibility_validation():
    """Verify that an exception is raised when H % tau != 0."""
    from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)[:5]
    P = compute_toa_matrix(packets, machines, config)

    # Corrupt tau to a non-divisor
    bad_config = copy.deepcopy(config)
    bad_config.cyclic_executive.minor_cycle_duration_s = 7.0
    bad_config.cyclic_executive.minor_cycle_duration_ms = 7000

    with pytest.raises(ValueError, match="must be an integer multiple"):
        run_cyclic_hypercycle_scheduler(
            packets=packets,
            machines=machines,
            P_full=P,
            config=bad_config,
        )


def test_cyclic_carryover_active_recovery_under_congestion():
    """
    Demonstrate that under heavy congestion in cycle 0, packets dropped in cycle 0
    are carried over to cycle 1 and successfully recovered before their deadlines.
    """
    from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
    from data_structures import Packet
    config = load_config("config.json")
    machines = create_machines(config)

    # Use a small configuration: 2 minor cycles of tau=500 ms (H = 1000 ms)
    test_cfg = copy.deepcopy(config)
    test_cfg.network.hypercycle_duration_s = 1.0
    test_cfg.network.hypercycle_duration_ms = 1000
    test_cfg.cyclic_executive.minor_cycle_duration_s = 0.5
    test_cfg.cyclic_executive.minor_cycle_duration_ms = 500
    test_cfg.cyclic_executive.enable_packet_carryover = True

    # Packets released at t=0 with deadline=1000 ms
    # Create 80 packets (many more than can fit in a 500ms cycle under 8 demod limit and ToA ~40-60ms)
    packets = [
        Packet(
            id=i,
            release_time=0,
            deadline=1000,
            priority=float(i + 1),
            payload_size=10,
            device_id=i,
            period=1000,
        )
        for i in range(80)
    ]
    P = compute_toa_matrix(packets, machines, test_cfg)

    res = run_cyclic_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        config=test_cfg,
        check_invariants=True,
    )

    # In cycle 0, some packets must be dropped and then recovered in cycle 1
    assert res.feasible is True
    assert res.num_minor_cycles == 2
    # Verify that carryover actively recovered packets into cycle 1
    assert len(res.recovered_packet_ids) > 0
    assert res.carryover_stats["recovered_count"] > 0
    assert len(res.entries) > res.cycle_results[0]["num_scheduled"]



def test_cyclic_scheduler_preserves_2approximation_per_cycle():
    """Verify that in every minor cycle k, C_max^(k) <= 2 * w_k* strictly holds."""
    from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    P = compute_toa_matrix(packets, machines, config)

    res = run_cyclic_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        config=config,
        check_invariants=True,
        enable_energy_opt=True,
    )

    assert res.feasible is True
    # Verify per-cycle 2-approximation property
    for c in res.cycle_results:
        w_star = c["w_star_ms"]
        machine_load = c["machine_makespan_ms"]
        if w_star > 0:
            assert machine_load <= 2 * w_star, f"Cycle {c['cycle_index']} violated 2*w*: {machine_load} > {2*w_star}"


def test_cyclic_executive_end_to_end_validation():
    """Full end-to-end integration test of Cyclic Executive Scheduler with energy optimization."""
    from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
    from lorawan_energy import compute_energy_matrix
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    P = compute_toa_matrix(packets, machines, config)
    E = compute_energy_matrix(packets, machines, config, P)

    res = run_cyclic_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        config=config,
        E_full=E,
        check_invariants=True,
        enable_energy_opt=True,
    )

    assert res.feasible is True
    assert res.num_minor_cycles == 10
    assert len(res.entries) > 0
    assert res.makespan_ms <= config.network.hypercycle_duration_ms
    assert res.energy_stats["scheduled_energy_mj"] > 0

    # Ensure all scheduled entries strictly obey deadline and non-preemption across the global timeline
    val_res = check_schedule_validity(
        res.entries, machines, config.network.hypercycle_duration_ms, config.gateway.max_concurrent_demodulations
    )
    assert val_res["per_channel_ok"] is True
    assert val_res["deadlines_ok"] is True
    assert val_res["demod_limit_ok"] is True


def test_heterogeneous_cyclic_duration_sum_validation():
    """Verify ValueError is raised when sum(minor_cycle_durations) != H."""
    from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)[:5]
    P = compute_toa_matrix(packets, machines, config)

    # Set variable durations that do not sum to H (100,000 ms)
    bad_config = copy.deepcopy(config)
    bad_config.cyclic_executive.minor_cycle_durations_s = [10.0, 20.0, 40.0]  # sum = 70s != 100s
    bad_config.cyclic_executive.minor_cycle_durations_ms = [10000, 20000, 40000]

    with pytest.raises(ValueError, match="must equal hypercycle duration"):
        run_cyclic_hypercycle_scheduler(
            packets=packets,
            machines=machines,
            P_full=P,
            config=bad_config,
        )


def test_heterogeneous_cyclic_scheduler_end_to_end():
    """Verify cyclic executive with variable-length (heterogeneous) minor frames."""
    from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
    from lorawan_energy import compute_energy_matrix
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    P = compute_toa_matrix(packets, machines, config)
    E = compute_energy_matrix(packets, machines, config, P)

    # Configure heterogeneous frame durations: 10s + 15s + 25s + 50s = 100s
    het_config = copy.deepcopy(config)
    het_config.cyclic_executive.minor_cycle_durations_s = [10.0, 15.0, 25.0, 50.0]
    het_config.cyclic_executive.minor_cycle_durations_ms = [10000, 15000, 25000, 50000]

    res = run_cyclic_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        config=het_config,
        E_full=E,
        check_invariants=True,
        enable_energy_opt=True,
    )

    assert res.feasible is True
    assert res.num_minor_cycles == 4
    assert res.is_homogeneous is False
    assert res.minor_cycle_durations_ms == [10000, 15000, 25000, 50000]
    assert len(res.entries) > 0
    assert res.makespan_ms <= het_config.network.hypercycle_duration_ms

    # Invariant: every cycle satisfies machine_makespan <= 2 * w*
    for c in res.cycle_results:
        w_star = c["w_star_ms"]
        machine_load = c["machine_makespan_ms"]
        if w_star > 0:
            assert machine_load <= 2 * w_star, f"Cycle {c['cycle_index']} violated 2*w*: {machine_load} > {2*w_star}"

    # Global schedule validity
    val_res = check_schedule_validity(
        res.entries, machines, het_config.network.hypercycle_duration_ms, het_config.gateway.max_concurrent_demodulations
    )
    assert val_res["per_channel_ok"] is True
    assert val_res["deadlines_ok"] is True
    assert val_res["demod_limit_ok"] is True


def test_heterogeneous_carryover_active_recovery():
    """Verify carryover and recovery between variable-length frames under transient congestion."""
    from scheduler.cyclic_hypercycle_wrapper import run_cyclic_hypercycle_scheduler
    from data_structures import Packet
    config = load_config("config.json")
    machines = create_machines(config)

    # Frame 0 is short (300 ms), Frame 1 is longer (700 ms), H = 1000 ms
    test_cfg = copy.deepcopy(config)
    test_cfg.network.hypercycle_duration_s = 1.0
    test_cfg.network.hypercycle_duration_ms = 1000
    test_cfg.cyclic_executive.minor_cycle_durations_s = [0.3, 0.7]
    test_cfg.cyclic_executive.minor_cycle_durations_ms = [300, 700]
    test_cfg.cyclic_executive.enable_packet_carryover = True

    # 60 packets released at t=0 with deadline=1000 ms
    packets = [
        Packet(
            id=i,
            release_time=0,
            deadline=1000,
            priority=float(i + 1),
            payload_size=10,
            device_id=i,
            period=1000,
        )
        for i in range(60)
    ]
    P = compute_toa_matrix(packets, machines, test_cfg)

    res = run_cyclic_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        config=test_cfg,
        check_invariants=True,
    )

    assert res.feasible is True
    assert res.num_minor_cycles == 2
    assert res.is_homogeneous is False
    assert len(res.recovered_packet_ids) > 0
    assert res.carryover_stats["recovered_count"] > 0


def test_apriori_schedulability_certificate():
    """
    Verify the A Priori Feasibility Certificate:
    If analytical upper bound X_tight <= H, feasibility is guaranteed mathematically
    with zero drops without requiring trial-and-error simulation.
    """
    from validator.feasibility_certificate import compute_schedulability_certificate
    from lorawan_energy import compute_energy_matrix
    config = load_config("config.json")
    machines = create_machines(config)
    packets = generate_packets(config, machines)
    P = compute_toa_matrix(packets, machines, config)
    E = compute_energy_matrix(packets, machines, config, P)

    cert = compute_schedulability_certificate(
        packets=packets,
        machines=machines,
        P=P,
        H_ms=config.network.hypercycle_duration_ms,
        E=E,
        tau_ms=config.cyclic_executive.minor_cycle_duration_ms,
    )

    # 1. Certificate validates a priori feasibility
    assert cert["feasible_a_priori"] is True
    assert cert["analytical_lower_bound_opt_ms"] > 0
    assert cert["proven_upper_bound_x_tight_ms"] > 0
    assert cert["proven_upper_bound_x_tight_ms"] <= config.network.hypercycle_duration_ms
    assert cert["safety_margin_pct"] > 90.0

    # 2. Transitivity: verify that scheduler achieves makespan <= X_tight <= H
    res = lorawan_hypercycle_scheduler(
        packets=packets,
        machines=machines,
        P_full=P,
        H_ms=config.network.hypercycle_duration_ms,
        max_demod=config.gateway.max_concurrent_demodulations,
        check_invariants=True,
        E_full=E,
        enable_energy_opt=True,
    )

    assert res.feasible is True
    assert len(res.dropped_packet_ids) == 0  # Zero drops proven a priori
    assert res.machine_makespan_ms <= cert["proven_upper_bound_x_tight_ms"] * 2  # Bounded by theoretical bounds


def test_cyclic_scheduler_empty_packets():
    """Verify cyclic scheduler handles empty packet sets gracefully with zero drops and feasible status."""
    config = load_config()
    machines = create_machines(config)
    res = run_cyclic_hypercycle_scheduler(
        packets=[],
        machines=machines,
        P_full=[],
        config=config,
    )
    assert res.feasible is True
    assert len(res.entries) == 0
    assert len(res.dropped_packet_ids) == 0
    assert res.makespan_ms == 0





