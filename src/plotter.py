import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from datetime import datetime, timedelta
from lambert import lambert
from ephemeris import get_ephemeris, MU_SUN

MAX_GRID_SIZE = 4_000_000  # Protection against Memory Exhaustion (DoS) - Reduced to ~600MB peak usage

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
        raise ValueError(f"Grid size {n_launch}x{n_arrival} ({n_launch*n_arrival:,}) exceeds maximum limit of {MAX_GRID_SIZE:,}. Try increasing the step size (dt) to reduce the grid resolution.")

    C3 = np.zeros((n_arrival, n_launch))
    Vinf_arr = np.zeros((n_arrival, n_launch))
    TOF = np.zeros((n_arrival, n_launch))
    
    # Pre-calculate positions to save time?
    # Or just loop. Loop is easier to write.
    
    # Vectorized implementation
    if verbose:
        print("Calculating vectorized solution...")

    # Vectorized ephemeris retrieval
    jd1_arr = np.array([jd_from_date(ld) for ld in launch_dates])
    r1_cols, v1_cols = get_ephemeris(body1, jd1_arr)
    # get_ephemeris returns (3, N), we want (N, 3)
    r1_arr = r1_cols.T
    v1_arr = v1_cols.T

    jd2_arr = np.array([jd_from_date(ad) for ad in arrival_dates])
    r2_cols, v2_cols = get_ephemeris(body2, jd2_arr)
    r2_arr = r2_cols.T
    v2_arr = v2_cols.T

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

