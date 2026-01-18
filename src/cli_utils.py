import sys
import time
import threading

class Style:
    """ANSI escape codes for styling CLI output."""
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'

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
            sys.stdout.write(f"\r{spinner_chars[i]} {self.message}...")
            sys.stdout.flush()
            time.sleep(self.delay)
            i = (i + 1) % len(spinner_chars)
