import numpy as np

# Gravitational Constant for Sun (km^3/s^2)
MU_SUN = 1.32712440018e11

def get_ephemeris(body_name, jd):
    """
    Returns position and velocity of a body at a given Julian Date.
    Simplified analytical model assuming circular/elliptical orbits 
    based on mean elements or just fixed elements.
    
    Args:
        body_name (str): 'earth', 'mars', etc.
        jd (float or np.array): Julian Date (scalar or array).
        
    Returns:
        r_vec (np.array): Position vector (km). Shape (3,) or (N, 3).
        v_vec (np.array): Velocity vector (km/s). Shape (3,) or (N, 3).
    """
    
    # Orbital elements (approximate, J2000)
    # a (AU), e, i (deg), Omega (deg), w (deg), M0 (deg at J2000)
    # Mean motion n (deg/day)
    
    # AU to km
    AU = 149597870.7
    
    # Reference J2000
    J2000 = 2451545.0

    # Ensure jd is handled as array internally if needed, or scalar if that's what it is
    # However, simple math operations work on both.
    d = jd - J2000
    
    elements = {}
    
    # Earth
    elements['earth'] = {
        'a': 1.00000011,
        'e': 0.01671022,
        'i': 0.00005,
        'O': -11.26064,
        'w': 102.94719,
        'L': 100.46435, # Mean Longitude L = M + w + O
        'n': 0.985609
    }
    
    # Mars
    elements['mars'] = {
        'a': 1.52366231,
        'e': 0.09341233,
        'i': 1.85061,
        'O': 49.57854,
        'w': 336.04084, # longitude of perihelion (w_bar = w + O) -> w = w_bar - O
        # Actually usually tabulated as L, w_bar, etc.
        # Let's use simple Keplerian elements.
        'M0': 19.412, # Mean anomaly at J2000?
        'n': 0.524039
    }
    
    if body_name == 'earth':
        # Use simple mean anomaly propagation
        el = elements['earth']
        M = np.radians(el['L'] - el['w'] - el['O'] + el['n'] * d)
        a = el['a'] * AU
        e = el['e']
        i = np.radians(el['i'])
        O = np.radians(el['O'])
        w = np.radians(el['w'])
    elif body_name == 'mars':
        el = elements['mars']
        # M = M0 + n * d
        M = np.radians(el['M0'] + el['n'] * d)
        a = el['a'] * AU
        e = el['e']
        i = np.radians(el['i'])
        O = np.radians(el['O'])
        # w is argument of periapsis
        # if w in dict is longitude of perihelion, w = w_bar - O
        w_bar = 336.04084 
        w = np.radians(w_bar - el['O'])
    else:
        raise ValueError(f"Unknown body: {body_name}")
        
    # Solve Kepler Equation M = E - e sin E
    E = M
    for _ in range(10):
        E = M + e * np.sin(E)
        
    # Perifocal coordinates
    # r = a(1 - e cos E)
    # x = a(cos E - e)
    # y = a sqrt(1-e^2) sin E
    
    r_mag = a * (1 - e * np.cos(E))
    xv = a * (np.cos(E) - e)
    yv = a * np.sqrt(1 - e**2) * np.sin(E)
    
    v_factor = np.sqrt(MU_SUN * a) / r_mag
    vxv = -v_factor * np.sin(E)
    vyv = v_factor * np.sqrt(1 - e**2) * np.cos(E)
    
    # Rotate to ECI (or ecliptic)
    
    # Perifocal vector construction
    # Handle array inputs for jd
    is_array = np.ndim(jd) > 0
    
    if is_array:
        zeros = np.zeros_like(xv)
        r_peri = np.stack([xv, yv, zeros]) # (3, N)
        v_peri = np.stack([vxv, vyv, zeros]) # (3, N)
    else:
        r_peri = np.array([xv, yv, 0.0]) # (3,)
        v_peri = np.array([vxv, vyv, 0.0]) # (3,)
    
    def R3(ang):
        c, s = np.cos(ang), np.sin(ang)
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        
    def R1(ang):
        c, s = np.cos(ang), np.sin(ang)
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        
    M_rot = R3(O) @ R1(i) @ R3(w)
    
    r_vec = M_rot @ r_peri
    v_vec = M_rot @ v_peri
    
    if is_array:
        # Transpose to (N, 3) to match vector convention
        return r_vec.T, v_vec.T
    else:
        return r_vec, v_vec

if __name__ == "__main__":
    # Test
    r, v = get_ephemeris('earth', 2451545.0)
    print("Earth J2000:", r, v)
