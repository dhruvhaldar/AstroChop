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

## 2025-02-23 - Vectorized Mesh Topology Generation
**Learning:** Generating mesh indices with nested Python loops is inherently $O(N \times M)$ and becomes a significant bottleneck for large grids (e.g., >1M points). By replacing loops with `np.meshgrid` and `np.stack` to generate index patterns, we reduced mesh generation time by ~72% (from ~5.3s to ~1.46s for 1M points).
**Action:** For structured grids, avoid iterating to build connectivity. Use `np.arange` and broadcasting to generate vertex indices and form topology arrays in a single pass.

## 2025-02-24 - Einsum for Norm Calculation
**Learning:** `np.linalg.norm` is convenient but can be slow for large arrays due to overhead and intermediate allocations. Replacing `np.linalg.norm(x)**2` with `np.einsum('...k,...k->...', x, x)` avoids `sqrt` and array allocation, yielding a ~4.8x speedup. Even for standard norm, `np.sqrt(np.einsum(...))` is ~2.6x faster than `np.linalg.norm`.
**Action:** In hot paths, especially for C3 (squared energy) calculations, use `np.einsum` to compute dot products and squared norms directly. Avoid `np.linalg.norm` inside critical loops or on massive grids.

## 2025-02-24 - Initialization Overhead in Hot Loops
**Learning:** In repeatedly called functions (like `_compute_term_ratio` inside `lambert` solver), even efficient operations like `np.zeros_like` add up. Replacing it with `np.empty_like` when full array population is guaranteed saved ~4% execution time.
**Action:** Use `np.empty_like` instead of `np.zeros_like` or `np.full_like` in performance-critical sections IF and ONLY IF you can prove every element is subsequently overwritten.

## 2025-02-24 - Buffer Reuse in Hot Loops
**Learning:** Allocating arrays inside a hot loop (like `term` and `ratio` in `lambert` solver) causes significant overhead. By preallocating buffers and passing them down, we reduced execution time by ~22%.
**Action:** Identify large temporary arrays allocated in loops. Preallocate them outside and pass slices (e.g., `buffer[:n]`) to inner functions. BEWARE of aliasing! When reusing a buffer for multiple purposes (like `ratio` reused for `t_val`), ensure you don't overwrite data you still need to read.

## 2025-02-24 - Boolean Mask Allocation
**Learning:** Even boolean mask operations like `is_small = ~(large_pos | large_neg)` create multiple temporary arrays. In hot loops, this adds up. Using in-place logic `np.logical_or(large_pos, large_neg, out=large_pos)` followed by `np.logical_not` reduced allocation overhead in the mixed regime.
**Action:** Reuse existing boolean buffers for logical operations when the original data is no longer needed.

## 2025-02-25 - Efficient Regime Detection
**Learning:** In the Lambert solver, detecting pure regimes using `np.min` and `np.max` required 2 full data passes, which became a bottleneck in the "Mixed" regime (iterations 3+). Replacing this with boolean mask generation (`z >= 0.1`) and boolean reductions (`.all()`, `.any()`) reduced data traversals in the mixed case while maintaining speed for pure cases. This yielded a ~5% speedup in the mixed regime.
**Action:** When categorizing large arrays into regimes, prioritize logic that minimizes total passes over the data, especially for the most common case. Allocating boolean masks (1 pass + overhead) can be cheaper than `min`/`max` (2 passes) if those masks are subsequently reused for calculation.
