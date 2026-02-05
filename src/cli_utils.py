import sys
import time
import threading
import os

def make_hyperlink(text, target):
    """
    Creates an OSC 8 ANSI escape sequence for a hyperlink.
    """
    return f"\033]8;;{target}\033\\{text}\033]8;;\033\\"

def format_date_with_doy(date):
    """
    Formats a date string with weekday and Day of Year (DOY).
    Format: YYYY-MM-DD (Mon, DOY 123)
    """
    doy = date.timetuple().tm_yday
    return f"{date.strftime('%Y-%m-%d (%a')}, DOY {doy})"

class Style:
    """ANSI escape codes for styling CLI output."""
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'

def format_duration(days, short=False):
    """
    Formats a duration in days into a human-friendly string.

    Args:
        days (float): Duration in days.
        short (bool): If True, uses abbreviated units (d, mo, yr).

    Examples:
        25.0 -> "25.0 days" (short: "25.0 d")
        45.0 -> "1 month, 15 days" (short: "1 mo, 15 d")
        400.0 -> "1 year, 1 month" (short: "1 yr, 1 mo")
    """
    if days < 30:
        unit = "d" if short else "days"
        return f"{days:.1f} {unit}"

    # Approx constants
    DAYS_PER_YEAR = 365.25
    DAYS_PER_MONTH = 30.44

    if days >= DAYS_PER_YEAR:
        years = int(days // DAYS_PER_YEAR)
        remaining_days = days % DAYS_PER_YEAR
        months = int(round(remaining_days / DAYS_PER_MONTH))

        # Handle case where rounding up months makes it 12
        if months == 12:
            years += 1
            months = 0

        if short:
            y_str = "yr"
            m_str = "mo"
        else:
            y_str = "year" if years == 1 else "years"
            m_str = "month" if months == 1 else "months"

        if months == 0:
            return f"{years} {y_str}"
        return f"{years} {y_str}, {months} {m_str}"

    else:
        # Months and days
        months = int(days // DAYS_PER_MONTH)
        remaining_days = int(round(days % DAYS_PER_MONTH))

        # Handle rollover
        if remaining_days >= 30: # Rough check to roll over to next month
             months += 1
             remaining_days = 0

        if short:
            m_str = "mo"
            d_str = "d"
        else:
            m_str = "month" if months == 1 else "months"
            d_str = "day" if remaining_days == 1 else "days"

        if remaining_days == 0:
            return f"{months} {m_str}"
        return f"{months} {m_str}, {remaining_days} {d_str}"

def get_c3_rating(value):
    """
    Returns a tuple (color, description) based on C3 energy value (km^2/s^2).

    Context (Earth-Mars):
        < 15: Excellent (Green)
        15-20: Good (Green)
        20-30: Acceptable (Yellow)
        > 30: High Energy (Red)
    """
    if value < 15:
        return Style.GREEN, "(Excellent)"
    elif value <= 20:
        return Style.GREEN, "(Good)"
    elif value <= 30:
        return Style.YELLOW, "(Acceptable)"
    else:
        return Style.RED, "(High Energy)"

def get_c3_color(value):
    """
    Returns the ANSI color code based on C3 energy value (km^2/s^2).
    Wrapper around get_c3_rating for backward compatibility.
    """
    color, _ = get_c3_rating(value)
    return color

def get_vinf_rating(value):
    """
    Returns a tuple (color, description) based on Arrival V-Infinity (km/s).

    Context (Mars Arrival):
        <= 4.5: Good (Green) - manageable for aerocapture
        4.5 - 6.0: Acceptable (Yellow) - challenging
        > 6.0: High (Red) - very difficult propulsive capture
    """
    if value <= 4.5:
        return Style.GREEN, "(Good)"
    elif value <= 6.0:
        return Style.YELLOW, "(Acceptable)"
    else:
        return Style.RED, "(High)"

class Spinner:
    """
    A context manager that displays a spinning animation in the console
    while a block of code is executing.

    Usage:
        with Spinner("Calculating..."):
            long_running_function()
    """
    def __init__(self, message="Processing", delay=0.1):
        self.message = message
        self.delay = delay
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._spin)
        self.start_time = None
        # Check if output is a TTY
        self.is_tty = sys.stdout.isatty()

    def __enter__(self):
        self.start_time = time.time()
        if self.is_tty:
            self.thread.start()
        else:
            # Fallback for non-TTY: just print the message
            sys.stdout.write(f"{self.message}...")
            sys.stdout.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_tty:
            self.stop_event.set()
            self.thread.join()
            # Clear the line
            sys.stdout.write('\r')
        else:
            sys.stdout.write(" ")

        elapsed = time.time() - self.start_time

        if exc_type is KeyboardInterrupt:
            sys.stdout.write(f"{Style.YELLOW}✖ (Cancelled after {elapsed:.1f}s){Style.ENDC}\n")
            if not self.is_tty:
                sys.stdout.write(f"{self.message} Cancelled.\n")
            return False # Propagate interrupt

        if exc_type:
            sys.stdout.write(f"{Style.RED}✖ (Failed after {elapsed:.1f}s){Style.ENDC}\n")
            if not self.is_tty:
                sys.stdout.write(f"{self.message} Failed.\n")
            return False # Propagate exception

        if self.is_tty:
            sys.stdout.write(f"{Style.GREEN}✓ {self.message} ({elapsed:.1f}s){Style.ENDC}\n")
        else:
            sys.stdout.write(f"Done ({elapsed:.1f}s)\n")

        sys.stdout.flush()

    def _spin(self):
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while not self.stop_event.is_set():
            elapsed = time.time() - self.start_time
            sys.stdout.write(f"\r{spinner_chars[i]} {self.message}... ({elapsed:.1f}s)")
            sys.stdout.flush()
            time.sleep(self.delay)
            i = (i + 1) % len(spinner_chars)
