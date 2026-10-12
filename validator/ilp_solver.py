"""
ILP Optimal Makespan Solver (PuLP).

Formulates the exact unrelated machine scheduling problem as an integer
linear program to find the true OPT for comparison with the 2-approximation:

    min  C_max
    s.t. sum_j x_ij = 1                  for all i in J
         sum_i p_ij * x_ij <= C_max      for all j in M
         x_ij in {0, 1}

Only feasible for moderate instances (n <= 200, m <= 50).
"""

from typing import List, Tuple, Optional
from data_structures import INF


def ilp_optimal_makespan(
    n: int, m: int,
    P: List[List[int]],
    time_limit_s: int = 60,
) -> Tuple[Optional[int], Optional[List[int]]]:
    """
    Solve exact unrelated machine makespan minimization using PuLP.

    Parameters
    ----------
    n, m : int
        Number of jobs and machines.
    P : list[list[int]]
        n × m ToA matrix (INF for infeasible).
    time_limit_s : int
        Solver time limit in seconds.

    Returns
    -------
    (opt_makespan, alpha) or (None, None) if infeasible, timed out, or no solver.
    """
    try:
        import pulp
    except ImportError:
        print("[ILP] PuLP not installed.")
        return None, None

    # Check solver availability
    available_solvers = pulp.listSolvers(onlyAvailable=True)

    prob = pulp.LpProblem("Makespan_Min", pulp.LpMinimize)

    # Decision variables (compatible with PuLP 4.x and < 4.x)
    x = {}
    is_pulp4 = hasattr(prob, "add_variable")

    for i in range(n):
        for j in range(m):
            if P[i][j] < INF:
                if is_pulp4:
                    x[i, j] = prob.add_variable(f"x_{i}_{j}", cat="Binary")
                else:
                    x[i, j] = pulp.LpVariable(f"x_{i}_{j}", cat="Binary")

    if is_pulp4:
        C_max = prob.add_variable("C_max", lowBound=0, cat="Integer")
    else:
        C_max = pulp.LpVariable("C_max", lowBound=0, cat="Integer")

    # Objective: minimise makespan
    prob += C_max

    # Constraint 1: each job assigned to exactly one machine
    for i in range(n):
        feasible_j = [j for j in range(m) if P[i][j] < INF]
        if not feasible_j:
            return None, None  # Infeasible instance
        prob += pulp.lpSum(x[i, j] for j in feasible_j) == 1, f"assign_{i}"

    # Constraint 2: makespan ≥ load on each machine
    for j in range(m):
        assigned_jobs = [i for i in range(n) if (i, j) in x]
        if assigned_jobs:
            prob += (
                pulp.lpSum(P[i][j] * x[i, j] for i in assigned_jobs) <= C_max,
                f"load_{j}",
            )

    # Solve
    try:
        if available_solvers:
            solver = pulp.getSolver(available_solvers[0], timeLimit=time_limit_s, msg=False)
            status = prob.solve(solver)
        else:
            raise RuntimeError("No external solver binary (CBC/GLPK/HiGHS) registered in PuLP")
    except Exception as e:
        print(f"[ILP] {e}. Falling back to pure Python exact Branch-and-Bound solver...")
        from validator.bruteforce_comparator import exact_optimal_makespan
        opt, alpha, _ = exact_optimal_makespan(n, m, P, time_limit_s=float(time_limit_s))
        return opt, alpha

    if pulp.LpStatus.get(status) not in ("Optimal", "Not Solved"):
        return None, None

    if pulp.value(C_max) is None:
        return None, None

    opt = int(round(pulp.value(C_max)))

    # Extract assignment
    alpha = [-1] * n
    for i in range(n):
        for j in range(m):
            if (i, j) in x and pulp.value(x[i, j]) is not None:
                if pulp.value(x[i, j]) > 0.5:
                    alpha[i] = j
                    break

    if any(a < 0 for a in alpha):
        return opt, None

    return opt, alpha
