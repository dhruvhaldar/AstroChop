import numpy as np
import warnings

def stumpff_c(z):
    """
    Vectorized Stumpff C function.
    """
    c = np.zeros_like(z, dtype=float)

    # Identify regimes
    pos = z > 0
    neg = z < 0
    zero = z == 0

    # Positive z
    if np.any(pos):
        sqrt_z = np.sqrt(z[pos])
        c[pos] = (1 - np.cos(sqrt_z)) / z[pos]

    # Negative z
    if np.any(neg):
        sqrt_mz = np.sqrt(-z[neg])
        c[neg] = (np.cosh(sqrt_mz) - 1) / (-z[neg])

    # Zero case
    c[zero] = 0.5

    return c

def stumpff_s(z):
    """
    Vectorized Stumpff S function.
    """
    s = np.zeros_like(z, dtype=float)

    pos = z > 0
    neg = z < 0
    zero = z == 0

    # Positive z
    if np.any(pos):
        sqrt_z = np.sqrt(z[pos])
        s[pos] = (sqrt_z - np.sin(sqrt_z)) / (sqrt_z**3)

    # Negative z
    if np.any(neg):
        sqrt_mz = np.sqrt(-z[neg])
        s[neg] = (np.sinh(sqrt_mz) - sqrt_mz) / (sqrt_mz**3)

    # Zero case
    s[zero] = 1.0/6.0

    return s

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
    
    dnu = np.arccos(cos_dnu)
    
    if tm == -1:
        dnu = 2 * np.pi - dnu
        
    # Calculate A
    denom = 1 - cos_dnu
    # Prevent division by zero if dnu=0 (identical points)
    # Using np.where to handle scalars/arrays safely
    denom = np.where(denom == 0, 1e-12, denom)
    
    A = np.sin(dnu) * np.sqrt(r1 * r2 / denom)
    
    # Solver state
    # We solve for z.
    # Initial guesses
    z0 = np.zeros_like(dt, dtype=float)
    z1 = np.ones_like(dt, dtype=float) # Guess z=1
    
    # Helper to compute Time from z
    def compute_t(z_vals):
        C = stumpff_c(z_vals)
        S = stumpff_s(z_vals)
        
        # y = r1 + r2 + A * (z*S - 1)/sqrt(C)
        
        sqrt_C = np.sqrt(C)
        term = (z_vals * S - 1) / sqrt_C
        y_val = r1 + r2 + A * term
        
        # Valid check
        valid = y_val > 0
        
        t_val = np.full_like(z_vals, np.nan)
        
        if np.any(valid):
            x_val = np.sqrt(y_val[valid] / C[valid])
            t_val[valid] = (x_val**3 * S[valid] + A[valid] * np.sqrt(y_val[valid])) / np.sqrt(mu)

        return t_val

    # Initialize Secant
    t0 = compute_t(z0)
    t1 = compute_t(z1)

    for _ in range(max_iter):
        diff = t1 - dt
        # Check convergence (ignoring NaNs)
        valid_diff = diff[~np.isnan(diff)]
        if len(valid_diff) > 0 and np.all(np.abs(valid_diff) < tol):
            # Also check that we don't have pending NaNs that could be resolved?
            # If everything valid is converged, we stop.
            break

        # Secant step
        denom_sec = t1 - t0
        # handle zero denom
        denom_sec = np.where(denom_sec == 0, 1e-12, denom_sec)
        
        dz = -diff * (z1 - z0) / denom_sec
        
        z_new = z1 + dz
        
        # Update
        z0 = z1.copy()
        t0 = t1.copy()
        z1 = z_new
        t1 = compute_t(z1)
        
        # If t1 became NaN (invalid y), try to recover?
        nan_mask = np.isnan(t1)
        if np.any(nan_mask):
             # Simple recovery: take midpoint of previous valid z0
             # We assume z0 was valid. If z0 was also nan, we can't help much.
             # Only update those that are NaN
             z1[nan_mask] = (z0[nan_mask] + z0[nan_mask])/2.0
             t1 = compute_t(z1)

    # Final z is z1
    z = z1

    # Compute v vectors
    C = stumpff_c(z)
    S = stumpff_s(z)
    sqrt_C = np.sqrt(C)
    y = r1 + r2 + A * (z * S - 1) / sqrt_C
    
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
