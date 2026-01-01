## 2024-05-23 - Vectorized Porkchop Generation
**Learning:** Python loops are the enemy of performance in numerical computing. Vectorizing the nested loops in `generate_porkchop` reduced execution time by ~99% (from ~3.0s to ~0.03s for a 50x50 grid).
**Action:** When working with grid-based calculations (like porkchop plots), always look for opportunities to broadcast arrays using NumPy instead of iterating. Ensure the underlying solver (like `lambert`) supports array inputs.

## 2024-05-24 - Loop Invariant Hoisting in Lambert Solver
**Learning:** Even in vectorized code, repeated array operations inside a loop (like `r1 + r2`) add up. Hoisting `r_sum = r1 + r2` out of the Secant loop in `lambert.py` saved ~1 million float additions/allocations per iteration on a 1000x1000 grid.
**Action:** Identify variables in solver loops that depend only on inputs (not the iteration variable) and precompute them. Use `benchmark_lambert.py` to verify.
