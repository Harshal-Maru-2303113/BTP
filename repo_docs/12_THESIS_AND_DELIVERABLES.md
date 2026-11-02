# Thesis & Deliverables

## Academic Thesis (main.tex → main.pdf)

A complete ~15-page academic BTP report in IEEE format covering:

### Sections

1. **System Model and Problem Statement** (§1)
   - Network/hardware model (8 channels × 6 SFs = 48 machines)
   - Traffic model (harmonic periodic, real-time deadlines)
   - ToA matrix formulation (Semtech SX1276)
   - Problem formulation (R || C_max)
   - Machine load makespan vs timeline calendar span distinction

2. **Combinatorial 2-Approximation on Unrelated Machines** (§2)
   - Generalized unsplittable flow formulation
   - Residual network and machine partitioning (M⁺, M⁰, M⁻)
   - Gain rounding and Truemper's logarithmic transformation
   - Node potentials and reduced cost optimality

3. **Algorithmic Mechanics and Theoretical Proofs** (§3)
   - Inner loop: Unsplittable-Blocking-Flow (Algorithm 1, Theorem 2.3)
   - Outer loop: Unsplittable-Truemper (Algorithm 2, Theorem 3.3)
   - Binary search and 2-approximation theorem (Theorem 3.4)
   - Formal pseudocode for all 3 algorithms

4. **LoRaWAN Hypercycle Scheduling with Hardware Constraints** (§4)
   - Gateway demodulation constraint (8 concurrent)
   - Phase 1.5: Energy-optimal capacity-constrained downshifting (Theorem 4.1)
   - Per-channel EDF timeline with segment tree
   - Complete Algorithm 3 pseudocode

5. **Time Complexity Analysis** (§5)
   - Phase-by-phase breakdown with formal proofs
   - Overall system bound: O(m²·A·log m·log Δw + k_drop·n·log H)
   - Hardware-fixed bound: O(n²·log H); quasi-linear when k_drop = 0

6. **Experimental Validation** (§6)
   - Approximation ratio: 1302/800 = 1.6275 ≤ 2.0
   - Demodulation occupancy: peak 8/8
   - Radio energy consumption analysis (Casals et al. 2017)
   - Physical bottleneck analysis of drops

7. **Conclusion and Future Work** (§7)
   - Dynamic TPC, runtime slack reclamation, (m,k)-firm deadlines

### LaTeX Structure
- `main.tex` — main document
- `preamble.tex` — packages, macros, formatting
- `refr.bib` — bibliography (Gairing et al., Semtech, Graham, etc.)
- `IEEEtran.bst` — IEEE bibliography style
- `main.pdf` — compiled output

---

## Documentation Deliverables

| File | Content |
|---|---|
| `upper_bound_proof.md` | Complete 600-line proof of the 2-approximation upper bound |
| `baseline_comparison.md` | Detailed baseline analysis + 5-suite stress test results |
| `simulation_report.md` | Large-scale simulation results (n=100 to 10,000) |
| `input.md` | System input and configuration guide |
| `output.md` | Output specifications and metric verification |
| `README.md` | Project overview, architecture diagram, quick start |

---

## Key Numbers for Presentations

### End-to-End Pipeline Benchmark (main.py / Thesis §6)
| Metric | Value | Context |
|---|---|---|
| Total packets generated | 234 | 50 end-devices, harmonic periods |
| Packets scheduled | 101 (43.16%) | Full temporal & demod feasibility |
| Packets dropped | 133 (56.84%) | Physical limitation ($t=0$ synchronous release saturation) |
| Timeline calendar span | 90,072 ms | Within $H = 100,000$ ms hypercycle (90.07% utilization) |
| Machine load makespan | **1,302 ms** | Maximum single-channel airtime burden |
| Exact OPT makespan (B&B) | **800 ms** | Exact combinatorial minimum on scheduled subset |
| **Empirical approx ratio** | **1.6275 ≤ 2.0 ✅** | **18.6% safety margin below theoretical 2.0 bound** |
| Peak concurrent demod | 8 / 8 ✅ | Never exceeds SX1301/1302 hardware limit |
| Scheduler execution time | ~0.4–0.6s | Linear with respect to packet count |

### Full Workload Allocation Benchmark (run_baseline_comparison.py)
| Metric | Value | Context |
|---|---|---|
| Workload | 234 packets | All packets assigned across 48 machines (Phase 1 only) |
| Critical threshold $w^*$ | 775 ms | Binary search certificate ($OPT \ge 775$ ms) |
| 2-Approx makespan | **1,545 ms** | All machines $\le 2w^*$ |
| Exact OPT makespan (ILP) | **933 ms** | Exact global optimum |
| **Empirical approx ratio** | **1.656 ≤ 2.0 ✅** | Ratio to exact OPT ($1,545 / 933$) |
| **Total radio energy (2-Approx)** | **6,493.8 mJ** | Lowest energy among all coordinated algorithms |
| Baseline energy overhead | +34.5% to +45.1% | Heuristics offload to higher SFs, inflating energy |
| Worst heuristic ratio | 3.31× | Greedy LL & Min-Min on adversarial stress tests |
| Random ALOHA worst | 22.1× | Pure uncoordinated baseline degradation |
| Hardness lower bound | 3/2 (1.50×) | Lenstra, Shmoys & Tardos (1990) NP-hardness bound |

---

## References Used in the Project

1. **Gairing, Monien, Woclaw (2007)** — Base 2-approximation algorithm (TCS)
2. **Semtech SX1276 Datasheet §4.1.1.7** — LoRa Modem Designer's Guide (exact ToA formula)
3. **Casals, Mir, Vidal, Gomez (2017)** — "Modeling the Energy Performance of LoRaWAN", Sensors 17(10):2364
4. **Bouguera et al. (2018)** — "Energy Consumption Model for Sensor Nodes Based on LoRa and LoRaWAN", Sensors 18(7):2104
5. **Graham (1966)** — List scheduling bounds
6. **Ibarra & Kim (1977)** — Min-Min, Max-Min heuristics
7. **Braun et al. (2001)** — Comparison of 11 static heuristics
8. **Lenstra, Shmoys & Tardos (1990)** — 2-approx via LP rounding; 3/2 hardness lower bound

