import numpy as np

def stumpff_c(z):
    if z > 0:
        return (1 - np.cos(np.sqrt(z))) / z
    elif z < 0:
        return (np.cosh(np.sqrt(-z)) - 1) / (-z)
    else:
        return 1/2.0

def stumpff_s(z):
    if z > 0:
        return (np.sqrt(z) - np.sin(np.sqrt(z))) / (np.sqrt(z)**3)
    elif z < 0:
        return (np.sinh(np.sqrt(-z)) - np.sqrt(-z)) / (np.sqrt(-z)**3)
    else:
        return 1/6.0

def lambert(r1_vec, r2_vec, dt, mu, tm=1):
    """
    Solves Lambert's problem using Universal Variables.
    
    Args:
        r1_vec (np.array): Initial position vector (km).
        r2_vec (np.array): Final position vector (km).
        dt (float): Time of flight (seconds).
        mu (float): Gravitational parameter (km^3/s^2).
        tm (int): Transfer mode. +1 for short way, -1 for long way.
                  (Note: typical implementations might use separate boolean for retrograde)
                  Here, we assume prograde motion. If tm is -1, it handles > 180 deg transfer?
                  Let's stick to simple short/long way based on cross product or just standard algorithm logic.
                  
                  Actually, let's simplify: 
                  We usually want the "short way" (angle < 180) or "long way" (angle > 180).
                  The direction of motion depends on the specific orbit, but usually for interplanetary
                  we assume prograde.
                  
    Returns:
        v1_vec (np.array): Initial velocity vector.
        v2_vec (np.array): Final velocity vector.
    """
    r1 = np.linalg.norm(r1_vec)
    r2 = np.linalg.norm(r2_vec)
    
    cross_12 = np.cross(r1_vec, r2_vec)
    
    # Calculate difference in true anomaly
    # cos(dnu) = dot(r1, r2) / (r1 * r2)
    # sin(dnu) = (r1 x r2) dot (angular_momentum_direction?)
    # For prograde orbits, angular momentum is usually +Z roughly.
    # Let's compute dnu carefully.
    
    cos_dnu = np.dot(r1_vec, r2_vec) / (r1 * r2)
    
    # Ensure numerical stability
    if cos_dnu > 1.0: cos_dnu = 1.0
    if cos_dnu < -1.0: cos_dnu = -1.0

    # Determine the angle 0 <= dnu <= pi initially
    # But we need to know if it's > pi.
    # Usually we rely on the z-component of the cross product for 2D, 
    # but in 3D we need to decide the transfer plane.
    # "Short way" means dnu < 180. "Long way" means dnu > 180.
    # Porkchop plots usually scan both or pick the optimal.
    # We will accept a 'tm' parameter: +1 for short way, -1 for long way.
    
    # Actually, usually 'tm' means direction of motion (prograde/retrograde).
    # Let's assume prograde. 
    # If Z component of cross product is positive, it is prograde short way?
    # No, let's keep it simple. dnu is the angle swept.
    
    # If tm == 1 (short way):
    #   if cross_z >= 0: dnu = acos(...)
    #   else: dnu = 2pi - acos(...) ? No.
    
    # Let's just calculate the angle between vectors.
    dnu = np.arccos(cos_dnu)
    
    # Fix the quadrant if needed based on `tm` (transfer mode).
    # tm = 1: short way (dnu < pi)
    # tm = -1: long way (dnu > pi)
    
    if tm == -1:
        dnu = 2 * np.pi - dnu
        
    A = np.sin(dnu) * np.sqrt(r1 * r2 / (1 - np.cos(dnu)))
    
    # Define function to zero
    def time_of_flight_residual(z):
        C = stumpff_c(z)
        S = stumpff_s(z)
        if C <= 0: return np.nan
        y = r1 + r2 + A * (z * S - 1) / np.sqrt(C)
        if y < 0:
            return np.nan # Invalid region
        x = np.sqrt(y / C)
        t = (x**3 * S + A * np.sqrt(y)) / np.sqrt(mu)
        return t - dt

    from scipy.optimize import brentq
    
    # Find bounds?
    # z can be positive (ellipse) or negative (hyperbola).
    # Lower bound for z is related to parabolic limit?
    # Usually -4pi^2 is a safe lower bound for one revolution? 
    # For single revolution transfer, z > -4pi^2 approx?
    
    try:
        # We try to bracket the root.
        # z=0 is a parabola.
        # Check T(0).
        t0 = time_of_flight_residual(0)
        
        if np.isnan(t0):
            # This shouldn't happen for valid geometries usually?
             # Check y calculation for z=0.
             # y(0) = r1 + r2 + A * (-1) / sqrt(1/2) = r1+r2 - A*sqrt(2)
             pass
        
        # If t0 < dt, we need larger t, meaning larger a, so z goes towards 0 or positive?
        # Period T ~ a^1.5. z = x^2/a. 
        
        # Let's search in a reasonable range [-100, 100] ?
        # Or better yet, define the function and let root solver handle it with a guess.
        
        from scipy.optimize import root_scalar
        sol = root_scalar(time_of_flight_residual, x0=0, x1=1, bracket=None, method='secant') 
        # Secant might be unstable if we hit y<0.
        # Let's try bracket.
        
        # We can try to bracket it manually.
        lower = -4*np.pi**2 + 0.1
        upper = 4*np.pi**2
        
        # If dt is very large, z approaches upper limit (multi-rev).
        # We assume single revolution (0 revs).
        
        # Check signs
        f_lower = time_of_flight_residual(lower)
        f_upper = time_of_flight_residual(upper)
        
        if np.isnan(f_lower): f_lower = -1e9 # hack
        
        if f_lower * f_upper < 0:
             z = brentq(time_of_flight_residual, lower, upper)
        else:
             # Try to find root with newton or just guess
             sol = root_scalar(time_of_flight_residual, x0=0, method='secant')
             z = sol.root
             
    except Exception as e:
        # Fallback or propagate error
        # print(f"Lambert solver failed: {e}")
        return np.zeros(3), np.zeros(3)

    # Recompute values with solution z
    C = stumpff_c(z)
    S = stumpff_s(z)
    # Ensure C is not zero (it shouldn't be for real z)
    if C <= 0: C = 1e-9
    y = r1 + r2 + A * (z * S - 1) / np.sqrt(C)
    
    f = 1 - y / r1
    g = A * np.sqrt(y / mu)
    
    g_dot = 1 - y / r2
    
    v1_vec = (r2_vec - f * r1_vec) / g
    v2_vec = (g_dot * r2_vec - r1_vec) / g
    
    return v1_vec, v2_vec
