## 2024-05-24 - [Path Traversal in Mesh Exporter]
**Vulnerability:** The `write_vtp` function in `src/mesh_exporter.py` allowed writing files to arbitrary paths using directory traversal (e.g., `../file`).
**Learning:** Libraries performing file I/O must validate paths, especially if they might be used with user-controlled input, even if the current consumer is hardcoded.
**Prevention:** Use `os.path.abspath` and `os.path.commonpath` (or `os.path.commonprefix` with caution) to ensure the target path is within the intended directory (e.g., `os.getcwd()`).

## 2025-02-18 - [Symlink Attack via File Overwrite]
**Vulnerability:** The `write_vtp` function in `src/mesh_exporter.py` was vulnerable to Symlink Attacks. While it checked for path traversal using `os.path.abspath`, it did not resolve symbolic links. An attacker could create a symlink in the allowed directory pointing to a sensitive file outside the directory (e.g., `/etc/passwd`), and the tool would overwrite the target.
**Learning:** `os.path.abspath` does not resolve symbolic links. Validation using it alone is insufficient against symlink attacks.
**Prevention:** Use `os.path.realpath` to resolve the canonical path before checking `os.path.commonpath`. Additionally, explicitly checking `os.path.islink` adds another layer of defense against writing to unintended targets.

## 2025-02-19 - TOCTOU Mitigation
**Vulnerability:** Time-of-Check Time-of-Use (TOCTOU) race condition in file writing. An attacker could replace a file with a symlink between the check and the open call.
**Learning:** Checking for symlinks (os.path.islink) before opening a file is insufficient. Atomic operations using os.open with O_NOFOLLOW are required.
**Prevention:** Use os.open with O_NOFOLLOW for writing files in security-sensitive contexts.

## 2025-02-27 - [Unbounded Allocation DoS in Plotter]
**Vulnerability:** The `generate_porkchop` function in `src/plotter.py` allowed generating arbitrarily large grids (e.g., 30M+ points) without validation, leading to potential Denial of Service (DoS) via memory exhaustion.
**Learning:** Numerical functions exposed to potential user input (even indirectly) must enforce resource limits. NumPy allocations for large multi-dimensional arrays can easily exceed available RAM.
**Prevention:** Implement explicit limits (e.g., `MAX_GRID_SIZE`) on input dimensions before allocating large arrays.

## 2025-02-27 - [Path Traversal in Plotter]
**Vulnerability:** The `plot_porkchop` function lacked path validation, allowing writing images to arbitrary paths (e.g., `../../etc/passwd`).
**Learning:** Consistency in security controls is key. While `mesh_exporter.py` was secured, `plotter.py` was not.
**Prevention:** Reused the `os.path.realpath` + `os.path.commonpath` pattern from `mesh_exporter.py` and added file extension enforcement.

## 2025-02-27 - [Log Injection via Filename]
**Vulnerability:** Exceptions raised by `write_vtp` and `plot_porkchop` included the user-provided filename in the error message. If a filename contained newline characters (e.g., `test\n[CRITICAL] Pwned`), an attacker could forge log entries if these exceptions were logged by the calling application.
**Learning:** Input validation must include checking for control characters in data that might be logged, especially file paths which can technically contain newlines in some filesystems (like Linux).
**Prevention:** Explicitly validate filenames against a blacklist of control characters (like `\n`, `\r`) before processing or including them in error messages.
