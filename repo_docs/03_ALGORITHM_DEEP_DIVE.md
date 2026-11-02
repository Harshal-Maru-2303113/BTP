# Algorithm Deep Dive

## The 3-Phase Algorithm

### Phase 1: 2-Approximation Makespan Minimisation

**Goal**: Find an assignment α of packets to machines such that max machine load ≤ 2 · OPT.

#### Layer 1: Binary Search (`binary_search.py`)

- Search over candidate makespan `w` in `[w_min, w_max]`
- `w_min = max(max_i min_j P[i][j], ceil(sum(min_j P[i][j]) / m))`
- `w_max = min(H_ms, (ceil(sum_min / m) + max(max_toas)) * 2)` (clamped to hypercycle duration)
- For each candidate `w`, call Unsplittable-Truemper
- If Truemper succeeds (M⁺ = ∅): record best and try lower w
- If Truemper fails: OPT ≥ w + 1, try higher w
- Returns `(alpha, w_star)` — best assignment and critical threshold

#### Layer 2: Unsplittable-Truemper (`truemper.py`)

- **Input**: n, m, P, C (cost matrix), w, b (rounding base)
- **Initial assignment**: Each job to its min-ToA feasible machine (among those with P[i][j] ≤ w)
- **Node potentials**: π_mach[j] = 0, π_job[i] = C[i][α(i)]
- **Main loop** (at most O(m·log_b(m)) iterations):
  1. Compute M⁺ (loads ≥ 2w+1) and M⁻ (loads ≤ w)
  2. If M⁺ = ∅ → **success**, return α
  3. If any M⁺ potential ≥ log_b(m) → **fail** (OPT ≥ w+1)
  4. Run **Dijkstra** on reversed residual graph (reduced costs) to find shortest distances to M⁻
  5. If no M⁺ machine reaches M⁻ → **fail**
  6. Update potentials: π ← π + d
  7. Build **admissible graph** (zero reduced cost edges)
  8. Restrict to subgraph reachable from M⁺_min (lowest-potential M⁺ machines)
  9. Call **Unsplittable-Blocking-Flow** on this subgraph
  10. Recompute loads

#### Layer 3: Unsplittable-Blocking-Flow (`blocking_flow.py`)

- **Input**: n, m, α, loads, admissible adjacency, P, w
- Works in phases (at most m phases):
  1. Compute **BFS heights** from M⁻ in admissible graph
  2. Find **helpful machines**: j ∈ M⁺ with h(j) < ∞ and load ≥ w+1+P[s(j)][j]
  3. Pick helpful machine of minimum height
  4. Build **helpful path**: alternating machine-job-machine sequence
     - Terminal machine must stay ≤ 2w after receiving
     - Intermediate machines must stay in [w+1, 2w] after swap
  5. **Push** jobs along the path: reassign each job to the next machine
  6. Update adjacency (reverse edge directions)
  7. Repeat until no more helpful machines or M⁺/M⁻ empty

#### Supporting: Graph Utilities (`graph_utils.py`)

- `compute_loads(n, m, P, alpha)` — machine loads from assignment
- `dijkstra_to_sinks(...)` — multi-source Dijkstra on reversed residual with reduced costs
- `build_admissible_graph(...)` — extract zero-reduced-cost edges
- `bfs_heights(...)` — BFS hop distances to sinks for level graph
- `get_admissible_successors(u, adj, h)` — successors with h(u) = h(v) + 1

---

### Phase 1.5: Energy-Optimal Capacity-Constrained Downshifting (`energy_optimizer.py`)

**Goal**: Minimize total fleet radio energy consumption $\sum_i E[i][\alpha(i)]$ by downshifting packets from higher spreading factors to lower spreading factors, **subject to preserving the 2-approximation makespan upper bound**.

