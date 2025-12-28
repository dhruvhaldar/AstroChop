import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from lambert import lambert
from ephemeris import get_ephemeris, MU_SUN

MAX_GRID_SIZE = 25_000_000  # Protection against Memory Exhaustion (DoS)

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

def generate_porkchop(launch_dates, arrival_dates, body1='earth', body2='mars', verbose=False):
    """
    Generates data for porkchop plot.
    
    Args:
        launch_dates (list of datetime): Possible launch dates.
        arrival_dates (list of datetime): Possible arrival dates.
        body1 (str): Departure body.
        body2 (str): Arrival body.
        verbose (bool): Whether to show a progress bar.
        
    Returns:
        X (np.array): Launch dates (JDs).
        Y (np.array): Arrival dates (JDs).
        C3 (np.array): Characteristic energy (km^2/s^2).
        TOF (np.array): Time of Flight (days).
    """
    n_launch = len(launch_dates)
    n_arrival = len(arrival_dates)
    
    # Security Check: Prevent Memory Exhaustion / DoS
    if n_launch * n_arrival > MAX_GRID_SIZE:
        raise ValueError(f"Grid size {n_launch}x{n_arrival} ({n_launch*n_arrival}) exceeds maximum limit of {MAX_GRID_SIZE}.")

    C3 = np.zeros((n_arrival, n_launch))
    Vinf_arr = np.zeros((n_arrival, n_launch))
    TOF = np.zeros((n_arrival, n_launch))
    
    # Pre-calculate positions to save time?
    # Or just loop. Loop is easier to write.
    
    # Pre-calculate launch ephemeris
    launch_data = []
    for ld in launch_dates:
        jd1 = jd_from_date(ld)
        r1, v1_body = get_ephemeris(body1, jd1)
        launch_data.append((jd1, r1, v1_body))

    # Pre-calculate arrival ephemeris
    arrival_data = []
    for ad in arrival_dates:
        jd2 = jd_from_date(ad)
        r2, v2_body = get_ephemeris(body2, jd2)
        arrival_data.append((jd2, r2, v2_body))

    # Vectorized implementation
    if verbose:
        print("Calculating vectorized solution...")

    # Extract arrays from pre-calculated ephemeris
    # launch_data: list of (jd, r, v)
    jd1_arr = np.array([x[0] for x in launch_data])
    r1_arr = np.array([x[1] for x in launch_data])
    v1_arr = np.array([x[2] for x in launch_data])

    # arrival_data: list of (jd, r, v)
    jd2_arr = np.array([x[0] for x in arrival_data])
    r2_arr = np.array([x[1] for x in arrival_data])
    v2_arr = np.array([x[2] for x in arrival_data])

    # Broadcast shapes
    # launch (i): axis 1 -> (1, N)
    r1_grid = r1_arr[np.newaxis, :, :]  # (1, N, 3)
    v1_grid = v1_arr[np.newaxis, :, :]  # (1, N, 3)
    jd1_grid = jd1_arr[np.newaxis, :]   # (1, N)

    # arrival (j): axis 0 -> (M, 1)
    r2_grid = r2_arr[:, np.newaxis, :]  # (M, 1, 3)
    v2_grid = v2_arr[:, np.newaxis, :]  # (M, 1, 3)
    jd2_grid = jd2_arr[:, np.newaxis]   # (M, 1)

    # Time of Flight matrix (M, N)
    dt_days = jd2_grid - jd1_grid
    valid_mask = dt_days > 0

    # Prepare inputs for Lambert
    # We replace invalid dt with a dummy value (1.0) to avoid errors, then mask result
    dt_sec = dt_days * 86400.0
    dt_sec_safe = np.where(valid_mask, dt_sec, 1.0)

    # Solve Lambert (vectorized)
    # r1_grid (1, N, 3) broadcasts with r2_grid (M, 1, 3) -> (M, N, 3)
    # dt_sec_safe (M, N)
    # Note: lambert() handles broadcasting automatically
    v1_trans, v2_trans = lambert(r1_grid, r2_grid, dt_sec_safe, MU_SUN)

    # Calculate C3 and Vinf
    # v1_trans (M, N, 3) - v1_grid (1, N, 3) -> (M, N, 3)
    dv1 = v1_trans - v1_grid
    v_inf_dep = np.linalg.norm(dv1, axis=-1)
    C3 = v_inf_dep**2

    # v2_trans (M, N, 3) - v2_grid (M, 1, 3) -> (M, N, 3)
    dv2 = v2_trans - v2_grid
    Vinf_arr = np.linalg.norm(dv2, axis=-1)

    TOF = dt_days

    # Apply mask to invalidate cases where dt <= 0
    # Also mask any NaNs that might have come from Lambert (non-convergence)
    C3[~valid_mask] = np.nan
    Vinf_arr[~valid_mask] = np.nan
    TOF[~valid_mask] = np.nan

    return launch_dates, arrival_dates, C3, Vinf_arr, TOF

def plot_porkchop(launch_dates, arrival_dates, C3, TOF, filename='astrochop.png', optimal_transfer=None):
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

    # Plot optimal transfer marker if provided
    if optimal_transfer:
        opt_launch, opt_arrival = optimal_transfer
        # Convert to matplotlib date format
        opt_x = mdates.date2num(opt_launch)
        opt_y = mdates.date2num(opt_arrival)

        # Plot star marker: White with black outline for visibility on any background
        ax.plot(opt_x, opt_y, '*', markersize=15, markerfacecolor='white', markeredgecolor='black', label='Optimal Transfer', zorder=10)
        ax.legend(loc='upper right')

    # Grid
    ax.grid(True, linestyle=':', alpha=0.6)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    fig.autofmt_xdate()
    
    ax.set_title('Earth-Mars Porkchop Plot')
    ax.set_xlabel('Launch Date')
    ax.set_ylabel('Arrival Date')
    
    # Security: Prevent path traversal and enforce extension (similar to mesh_exporter.py)
    real_path = os.path.realpath(filename)
    cwd = os.path.realpath(os.getcwd())

    if os.path.commonpath([cwd, real_path]) != cwd:
        raise ValueError(f"Security Error: File path resolves to '{real_path}', which is outside the current working directory.")

    if not filename.lower().endswith('.png'):
        raise ValueError(f"Security Error: Filename '{filename}' must end with .png extension.")

    plt.savefig(filename)
