## 2024-05-23 - Vectorized Porkchop Generation
**Learning:** Python loops are the enemy of performance in numerical computing. Vectorizing the nested loops in `generate_porkchop` reduced execution time by ~99% (from ~3.0s to ~0.03s for a 50x50 grid).
**Action:** When working with grid-based calculations (like porkchop plots), always look for opportunities to broadcast arrays using NumPy instead of iterating. Ensure the underlying solver (like `lambert`) supports array inputs.

## 2024-05-24 - Loop Invariant Hoisting in Lambert Solver
**Learning:** Even in vectorized code, repeated array operations inside a loop (like `r1 + r2`) add up. Hoisting `r_sum = r1 + r2` out of the Secant loop in `lambert.py` saved ~1 million float additions/allocations per iteration on a 1000x1000 grid.
**Action:** Identify variables in solver loops that depend only on inputs (not the iteration variable) and precompute them. Use `benchmark_lambert.py` to verify.

## 2024-05-25 - Trigonometric Reduction in Lambert Solver
**Learning:** In the Lambert Universal Variables method, computing Stumpff functions `C(z)` and `S(z)` involves redundant trigonometric calls and square roots. By rewriting the auxiliary variables `y` and `t` using half-angle formulas (e.g., `cos(sqrt(z)/2)`), we can avoid computing `C` and `S` entirely in the hot loop, reducing transcendental function calls by ~30% per iteration.
**Action:** When implementing well-known algorithms, look for algebraic simplifications that avoid intermediate variables. Specifically, substituting `stumpff_c_s` with a specialized `_compute_term_ratio` reduced execution time by ~12% (from ~9.4s to ~8.2s).

## 2024-05-26 - Polynomial Series for Small Angles
**Learning:** In the Lambert solver's `small z` regime, branching to handle positive/negative cases for `sqrt` and `trig` functions was a hidden cost. Replacing `cos(sqrt(z)/2)` and `cosh(sqrt(-z)/2)` with a single polynomial series (valid for all real `z`) eliminated both the expensive transcendental calls and the need for conditional masking in the hot path. This reduced `_compute_term_ratio` execution time by ~22%.
**Action:** For small arguments, Taylor series are often faster than built-in transcendental functions and handle sign changes naturally (e.g., `cos(x)` vs `cosh(ix)`), allowing for branch-free vectorization.
