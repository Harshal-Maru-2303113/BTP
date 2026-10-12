"""
Combinatorial 2-Approximation for Unrelated Machine Makespan Minimisation.

Implements the algorithm of Gairing, Monien & Woclaw (2007):
  - Binary search over candidate makespan w
  - Unsplittable-Truemper outer loop (node potentials + shortest paths)
  - Unsplittable-Blocking-Flow inner loop (helpful paths)

References
----------
M. Gairing, B. Monien, A. Woclaw, "A faster combinatorial approximation
algorithm for scheduling unrelated parallel machines", TCS 2007.
"""
