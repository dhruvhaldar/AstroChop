import numpy as np
import os
import errno

def write_vtp(filename, mesh):
    """
    Writes the PorkchopMesh to a VTK XML PolyData (.vtp) file.

    Args:
        filename (str): Output filename (should end in .vtp).
        mesh (PorkchopMesh): The mesh object to export.

    Raises:
        ValueError: If mesh is not generated or filename has path traversal attempt.
    """
    # Security Check: Prevent path traversal and Symlink attacks
    # Ensure the file is written within the current working directory
    # Resolve symlinks to find the actual destination
    real_path = os.path.realpath(filename)
    cwd = os.path.realpath(os.getcwd())

    if os.path.commonpath([cwd, real_path]) != cwd:
        raise ValueError(f"Security Error: File path resolves to '{real_path}', which is outside the current working directory.")

    if mesh.vertices is None or mesh.indices is None:
        raise ValueError("Mesh has not been generated. Call generate_mesh() first.")

    # Security: Prevent path traversal and enforce extension
    if not filename.endswith('.vtp'):
        raise ValueError("Filename must end with .vtp")

    if '..' in filename:
        raise ValueError("Path traversal detected in filename")

    n_points = len(mesh.vertices)
    n_polys = len(mesh.indices)

    # Use os.open with O_NOFOLLOW to prevent symlink attacks (TOCTOU)
    # O_TRUNC to overwrite if exists, O_CREAT to create if not exists
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC

    # O_NOFOLLOW is not available on Windows
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW

    try:
        # Set mode to 0o600 (rw-------) for security (owner read/write only)
        fd = os.open(filename, flags, 0o600)
    except OSError as e:
        if hasattr(errno, 'ELOOP') and e.errno == errno.ELOOP:
            raise ValueError(f"Security Error: File path '{filename}' is a symbolic link.")
        raise

    with os.fdopen(fd, 'w') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<VTKFile type="PolyData" version="0.1" byte_order="LittleEndian">\n')
        f.write('  <PolyData>\n')
        f.write(f'    <Piece NumberOfPoints="{n_points}" NumberOfPolys="{n_polys}">\n')

        # Points
        f.write('      <Points>\n')
        f.write('        <DataArray type="Float32" Name="Points" NumberOfComponents="3" format="ascii">\n')
        # Optimized: Use np.savetxt to stream data instead of creating large string
        # This drastically reduces memory usage for large meshes (e.g. 25M points)
        # Time tradeoff is acceptable for stability.
        np.savetxt(f, mesh.vertices, fmt='%.6f', delimiter=' ')
        f.write('        </DataArray>\n')
        f.write('      </Points>\n')

        # Polys
        f.write('      <Polys>\n')
        f.write('        <DataArray type="Int32" Name="connectivity" format="ascii">\n')
        # Optimized: Write indices directly. VTP supports newline separation.
        np.savetxt(f, mesh.indices, fmt='%d', delimiter=' ')
        f.write('        </DataArray>\n')
        f.write('        <DataArray type="Int32" Name="offsets" format="ascii">\n')

        offsets = np.arange(3, n_polys * 3 + 1, 3)
        np.savetxt(f, offsets, fmt='%d') # Defaults to newline delimiter
        f.write('        </DataArray>\n')
        f.write('      </Polys>\n')

        # Point Data
        f.write('      <PointData Scalars="MorphedValue">\n')
        f.write('        <DataArray type="Float32" Name="MorphedValue" format="ascii">\n')
        np.savetxt(f, mesh.scalars, fmt='%.6f')
        f.write('        </DataArray>\n')
        f.write('        <DataArray type="Float32" Name="NormalizedUV" format="ascii">\n')
        np.savetxt(f, mesh.uvs, fmt='%.6f')
        f.write('        </DataArray>\n')
        f.write('      </PointData>\n')

        f.write('    </Piece>\n')
        f.write('  </PolyData>\n')
        f.write('</VTKFile>\n')
