import numpy as np
import warnings

# Precompute constant
SQRT2 = np.sqrt(2.0)
INV_3 = 1.0 / 3.0

def stumpff_c_s(z):
    """
    Vectorized Stumpff C and S functions computed together.
    Returns (c, s).
    """
    c = np.zeros_like(z, dtype=float)
    s = np.zeros_like(z, dtype=float)

    # Identify regimes
    pos = z > 0
    neg = z < 0
    zero = z == 0

    # Positive z
    if np.any(pos):
        z_pos = z[pos]
        sqrt_z = np.sqrt(z_pos)
        c[pos] = (1 - np.cos(sqrt_z)) / z_pos
        # Optimization: Use multiplication instead of power for speed
        s[pos] = (sqrt_z - np.sin(sqrt_z)) / (z_pos * sqrt_z)

    # Negative z
    if np.any(neg):
        z_neg = z[neg]
        sqrt_mz = np.sqrt(-z_neg)
        c[neg] = (np.cosh(sqrt_mz) - 1) / (-z_neg)
        # Optimization: Use multiplication (z_neg is negative, so -z_neg is positive squared mag)
        s[neg] = (np.sinh(sqrt_mz) - sqrt_mz) / (-z_neg * sqrt_mz)

    # Zero case
    if np.any(zero):
        c[zero] = 0.5
        s[zero] = 1.0/6.0

    return c, s

# Retain original functions for compatibility if needed, but implementation uses the combined one
def stumpff_c(z):
    return stumpff_c_s(z)[0]

def stumpff_s(z):
    return stumpff_c_s(z)[1]

def _compute_term_ratio(z):
    """
    Computes auxiliary variables for Lambert solver using half-angle formulas.
    This avoids expensive Stumpff function calls and intermediate square roots.

    Returns:
        term: -sqrt(2) * cos(sqrt(z)/2)  [for z>0]
              -sqrt(2) * cosh(sqrt(-z)/2) [for z<0]
              Used to compute y = r_sum + A * term.

        ratio: S(z) / C(z)^1.5
               Used to compute t.
    """
    term = np.zeros_like(z, dtype=float)
    ratio = np.zeros_like(z, dtype=float)

    pos = z > 0
    neg = z < 0

    # 1. Compute Term (Stable everywhere using standard functions)
    if np.any(pos):
        zp = z[pos]
        # For z=0, sqrt(0)=0, cos(0)=1. term = -sqrt(2). Correct.
        term[pos] = -SQRT2 * np.cos(np.sqrt(zp) * 0.5)

    if np.any(neg):
        zn = -z[neg]
        term[neg] = -SQRT2 * np.cosh(np.sqrt(zn) * 0.5)

    # Zero case for term (cos(0) = 1)
    zero = z == 0
    if np.any(zero):
        term[zero] = -SQRT2
        # Ratio for zero is handled in series or separately, but series covers it.
        # However, for exact zero, direct assignment is faster/cleaner.
        ratio[zero] = SQRT2 * INV_3

    # 2. Compute Ratio
    # Regime split for stability: Use series for small z to avoid cancellation
    # Threshold 0.1 is standard, but 0.2 covers more ground safely given degree 5 series.
    is_small = (np.abs(z) < 0.1) & (~zero)
    is_large = ~is_small & ~zero

    # Large z: Use half-angle explicit formulas
    large_pos = is_large & pos
    if np.any(large_pos):
        zp = z[large_pos]
        sz = np.sqrt(zp)
        sz_2 = sz * 0.5
        sa = np.sin(sz_2)
        ca = np.cos(sz_2)
        sa3 = sa * sa * sa
        ratio[large_pos] = (sz - 2 * sa * ca) / (2 * SQRT2 * sa3)

    large_neg = is_large & neg
    if np.any(large_neg):
        zn = -z[large_neg]
        sz = np.sqrt(zn)
        sz_2 = sz * 0.5
        sa = np.sinh(sz_2)
        ca = np.cosh(sz_2)
        sa3 = sa * sa * sa
        ratio[large_neg] = (2 * sa * ca - sz) / (2 * SQRT2 * sa3)

    # Small z: Use Single Polynomial Series for Ratio
    # Derived from S(z)/C(z)^1.5 Taylor expansions.
    # Ratio(z) = sqrt(2)/3 * (1 + 3/40 z + 17/4480 z^2 + ...)
    # Coefficients for Ratio / (sqrt(2)/3):
    # c0 = 1.0
    # c1 = 3/40 = 0.075
    # c2 = 17/4480 ~ 0.0037946
    # c3 ~ 1.618e-4
    # c4 ~ 6.24e-6
    # c5 ~ 2.25e-7
    if np.any(is_small):
        zs = z[is_small]

        # Horner's method for Ratio / (sqrt(2)/3)
        # Using computed coefficients for z (not -z, coefficients include signs appropriately)
        # The series was derived for Ratio(z).
        # Coefficients: [1.0, 0.075, 0.00379464, 1.6183e-4, 6.2409e-6, 2.2477e-7]

        val = 2.24778741e-07
        val = val * zs + 6.24091078e-06
        val = val * zs + 1.61830357e-04
        val = val * zs + 3.79464286e-03
        val = val * zs + 7.50000000e-02
        val = val * zs + 1.0

        ratio[is_small] = (SQRT2 * INV_3) * val

    return term, ratio

