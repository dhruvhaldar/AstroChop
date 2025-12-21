import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from lambert import lambert
from ephemeris import get_ephemeris, MU_SUN

def jd_from_date(date):
    """
    Converts datetime object to Julian Date.
    """
    # Simple conversion
    # JD = 367*Y - INT(7*(Y+INT((M+9)/12))/4) + INT(275*M/9) + D + 1721013.5 + UT/24
    # Or just use astropy if available, but we don't have it.
    # Use standard algorithm.
    
    Y = date.year
    M = date.month
    D = date.day
    h = date.hour + date.minute/60 + date.second/3600
    
    JDN = (1461 * (Y + 4800 + (M - 14)//12)) // 4 +\
          (367 * (M - 2 - 12 * ((M - 14)//12))) // 12 -\
          (3 * ((Y + 4900 + (M - 14)//12) // 100)) // 4 +\
          D - 32075
          
    return JDN + (h - 12) / 24.0

def date_from_jd(jd):
    """
    Converts Julian Date to datetime object.
    """
    # Inverse algorithm
    # Adapted from standard sources
    Z = int(jd + 0.5)
    F = jd + 0.5 - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    
    day = B - D - int(30.6001 * E) + F
    if E < 14:
        month = E - 1
    else:
        month = E - 13
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
        
    # Convert fraction of day to h:m:s
    d_frac = day - int(day)
    h_total = d_frac * 24
    h = int(h_total)
    m_total = (h_total - h) * 60
    m = int(m_total)
    s = (m_total - m) * 60
    
    return datetime(year, month, int(day), h, m, int(s))

def generate_porkchop(launch_dates, arrival_dates, body1='earth', body2='mars'):
    """
    Generates data for porkchop plot.
    
    Args:
        launch_dates (list of datetime): Possible launch dates.
        arrival_dates (list of datetime): Possible arrival dates.
        body1 (str): Departure body.
        body2 (str): Arrival body.
        
    Returns:
        X (np.array): Launch dates (JDs).
        Y (np.array): Arrival dates (JDs).
        C3 (np.array): Characteristic energy (km^2/s^2).
        TOF (np.array): Time of Flight (days).
    """
    n_launch = len(launch_dates)
    n_arrival = len(arrival_dates)
    
    C3 = np.zeros((n_arrival, n_launch))
    Vinf_arr = np.zeros((n_arrival, n_launch))
    TOF = np.zeros((n_arrival, n_launch))
    
    # Pre-calculate positions to save time
    # This optimization avoids re-calculating JDs and ephemeris inside the nested loop
    
    # 1. Pre-calculate JDs
    launch_jds = [jd_from_date(d) for d in launch_dates]
    arrival_jds = [jd_from_date(d) for d in arrival_dates]

    # 2. Pre-calculate ephemeris states (r, v)
    # List of (r, v) tuples
    launch_states = [get_ephemeris(body1, jd) for jd in launch_jds]
    arrival_states = [get_ephemeris(body2, jd) for jd in arrival_jds]

    for i, _ in enumerate(launch_dates):
        jd1 = launch_jds[i]
        r1, v1_body = launch_states[i]
        
        for j, _ in enumerate(arrival_dates):
            jd2 = arrival_jds[j]
            
            dt_days = jd2 - jd1
            if dt_days <= 0:
                C3[j, i] = np.nan
                TOF[j, i] = np.nan
                continue
            
            # Use pre-calculated state
            r2, v2_body = arrival_states[j]
            
            dt_sec = dt_days * 86400
            
            # Solve Lambert
            try:
                v1_trans, v2_trans = lambert(r1, r2, dt_sec, MU_SUN)
                
                # C3 = v_inf_dep^2 = |v_transfer - v_body|^2
                v_inf_dep = np.linalg.norm(v1_trans - v1_body)
                c3_val = v_inf_dep**2
                
                # V_inf_arr = |v_body - v_transfer|
                v_inf_arr = np.linalg.norm(v2_trans - v2_body)
                
                C3[j, i] = c3_val
                Vinf_arr[j, i] = v_inf_arr
                TOF[j, i] = dt_days
                
            except Exception:
                C3[j, i] = np.nan
                TOF[j, i] = np.nan

    return launch_dates, arrival_dates, C3, Vinf_arr, TOF

def plot_porkchop(launch_dates, arrival_dates, C3, TOF, filename='astrochop.png'):
    X, Y = np.meshgrid([jd_from_date(d) for d in launch_dates], [jd_from_date(d) for d in arrival_dates])
    
    # Convert dates for axis labels
    x_dates = launch_dates
    y_dates = arrival_dates
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Contour levels for C3
    levels = np.linspace(0, 50, 26) # 0 to 50 km^2/s^2
    
    # Plot C3 contours
    CS = ax.contour(X, Y, C3, levels=levels, colors='blue', linewidths=0.5)
    ax.clabel(CS, inline=1, fontsize=8, fmt='%1.1f')
    
    # Plot TOF contours
    # levels_tof = np.linspace(100, 500, 9)
    # CS2 = ax.contour(X, Y, TOF, levels=levels_tof, colors='red', linewidths=0.5, linestyles='dashed')
    # ax.clabel(CS2, inline=1, fontsize=8, fmt='%1.0f')
    
    # Format axes with dates
    # We can use matplotlib.dates but let's stick to simple labels for now or raw JDs?
    # Better to use matplotlib dates.
    
    import matplotlib.dates as mdates
    
    # We need to replot using date numbers
    X_dates = mdates.date2num(np.meshgrid(launch_dates, arrival_dates)[0])
    Y_dates = mdates.date2num(np.meshgrid(launch_dates, arrival_dates)[1])
    
    ax.clear()
    CS = ax.contour(X_dates, Y_dates, C3, levels=levels, colors='blue')
    ax.clabel(CS, inline=1, fontsize=8, fmt='C3=%1.1f')
    
    # Plot TOF
    levels_tof = range(100, 1000, 50)
    CS2 = ax.contour(X_dates, Y_dates, TOF, levels=levels_tof, colors='red', linestyles='dashed', linewidths=0.5)
    ax.clabel(CS2, inline=1, fontsize=8, fmt='%d d')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    fig.autofmt_xdate()
    
    ax.set_title('Earth-Mars Porkchop Plot')
    ax.set_xlabel('Launch Date')
    ax.set_ylabel('Arrival Date')
    
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
