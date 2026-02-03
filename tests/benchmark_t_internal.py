
import time
import numpy as np
import warnings

def compute_t_check(y_val, ratio, A, inv_sqrt_mu):
    # Original logic simulation
    valid = y_val > 0

    if valid.all():
        sqrt_y = np.sqrt(y_val)
        ratio *= y_val
        ratio += A
        ratio *= sqrt_y
        ratio *= inv_sqrt_mu
        return ratio
    else:
        # Slow path
        t_val = ratio # reuse
        t_val.fill(np.nan)

        if np.any(valid):
            rat_v = ratio[valid] # Copy? No, ratio was filled with nan?
            # Wait, the original code captures valid parts BEFORE filling nan if reusing buffer
            # In simulation, let's assume we passed a copy or handled it correctly
            # To be fair to the original code:

            # Original:
            # if np.any(valid):
            #     rat_v = ratio[valid] # Copy
            #     y_v = y_val[valid]
            # ...
            # if ratio_out is not None:
            #     t_val = ratio_out
            #     t_val.fill(np.nan)

            # But wait, if ratio_out IS ratio, then ratio[valid] must be done BEFORE t_val.fill(nan)
            # The original code does:
            # rat_v = ratio[valid]
            # y_v = y_val[valid]
            # ... t_val.fill(np.nan) ...
            # ... t_val[valid] = rat_v ...

            pass # Simulation is tricky without full buffers

            # Let's just implement the logic exactly
            rat_v = ratio[valid]
            y_v = y_val[valid]
            if np.ndim(A) > 0:
                A_v = A[valid]
            else:
                A_v = A

            t_val.fill(np.nan)

            sqrt_y = np.sqrt(y_v)
            rat_v *= y_v
            rat_v += A_v
            rat_v *= sqrt_y
            rat_v *= inv_sqrt_mu

            t_val[valid] = rat_v
            return t_val
        return t_val

def compute_t_nan(y_val, ratio, A, inv_sqrt_mu):
    # Proposed logic: Just do it, let NaNs happen
    # We need to suppress warnings
    with np.errstate(invalid='ignore'):
        sqrt_y = np.sqrt(y_val) # NaNs where y < 0

        ratio *= y_val
        ratio += A
        ratio *= sqrt_y # NaN * x = NaN
        ratio *= inv_sqrt_mu
        return ratio

def benchmark():
    N = 1_000_000
    # Case 1: All valid (Fast path vs NaN path)
    print(f"Benchmarking N={N}...")

    y_valid = np.random.uniform(0.1, 10.0, N)
    ratio_valid = np.random.uniform(0.1, 1.0, N)
    A = np.random.uniform(0.1, 1.0, N)
    mu = 1.0
    inv_sqrt_mu = 1.0/np.sqrt(mu)

    # Warmup
    _ = compute_t_nan(y_valid.copy(), ratio_valid.copy(), A, inv_sqrt_mu)

    start = time.time()
    for _ in range(10):
        compute_t_check(y_valid, ratio_valid.copy(), A, inv_sqrt_mu)
    end = time.time()
    print(f"All Valid - Check: {(end-start)/10:.6f} s")

    start = time.time()
    for _ in range(10):
        compute_t_nan(y_valid, ratio_valid.copy(), A, inv_sqrt_mu)
    end = time.time()
    print(f"All Valid - NaN:   {(end-start)/10:.6f} s")

    # Case 2: Mixed (50% invalid)
    y_mixed = np.random.uniform(-5.0, 5.0, N)
    ratio_mixed = np.random.uniform(0.1, 1.0, N)

    start = time.time()
    for _ in range(10):
        compute_t_check(y_mixed, ratio_mixed.copy(), A, inv_sqrt_mu)
    end = time.time()
    print(f"Mixed 50% - Check: {(end-start)/10:.6f} s")

    start = time.time()
    for _ in range(10):
        compute_t_nan(y_mixed, ratio_mixed.copy(), A, inv_sqrt_mu)
    end = time.time()
    print(f"Mixed 50% - NaN:   {(end-start)/10:.6f} s")

    # Case 3: Mostly Invalid (90% invalid) - should favor Check?
    y_bad = np.random.uniform(-9.0, 1.0, N)

    start = time.time()
    for _ in range(10):
        compute_t_check(y_bad, ratio_mixed.copy(), A, inv_sqrt_mu)
    end = time.time()
    print(f"Mixed 90% Bad - Check: {(end-start)/10:.6f} s")

    start = time.time()
    for _ in range(10):
        compute_t_nan(y_bad, ratio_mixed.copy(), A, inv_sqrt_mu)
    end = time.time()
    print(f"Mixed 90% Bad - NaN:   {(end-start)/10:.6f} s")

if __name__ == "__main__":
    benchmark()