def _compute_t_internal(z_vals, r_sum, A, inv_sqrt_mu):
    """
    Internal helper to compute Time of Flight from z.
    Separated to support calculating on active subsets.
    """
    # Optimization: Use half-angle formulas to avoid stumpff_c_s and explicit sqrt(C)
    term, ratio = _compute_term_ratio(z_vals)

    y_val = r_sum + A * term

    # Valid check
    valid = y_val > 0

    t_val = np.full_like(z_vals, np.nan)

    if np.any(valid):
        y_v = y_val[valid]
        rat_v = ratio[valid]

        # For subset calculation, we need to slice A for valid entries too
        if A.shape != ():  # Check if A is an array
            # If A matches z_vals shape (broadcasted), we slice it.
            # If A is scalar or (1,1), we don't.
            # But here z_vals is likely a subset (active), so r_sum and A passed in
            # must already be subsets matching z_vals shape.
            # So we just slice with [valid].
            A_v = A[valid]
        else:
            A_v = A

        # t = sqrt(y) * (y * ratio + A) / sqrt(mu)
        sqrt_y = np.sqrt(y_v)
        t_val[valid] = sqrt_y * (y_v * rat_v + A_v) * inv_sqrt_mu

    return t_val

def lambert(r1_vec, r2_vec, dt, mu, tm=1, tol=1e-5, max_iter=50):
    """
    Solves Lambert's problem using Universal Variables (Vectorized).
    
    Args:
        r1_vec (np.array): Initial position vector (..., 3).
        r2_vec (np.array): Final position vector (..., 3).
        dt (np.array or float): Time of flight (seconds).
        mu (float): Gravitational parameter.
        tm (int): Transfer mode (+1 short way, -1 long way).
        tol (float): Tolerance for convergence.
        max_iter (int): Maximum iterations.
                  
    Returns:
        v1_vec (np.array): Initial velocity vector (..., 3).
        v2_vec (np.array): Final velocity vector (..., 3).
    """
    # Ensure inputs are arrays for broadcasting
    r1_vec = np.asarray(r1_vec)
    r2_vec = np.asarray(r2_vec)
    dt = np.asarray(dt)
    
    # Handle scalar inputs (single case) by promoting to 1-element arrays
    was_scalar = False
    if r1_vec.ndim == 1:
        r1_vec = r1_vec[np.newaxis, :]
        r2_vec = r2_vec[np.newaxis, :]
        dt = np.atleast_1d(dt)
        was_scalar = True
    
    # Magnitudes
    r1 = np.linalg.norm(r1_vec, axis=-1)
    r2 = np.linalg.norm(r2_vec, axis=-1)
    
    dot_prod = np.sum(r1_vec * r2_vec, axis=-1)
    
    # Cos dnu
    cos_dnu = dot_prod / (r1 * r2)
    cos_dnu = np.clip(cos_dnu, -1.0, 1.0)
    
    # Calculate A
    A = tm * np.sqrt(r1 * r2 * (1 + cos_dnu))
    
    # Precompute r_sum as it is constant in the loop
    r_sum = r1 + r2

    # Optimization: Precompute inverse sqrt(mu) to use multiplication instead of division
    inv_sqrt_mu = 1.0 / np.sqrt(mu)

    # Solver state
    # We solve for z.
    # Initial guesses
    z0 = np.zeros_like(dt, dtype=float)
    z1 = np.ones_like(dt, dtype=float) # Guess z=1
    
    # Initialize Secant
    # First iterations on full array
    t0 = _compute_t_internal(z0, r_sum, A, inv_sqrt_mu)
    t1 = _compute_t_internal(z1, r_sum, A, inv_sqrt_mu)

    # Convergence mask (initially all False)
    converged = np.zeros_like(dt, dtype=bool)

    for _ in range(max_iter):
        diff = t1 - dt

        # Check convergence
        not_nan = ~np.isnan(diff)
        just_converged = not_nan & (np.abs(diff) < tol)
        converged |= just_converged

        # Active set: Not converged
        active = ~converged

        if not np.any(active):
            break

        # Subsetting for active calculations
        z0_a = z0[active]
        z1_a = z1[active]
        t0_a = t0[active]
        t1_a = t1[active]
        diff_a = diff[active]

        denom_sec = t1_a - t0_a
        denom_sec[denom_sec == 0] = 1e-12
        
        dz = -diff_a * (z1_a - z0_a) / denom_sec
        z_new_a = z1_a + dz

        # Update z1 for active
        z0[active] = z1_a
        t0[active] = t1_a
        z1[active] = z_new_a
        
        # Compute t1 only for active
        # Slice static arrays to match active subset
        r_sum_a = r_sum[active]
        A_a = A[active]
        
        t_val_a = _compute_t_internal(z_new_a, r_sum_a, A_a, inv_sqrt_mu)
        t1[active] = t_val_a
        
        # Recovery for NaNs in active set
        nan_mask_sub = np.isnan(t_val_a)
        if np.any(nan_mask_sub):
            # If t1 becomes NaN, it means the guess z_new_a yielded invalid y (< 0).
            # Standard recovery is to bisect or reset.
            # Here we reset z1 to z0 (which was the previous valid step).
            # z0[active] holds the previous z1.
            # We must identify which indices in the full array correspond to these NaNs.
            # Or simpler: we just update the 'z1' array values at these active+nan positions.

            # Identify elements in 'z_new_a' that are bad
            z0_rec = z0_a[nan_mask_sub] # Previous valid values

            # We want to reset z1 to z0 for these bad points.
            # Since we just updated z1[active] = z_new_a, we need to overwrite the bad ones.
            # But we can't easily index into z1[active][nan_mask_sub] assignment-wise in one go
            # if we didn't keep the index mapping.
            # Actually we can:
            # We need to write into z1.
            # The indices in z1 are 'active' masked by 'nan_mask_sub'.
            # It's tricky to construct a boolean mask for the full array from nested masks.
            # Full mask = active AND (t1 is nan)

            # Since we updated t1[active], we can check t1 again?
            # t1 has been updated. The NaNs are there.
            full_nan_mask = active & np.isnan(t1)

            if np.any(full_nan_mask):
                # Reset z1 to z0 for these points
                z1[full_nan_mask] = z0[full_nan_mask]

                # We also need to recompute t1 for these points (which is t0)
                t1[full_nan_mask] = t0[full_nan_mask]

    # Final z is z1
    z = z1

    # Compute v vectors
    term, _ = _compute_term_ratio(z)
    y = r1 + r2 + A * term
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        f = 1 - y / r1
        g = A * np.sqrt(y / mu)
        g_dot = 1 - y / r2

        # Broadcasting g to (..., 1)
        g_exp = np.expand_dims(g, axis=-1)
        f_exp = np.expand_dims(f, axis=-1)
        g_dot_exp = np.expand_dims(g_dot, axis=-1)

        v1_vec = (r2_vec - f_exp * r1_vec) / g_exp
        v2_vec = (g_dot_exp * r2_vec - r1_vec) / g_exp
    
    if was_scalar:
        return v1_vec[0], v2_vec[0]
    else:
        return v1_vec, v2_vec
