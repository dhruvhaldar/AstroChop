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
**Learning:** Checking for symlinks (`os.path.islink`) before opening a file is insufficient. Atomic operations using `os.open` with `O_NOFOLLOW` are required.
**Prevention:** Use `os.open` with `O_NOFOLLOW` for writing files in security-sensitive contexts.

## 2025-02-20 - [DoS Prevention in Plotter]
**Vulnerability:** The `generate_porkchop` function lacked input size validation, allowing generation of excessively large grids that could cause memory exhaustion (DoS).
**Learning:** Numerical libraries processing user-defined ranges must enforce resource limits (e.g., maximum grid size) to prevent denial of service.
**Prevention:** Added `MAX_GRID_SIZE` limit and validation check before memory allocation.
