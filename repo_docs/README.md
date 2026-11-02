# LoRaWAN Hypercycle Scheduler — Documentation Index

Welcome to the comprehensive technical documentation for the **LoRaWAN Hypercycle Real-Time Packet Scheduler** Bachelor's Thesis Project (BTP).

This folder (`repo_docs/`) contains modular, deep-dive documentation covering the algorithm, codebase architecture, mathematical proofs, domain specifications, experimental evaluation, and thesis deliverables.

---

## 📚 Document Index

| # | Document | Description | Key Topics |
|:---:|---|---|---|
| **01** | [Project Overview](file:///home/harshal/Projects/BTP/repo_docs/01_PROJECT_OVERVIEW.md) | High-level problem statement and solution summary | Problem definition, $R \parallel C_{\max}$, GMW 2007 base paper, quick start |
| **02** | [Architecture](file:///home/harshal/Projects/BTP/repo_docs/02_ARCHITECTURE.md) | System structure, data flow, and module boundaries | Pipeline walkthrough, module dependency graph, directory layout |
| **03** | [Algorithm Deep Dive](file:///home/harshal/Projects/BTP/repo_docs/03_ALGORITHM_DEEP_DIVE.md) | The complete 4-phase scheduling algorithm | Phase 1 (Truemper + Blocking Flow), Phase 1.5 (Energy Downshift), Phase 2 (EDF + Segment Tree), Phase 3 (Dropping) |
| **04** | [Data Structures](file:///home/harshal/Projects/BTP/repo_docs/04_DATA_STRUCTURES.md) | Core classes, state schemas, and segment tree | `Packet`, `Machine`, `ScheduleEntry`, `SegmentTree` interval tree, Semtech ToA model |
| **05** | [Baselines & Evaluation](file:///home/harshal/Projects/BTP/repo_docs/05_BASELINES_AND_EVALUATION.md) | Comparative evaluation against heuristics and OPT | Earliest Deadline First (EDF), Shortest Processing Time (SPT), Least Loaded, Random, ILP |
| **06** | [Configuration Reference](file:///home/harshal/Projects/BTP/repo_docs/06_CONFIGURATION_REFERENCE.md) | `config.json` parameters and CLI flags | System hyperparameters, channel frequencies, SF configs, traffic patterns, CLI options |
| **07** | [Tests & Validation](file:///home/harshal/Projects/BTP/repo_docs/07_TESTS_AND_VALIDATION.md) | Test suite and physical invariant checkers | Pytest suite, `InvariantChecker` (no overlap, demod $\le 8$, deadlines), brute-force verifier |
| **08** | [LoRaWAN Domain Knowledge](file:///home/harshal/Projects/BTP/repo_docs/08_LORAWAN_DOMAIN.md) | Physical and protocol constraints of LoRaWAN | Orthogonality, SX1301/SX1302 8-channel demodulator limit, Time-on-Air (ToA) analysis |
| **09** | [Key Theorems & Proofs](file:///home/harshal/Projects/BTP/repo_docs/09_KEY_THEOREMS_AND_PROOFS.md) | Formal proofs of theoretical bounds | Upper bound proof ($C_{\max} \le 2 \cdot \text{OPT}$), Theorem 3.3/3.4, feasibility preservation |
| **10** | [Output Format Reference](file:///home/harshal/Projects/BTP/repo_docs/10_OUTPUT_FORMAT.md) | File outputs, console format, and metrics | `schedule.json`, `simulation_results.json`, logs, console reports, metric definitions |
| **11** | [Function Index](file:///home/harshal/Projects/BTP/repo_docs/11_FUNCTION_INDEX.md) | API reference of all public functions and methods | Signatures, parameters, return types, and file locations across all modules |
| **12** | [Thesis & Deliverables](file:///home/harshal/Projects/BTP/repo_docs/12_THESIS_AND_DELIVERABLES.md) | LaTeX thesis structure and deliverable artifacts | Chapter mapping (`main.tex`), published benchmarks, experimental results, bibtex |

---

## 🎯 Recommended Reading Paths

### 🔬 For Algorithmic & Theoretical Review
1. [01_PROJECT_OVERVIEW.md](file:///home/harshal/Projects/BTP/repo_docs/01_PROJECT_OVERVIEW.md) — Problem abstraction and high-level bounds
2. [09_KEY_THEOREMS_AND_PROOFS.md](file:///home/harshal/Projects/BTP/repo_docs/09_KEY_THEOREMS_AND_PROOFS.md) — 2-approximation theorem and proof chain
3. [03_ALGORITHM_DEEP_DIVE.md](file:///home/harshal/Projects/BTP/repo_docs/03_ALGORITHM_DEEP_DIVE.md) — Combinatorial layers (Truemper & Blocking Flow)
4. [12_THESIS_AND_DELIVERABLES.md](file:///home/harshal/Projects/BTP/repo_docs/12_THESIS_AND_DELIVERABLES.md) — LaTeX mapping and thesis contributions

### 💻 For Code Developers & Maintainers
1. [02_ARCHITECTURE.md](file:///home/harshal/Projects/BTP/repo_docs/02_ARCHITECTURE.md) — Pipeline flow and module boundaries
2. [04_DATA_STRUCTURES.md](file:///home/harshal/Projects/BTP/repo_docs/04_DATA_STRUCTURES.md) — State representations and Segment Tree
3. [11_FUNCTION_INDEX.md](file:///home/harshal/Projects/BTP/repo_docs/11_FUNCTION_INDEX.md) — Comprehensive API reference
4. [06_CONFIGURATION_REFERENCE.md](file:///home/harshal/Projects/BTP/repo_docs/06_CONFIGURATION_REFERENCE.md) — Configuration switches and flags
5. [07_TESTS_AND_VALIDATION.md](file:///home/harshal/Projects/BTP/repo_docs/07_TESTS_AND_VALIDATION.md) — Verification suite and test execution

### 📡 For LoRaWAN / Systems Researchers
1. [08_LORAWAN_DOMAIN.md](file:///home/harshal/Projects/BTP/repo_docs/08_LORAWAN_DOMAIN.md) — Physical PHY/MAC constraints, demodulator limits, ToA
2. [05_BASELINES_AND_EVALUATION.md](file:///home/harshal/Projects/BTP/repo_docs/05_BASELINES_AND_EVALUATION.md) — Comparison against EDF, SPT, and ILP
3. [10_OUTPUT_FORMAT.md](file:///home/harshal/Projects/BTP/repo_docs/10_OUTPUT_FORMAT.md) — Metric definitions and serialization schemas

---

## ⚡ Key Results & Guarantees at a Glance

* **Worst-case bound**: Makespan $C_{\max} \le 2 \cdot \text{OPT}$ unconditionally (Gairing–Monien–Woclaw 2007).
* **Energy-optimal allocation**: Phase 1.5 capacity-constrained downshifting achieves the lowest radio energy consumption (**6,493.8 mJ**, $27.8\text{ mJ/pkt}$), outperforming heuristics by 34.5%–45.1% while strictly preserving the $2 \cdot \text{OPT}$ bound.
* **Empirical performance**: Observed ratio of **1.6275× OPT** on the standard benchmark (18.6% margin below theoretical bound).
* **Demodulator capacity constraint**: Strictly respects the SX1301/1302 concurrent reception hardware limit ($\Omega(t) \le 8$ simultaneous packets network-wide) via a Segment Tree over active intervals.
* **Non-preemptive isolation**: Guarantees zero co-channel interference across all 48 logical machines ($8 \text{ channels} \times 6 \text{ Spreading Factors}$).

