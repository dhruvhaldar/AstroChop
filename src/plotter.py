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
    
    # 1. Prepare vectors for launch and arrival
    launch_jds = np.array([jd_from_date(d) for d in launch_dates])
    arrival_jds = np.array([jd_from_date(d) for d in arrival_dates])
    
    # Get ephemeris for all dates
    # We assume get_ephemeris is fast enough or we loop.
    # Ephemeris calls are usually fast (analytical).

    r1_list = []
    v1_body_list = []
    for jd in launch_jds:
        r, v = get_ephemeris(body1, jd)
        r1_list.append(r)
        v1_body_list.append(v)

    r2_list = []
    v2_body_list = []
    for jd in arrival_jds:
        r, v = get_ephemeris(body2, jd)
        r2_list.append(r)
        v2_body_list.append(v)

    # Convert to arrays: (N, 3)
    R1 = np.array(r1_list)
    V1_body = np.array(v1_body_list)

    R2 = np.array(r2_list)
    V2_body = np.array(v2_body_list)

    # 2. Broadcast to (N_arrival, N_launch, 3)
    # R1: (1, N_l, 3)
    # R2: (N_a, 1, 3)
    R1_broad = R1[np.newaxis, :, :]
    R2_broad = R2[:, np.newaxis, :]

    V1_body_broad = V1_body[np.newaxis, :, :]
    V2_body_broad = V2_body[:, np.newaxis, :]

    # Calculate DT: (N_a, N_l)
    DT_days = arrival_jds[:, np.newaxis] - launch_jds[np.newaxis, :]
    DT_sec = DT_days * 86400

    # 3. Filter invalid DT (DT <= 0)
    # We can mask them or just let lambert handle negative DT (it won't converge or return garbage)
    # But usually we want to pass valid DT to lambert.
    # We can pass all, and then post-filter.
    # Our vectorized lambert expects positive DT.

    valid_mask = DT_days > 0

    # Initialize results
    C3 = np.full((n_arrival, n_launch), np.nan)
    Vinf_arr = np.full((n_arrival, n_launch), np.nan)
    TOF = DT_days

    # If no valid dates, return early
    if not np.any(valid_mask):
        return launch_dates, arrival_dates, C3, Vinf_arr, TOF

    # 4. Call Vectorized Lambert
    # We call it with full arrays. The solver handles element-wise ops.
    # Where DT <= 0, the solver might produce NaNs or errors.
    # To be safe, we can clip DT to something positive small number, then mask result.
    DT_safe = DT_sec.copy()
    DT_safe[~valid_mask] = 1.0 # Dummy positive value

    v1_trans, v2_trans = lambert(R1_broad, R2_broad, DT_safe, MU_SUN)

    # 5. Compute C3 and Vinf
    # v_inf_dep = |v1_trans - v1_body|
    diff_v1 = v1_trans - V1_body_broad
    v_inf_dep_sq = np.sum(diff_v1**2, axis=-1) # Squared norm

    # v_inf_arr = |v2_body - v2_trans|
    diff_v2 = V2_body_broad - v2_trans
    v_inf_arr = np.sqrt(np.sum(diff_v2**2, axis=-1))

    # Apply mask
    C3 = np.where(valid_mask, v_inf_dep_sq, np.nan)
    Vinf_arr = np.where(valid_mask, v_inf_arr, np.nan)
    TOF = np.where(valid_mask, DT_days, np.nan)
    
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
    
    import matplotlib.dates as mdates
    
    # We need to replot using date numbers
    X_dates = mdates.date2num(np.meshgrid(launch_dates, arrival_dates)[0])
    Y_dates = mdates.date2num(np.meshgrid(launch_dates, arrival_dates)[1])
    
    ax.clear()
    
    # Filled contours for C3
    CSF = ax.contourf(X_dates, Y_dates, C3, levels=levels, cmap='viridis')
    cbar = fig.colorbar(CSF, ax=ax)
    cbar.set_label('$C_3$ (km$^2$/s$^2$)')

    # Line contours for C3 (thin, white/dark for contrast)
    CS = ax.contour(X_dates, Y_dates, C3, levels=levels, colors='white', linewidths=0.5, alpha=0.5)
    ax.clabel(CS, inline=1, fontsize=8, fmt='%1.1f')

    # Plot TOF (keep dashed red, maybe thicker or different color if needed)
    levels_tof = range(100, 1000, 50)
    CS2 = ax.contour(X_dates, Y_dates, TOF, levels=levels_tof, colors='red', linestyles='dashed', linewidths=1.0)
    ax.clabel(CS2, inline=1, fontsize=8, fmt='%d d')

    # Grid
    ax.grid(True, linestyle=':', alpha=0.6)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    fig.autofmt_xdate()
    
    ax.set_title('Earth-Mars Porkchop Plot')
    ax.set_xlabel('Launch Date')
    ax.set_ylabel('Arrival Date')
    
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