def plot_porkchop(launch_dates, arrival_dates, C3, TOF, filename='astrochop.png', optimal_transfer=None, title='Earth-Mars Porkchop Plot'):
    X, Y = np.meshgrid([jd_from_date(d) for d in launch_dates], [jd_from_date(d) for d in arrival_dates])
    
    # Convert dates for axis labels
    x_dates = launch_dates
    y_dates = arrival_dates
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Contour levels for C3
    levels = np.linspace(0, 50, 26) # 0 to 50 km^2/s^2
    
    import matplotlib.dates as mdates
    
    # We need to replot using date numbers
    X_dates = mdates.date2num(np.meshgrid(launch_dates, arrival_dates)[0])
    Y_dates = mdates.date2num(np.meshgrid(launch_dates, arrival_dates)[1])
    
    # Filled contours for C3
    CSF = ax.contourf(X_dates, Y_dates, C3, levels=levels, cmap='viridis')
    cbar = fig.colorbar(CSF, ax=ax)
    cbar.set_label('$C_3$ (km$^2$/s$^2$)')

    # Line contours for C3 (thin, white/dark for contrast)
    CS = ax.contour(X_dates, Y_dates, C3, levels=levels, colors='white', linewidths=0.5, alpha=0.5)
    ax.clabel(CS, inline=1, fontsize=10, fmt='%1.1f')

    # Plot TOF (keep dashed red, maybe thicker or different color if needed)
    # Dynamic levels for TOF to support both fast (Mercury) and slow (Jupiter) missions
    # We use roughly 15-20 contour lines based on the data range
    valid_tof = TOF[~np.isnan(TOF)]
    if len(valid_tof) > 0:
        tof_min, tof_max = valid_tof.min(), valid_tof.max()
        # Ensure we have a valid range
        if tof_max - tof_min < 1:
             levels_tof = [tof_min]
        else:
             # Use MaxNLocator-like logic: ~15 levels
             levels_tof = np.linspace(tof_min, tof_max, 15).astype(int)
             # Unique and sorted to prevent warnings
             levels_tof = np.unique(levels_tof)
    else:
        levels_tof = range(100, 1000, 50) # Fallback

    CS2 = ax.contour(X_dates, Y_dates, TOF, levels=levels_tof, colors='magenta', linestyles='dashed', linewidths=1.0)
    ax.clabel(CS2, inline=1, fontsize=10, fmt='%d d')

    # Grid
    ax.grid(True, linestyle=':', alpha=0.6)

    # Add generated timestamp (Palette UX)
    # Placing it bottom-right, outside axes to avoid clutter but ensure traceability
    plt.figtext(0.99, 0.01, f"Generated by AstroChop on {datetime.now().strftime('%Y-%m-%d')}",
                horizontalalignment='right', fontsize=8, color='#555555')

    # Legend elements
    legend_elements = []

    # Plot optimal transfer marker if provided
    if optimal_transfer:
        # Support 2-tuple (dates), 4-tuple (dates + values), or 5-tuple (dates + values + v_inf)
        if len(optimal_transfer) == 5:
            opt_launch, opt_arrival, opt_c3, opt_tof, opt_vinf = optimal_transfer
            dep_vinf = np.sqrt(opt_c3)
            label_text = f"$C_3$: {opt_c3:.1f} km$^2$/s$^2$\nDep $V_\\infty$: {dep_vinf:.2f} km/s\nArr $V_\\infty$: {opt_vinf:.2f} km/s\nTOF: {opt_tof:.0f} days ({opt_tof/30.44:.1f} mo)"
        elif len(optimal_transfer) == 4:
            opt_launch, opt_arrival, opt_c3, opt_tof = optimal_transfer
            dep_vinf = np.sqrt(opt_c3)
            label_text = f"$C_3$: {opt_c3:.1f} km$^2$/s$^2$\nDep $V_\\infty$: {dep_vinf:.2f} km/s\nTOF: {opt_tof:.0f} days ({opt_tof/30.44:.1f} mo)"
        else:
            opt_launch, opt_arrival = optimal_transfer
            label_text = None

        # Convert to matplotlib date format
        opt_launch_num = mdates.date2num(opt_launch)
        opt_arrival_num = mdates.date2num(opt_arrival)

        ax.plot(opt_launch_num, opt_arrival_num, marker='*', color='gold',
                markersize=15, markeredgecolor='black', label='Optimal Transfer', zorder=10)

        legend_elements.append(Line2D([0], [0], marker='*', color='w', markerfacecolor='gold',
                                      markeredgecolor='black', markersize=15, linestyle='None', label='Optimal Transfer'))

        if label_text:
            # Enhance UX: Add Launch/Arrival dates to annotation and use nicer colors
            launch_str = opt_launch.strftime('%Y-%m-%d (%a)')
            arrival_str = opt_arrival.strftime('%Y-%m-%d (%a)')
            label_text = f"Launch: {launch_str}\nArrival: {arrival_str}\n" + label_text

            # Smart Label Placement: Avoid cutting off text at edges by pointing towards center
            # Calculate relative position in the plot window (0.0 to 1.0)
            x_min, x_max = mdates.date2num(min(launch_dates)), mdates.date2num(max(launch_dates))
            y_min, y_max = mdates.date2num(min(arrival_dates)), mdates.date2num(max(arrival_dates))

            x_rel = (opt_launch_num - x_min) / (x_max - x_min)
            y_rel = (opt_arrival_num - y_min) / (y_max - y_min)

            # Point towards center: if > 0.6 (right/top), text goes left/down
            x_off = -30 if x_rel > 0.6 else 30
            y_off = -30 if y_rel > 0.6 else 30

            # Align text away from the point
            ha = 'right' if x_off < 0 else 'left'
            va = 'top' if y_off < 0 else 'bottom'

            ax.annotate(label_text, (opt_launch_num, opt_arrival_num),
                        xytext=(x_off, y_off), textcoords='offset points',
                        ha=ha, va=va,
                        bbox=dict(boxstyle="round,pad=0.5", fc="#FFFFE0", ec="#FFD700", alpha=0.95), # Light yellow bg, Gold edge
                        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2", color="#444444"),
                        fontsize=9, zorder=11)

    # Add contour explanations to legend
    # Note: C3 contours are white on the plot, but we use gray in the legend for visibility on the white background
    legend_elements.append(Line2D([0], [0], color='gray', lw=1, label='$C_3$ Energy (White Contours)'))
    legend_elements.append(Line2D([0], [0], color='magenta', linestyle='dashed', lw=1, label='Time of Flight'))

    ax.legend(handles=legend_elements, loc='best', framealpha=0.95, shadow=True, fancybox=True)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    fig.autofmt_xdate()
    
    ax.set_title(title)
    ax.set_xlabel('Launch Date')
    ax.set_ylabel('Arrival Date')
    
    # Security: Prevent path traversal and enforce extension (similar to mesh_exporter.py)
    real_path = os.path.realpath(filename)
    cwd = os.path.realpath(os.getcwd())

    if os.path.commonpath([cwd, real_path]) != cwd:
        raise ValueError(f"Security Error: File path resolves to '{real_path}', which is outside the current working directory.")

    if not filename.lower().endswith('.png'):
        raise ValueError(f"Security Error: Filename '{filename}' must end with .png extension.")

    # Security: Use os.open with O_NOFOLLOW to prevent TOCTOU symlink attacks
    # O_TRUNC to overwrite if exists, O_CREAT to create if not exists
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC

    # O_NOFOLLOW is not available on Windows
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW

    import errno
    try:
        # Set mode to 0o600 (rw-------) to ensure privacy
        fd = os.open(filename, flags, 0o600)
    except OSError as e:
        if hasattr(errno, 'ELOOP') and e.errno == errno.ELOOP:
            raise ValueError(f"Security Error: File path '{filename}' is a symbolic link.")
        raise

    with os.fdopen(fd, 'wb') as f:
        plt.savefig(f, format='png')
