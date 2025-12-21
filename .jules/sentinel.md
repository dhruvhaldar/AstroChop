## 2024-05-24 - [Path Traversal in Mesh Exporter]
**Vulnerability:** The `write_vtp` function in `src/mesh_exporter.py` allowed writing files to arbitrary paths using directory traversal (e.g., `../file`).
**Learning:** Libraries performing file I/O must validate paths, especially if they might be used with user-controlled input, even if the current consumer is hardcoded.
**Prevention:** Use `os.path.abspath` and `os.path.commonpath` (or `os.path.commonprefix` with caution) to ensure the target path is within the intended directory (e.g., `os.getcwd()`).
