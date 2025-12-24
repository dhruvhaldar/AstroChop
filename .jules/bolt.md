## 2024-05-23 - Vectorized Porkchop Generation
**Learning:** Python loops are the enemy of performance in numerical computing. Vectorizing the nested loops in `generate_porkchop` reduced execution time by ~99% (from ~3.0s to ~0.03s for a 50x50 grid).
**Action:** When working with grid-based calculations (like porkchop plots), always look for opportunities to broadcast arrays using NumPy instead of iterating. Ensure the underlying solver (like `lambert`) supports array inputs.
