## 2024-03-24 - [Secure File Writing Pattern]
**Vulnerability:** TOCTOU (Time-of-Check Time-of-Use) race condition in file writing. `plt.savefig(filename)` opens the file after path checks, allowing an attacker to replace the file with a symlink in between.
**Learning:** `matplotlib.pyplot.savefig` accepts a file-like object, which allows passing a safe file descriptor opened with `os.open` and `O_NOFOLLOW`.
**Prevention:** Use `os.open(filename, flags, mode)` with `O_NOFOLLOW` (if available) to get a file descriptor, then `os.fdopen(fd, 'wb')` to get a file object, and pass that to the library function instead of the filename string.
