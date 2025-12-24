## 2024-05-24 - [Path Traversal in Mesh Exporter]
**Vulnerability:** The `write_vtp` function in `src/mesh_exporter.py` allowed writing files to arbitrary paths using directory traversal (e.g., `../file`).
**Learning:** Libraries performing file I/O must validate paths, especially if they might be used with user-controlled input, even if the current consumer is hardcoded.
**Prevention:** Use `os.path.abspath` and `os.path.commonpath` (or `os.path.commonprefix` with caution) to ensure the target path is within the intended directory (e.g., `os.getcwd()`).

## 2025-02-18 - [Symlink Attack via File Overwrite]
**Vulnerability:** The `write_vtp` function in `src/mesh_exporter.py` was vulnerable to Symlink Attacks. While it checked for path traversal using `os.path.abspath`, it did not resolve symbolic links. An attacker could create a symlink in the allowed directory pointing to a sensitive file outside the directory (e.g., `/etc/passwd`), and the tool would overwrite the target.
**Learning:** `os.path.abspath` does not resolve symbolic links. Validation using it alone is insufficient against symlink attacks.
**Prevention:** Use `os.path.realpath` to resolve the canonical path before checking `os.path.commonpath`. Additionally, explicitly checking `os.path.islink` adds another layer of defense against writing to unintended targets.
