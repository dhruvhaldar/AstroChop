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
        jd (float): Julian Date.
        
    Returns:
        r_vec (np.array): Position vector (km).
        v_vec (np.array): Velocity vector (km/s).
    """
    
    # Orbital elements (approximate, J2000)
    # a (AU), e, i (deg), Omega (deg), w (deg), M0 (deg at J2000)
    # Mean motion n (deg/day)
    
    # AU to km
    AU = 149597870.7
    
    # Reference J2000
    J2000 = 2451545.0
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
    # P = [cos w cos O - sin w cos i sin O, -sin w cos O - cos w cos i sin O, sin i sin O] etc.
    # It's easier to rotate vectors
    
    def rot_z(angle, vec):
        c, s = np.cos(angle), np.sin(angle)
        x, y, z = vec
        return np.array([c*x - s*y, s*x + c*y, z])
        
    def rot_x(angle, vec):
        c, s = np.cos(angle), np.sin(angle)
        x, y, z = vec
        return np.array([x, c*y - s*z, s*y + c*z])

    # Perifocal vector
    # Handle both scalar and array cases
    if np.ndim(xv) == 0:
        r_peri = np.array([xv, yv, 0.0])
        v_peri = np.array([vxv, vyv, 0.0])
    else:
        zeros = np.zeros_like(xv)
        r_peri = np.stack([xv, yv, zeros]) # Shape (3, N)
        v_peri = np.stack([vxv, vyv, zeros])

    # Rotation Logic
    def R3(ang):
        c, s = np.cos(ang), np.sin(ang)
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        
    def R1(ang):
        c, s = np.cos(ang), np.sin(ang)
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        
    M_rot = R3(O) @ R1(i) @ R3(w) # (3, 3)
    
    # Apply rotation
    r_vec = M_rot @ r_peri
    v_vec = M_rot @ v_peri
    
    # If input was array (N,), return (N, 3) to be consistent
    if np.ndim(xv) != 0:
        r_vec = r_vec.T
        v_vec = v_vec.T

    return r_vec, v_vec

if __name__ == "__main__":
    # Test
    r, v = get_ephemeris('earth', 2451545.0)
    print("Earth J2000:", r, v)