- **Energy Gradient**: Transmitting at higher SF requires exponentially more airtime ($T_{\text{sym}} = 2^{\text{SF}}/\text{BW}$) and energy ($E_{\text{SF12}} \approx 8.5\times E_{\text{SF7}}$).
- **Core Optimization Mechanics**:
  1. Determine machine capacity ceiling: $\text{cap}_j = 2 w^* \le 2 \cdot \text{OPT}(P)$ (clamped to $H$).
  2. For each packet $i$ on machine $j = \alpha(i)$ with $\text{SF} > 7$:
     - Evaluate all feasible lower-SF machines $j'$ where $P[i][j'] \le w^*$.
     - Verify capacity constraint: $\delta_{j'} + P[i][j'] \le 2 w^*$.
     - Compute energy reduction: $\Delta E = E[i][j] - E[i][j'] > 0$.
  3. Greedily execute highest-$\Delta E$ downshifts while dynamically updating machine loads $\delta_j \leftarrow \delta_j - P[i][j]$ and $\delta_{j'} \leftarrow \delta_{j'} + P[i][j']$.
  4. Perform secondary load-leveling across channels within the same SF.
- **Provable Invariant**: Because every transition maintains $\delta_k \le 2 w^*$, the maximum load under $\alpha^*$ unconditionally satisfies:
  $$\max_{k \in \mathcal{M}} \delta_k \le 2 w^* \le 2 \cdot \text{OPT}(P)$$
  The 2-approximation theorem and upper bound proof remain **100% intact**.
- **Downstream Benefit for Phase 2**: Lower SF transmissions have vastly shorter ToA, freeing timeline slots, drastically reducing demodulator contention $\Omega(t) \le 8$, and decreasing drop rates in Phase 3.

---

### Phase 2: EDF Timeline with Demod Tracking (`lorawan_scheduler.py`)

**Goal**: Place packets on the timeline respecting release times, deadlines, per-channel non-preemption, and the 8-demod constraint.

- Group packets by assigned machine; sort each group by deadline (EDF)
- Use a **min-heap** to interleave placement across all machines (earliest start first)
- For each packet:
  1. Compute start = max(channel_cursor, release_time)
  2. Query **segment tree** for peak demod occupancy in [start, finish-1]
  3. If peak ≥ 8: scan forward to find a clear window (demod-aware shifting)
  4. If no clear window found within hypercycle → **demod violator**
  5. Check deadline: if finish > deadline or finish > H → **deadline violator**
  6. Otherwise: place packet, update segment tree with range_add, advance cursor

The **segment tree** (`segment_tree.py`) is a max segment tree with lazy propagation:
- `range_add(l, r, val)` — increment every slot in [l, r]
- `range_max(l, r)` — query maximum in [l, r]
- Size: H_ms = 100,000 slots (one per millisecond)

---

### Phase 3: Priority-Based Dropping (`lorawan_scheduler.py`)

**Goal**: Remove infeasible packets while preserving the most important ones.

- If Phase 2 identifies violators: drop the lowest-priority offender
- Drop ordering: `(lowest priority, latest deadline, highest ID)` — this means less important, less urgent packets are dropped first
- After dropping, **retry Phase 2** with the pruned assignment (no need to re-run Phase 1!)
- If makespan > H (from Phase 1): drop lowest-priority candidate and re-run Phase 1

---

### Phase 4 (Executive Layer): Hierarchical Cyclic Executive & Carryover Buffer (`cyclic_hypercycle_wrapper.py`)

**Goal**: Partition the major hypercycle $H$ into $K$ minor operational dispatch frames $\tau_k$ (which can be of **same length** $\tau$ or **different lengths** $\tau_0, \dots, \tau_{K-1}$ summing to $H$) and recover transiently dropped packets in subsequent cycles if their deadlines permit.

1. **Macro / Micro Hierarchy**:
   - $H = \text{lcm}(T_k)$ is the repeating macro-horizon.
   - **Homogeneous (Uniform) Frames**: $\tau_k = \tau$ for all $k$, with $H = K \cdot \tau$ ($H \pmod \tau = 0$).
   - **Heterogeneous (Variable-Length) Frames**: durations $\tau_k > 0$ can vary per frame, satisfying $\sum_{k=0}^{K-1} \tau_k = H$, defining execution windows $[t_k, t_{k+1})$.
2. **Carryover Queue with Slack Viability**:
   - For periodic LoRaWAN sensor traffic, $D_i = r_i + T_i$.
   - When $T_i > \tau_k$, a packet dropped in frame $k$ has valid remaining slack.
   - It is carried over to frame $k+1$ if and only if $t_{k+1} + \min_j p_{ij} \le D_i$, $\text{hops} < h_{\max}$, and $t_{k+1} < H$.
   - Packets failing this check are unrecoverable hard drops.
3. **Priority Escalation**:
   - Carried packets receive boosted priority: $\Pi'_i = \Pi_i + \text{hops} \cdot \Delta_{\Pi}$ to prevent starvation and bound latency.
4. **Unconditional 2-Approximation Preservation**:
   - In every minor frame $k$, Phase 1 and Phase 1.5 run on candidate set $\mathcal{J}^{(k)}$ over frame horizon $\tau_k$, ensuring $C_{\max}^{(k)} \le 2 w_k^* \le 2 \cdot \text{OPT}_k \le \tau_k$.
   - Since frame windows $[t_k, t_{k+1})$ are temporally disjoint, per-channel non-preemption and gateway demodulation occupancy $\Omega(t) \le 8$ hold globally over all $t \in [0, H]$.

---

## The Cost Matrix (Truemper's Logarithmic Transformation)

```
b = 1 + 1/m       (rounding base, e.g., 1.0208 for m=48)
C[i][j] = floor(log_b(P[i][j]))
```

This logarithmic transform converts multiplicative gains into additive costs, enabling shortest-path-based primal-dual optimisation while introducing at most 1/m relative error per edge.

---

## Key Invariants Maintained by the Algorithm

1. **Assignment feasibility**: P[i][α(i)] ≤ w for all jobs i
2. **Reduced-cost optimality**: c^π(u,v) ≥ 0 for all residual edges
3. **Load partition**: After blocking flow, M⁻ loads ↑, M⁰ stays in [w+1, 2w], M⁺ loads ↓
4. **Path gain invariant**: γ(W) ≥ 1 for all paths from M⁺ to any machine (proved via potentials from M⁺_min)
5. **Lower bound certificate**: If Truemper fails → OPT ≥ w + 1

---

## Time Complexity Summary

| Component | Complexity |
|---|---|
| ToA matrix | O(n·m) |
| Dijkstra (per Truemper iteration) | O(A·log(n+m)) |
| Blocking flow (inner loop) | O(m·A) |
| Truemper (outer loop) | O(m²·A·log m) |
| Binary search | O(log Δw) calls |
| **Phase 1 total** | **O(m²·A·log m·log Δw)** |
| Phase 2 single pass | O(n·(log n + log m + log H)) |
| Phase 3 (k drops) | O(k·n·(log m + log H)) |
| **For fixed m=48** | **O(n·log Δw + n²·log H)** |

