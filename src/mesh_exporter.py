import numpy as np
import os

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
    cwd = os.getcwd()

    if os.path.commonpath([cwd, real_path]) != cwd:
        raise ValueError(f"Security Error: File path resolves to '{real_path}', which is outside the current working directory.")

    # Also explicitly disallow writing to a symlink
    if os.path.islink(filename):
        raise ValueError(f"Security Error: File path '{filename}' is a symbolic link.")

    if mesh.vertices is None or mesh.indices is None:
        raise ValueError("Mesh has not been generated. Call generate_mesh() first.")

    # Security: Prevent path traversal and enforce extension
    if not filename.endswith('.vtp'):
        raise ValueError("Filename must end with .vtp")

    if '..' in filename:
        raise ValueError("Path traversal detected in filename")

    n_points = len(mesh.vertices)
    n_polys = len(mesh.indices)

    # Format data as space-separated strings
    points_str = "\n".join([f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in mesh.vertices])

    # Indices: "3 v0 v1 v2" for triangles
    # But in VTP/XML, we store connectivity and offsets separately.
    # Connectivity: v0 v1 v2 v3 v4 v5 ...
    # Offsets: 3 6 9 ...

    connectivity = mesh.indices.flatten()
    connectivity_str = " ".join(map(str, connectivity))

    offsets = np.arange(3, n_polys * 3 + 1, 3)
    offsets_str = " ".join(map(str, offsets))

    # Scalars (C3 or Morphed Value)
    # We flatten the grid data same way vertices are flattened
    scalars = mesh.scalars.flatten()
    scalars_str = " ".join([f"{s:.6f}" for s in scalars])

    uvs = mesh.uvs.flatten()
    uvs_str = " ".join([f"{u:.6f}" for u in uvs])

    with open(filename, 'w') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<VTKFile type="PolyData" version="0.1" byte_order="LittleEndian">\n')
        f.write('  <PolyData>\n')
        f.write(f'    <Piece NumberOfPoints="{n_points}" NumberOfPolys="{n_polys}">\n')

        # Points
        f.write('      <Points>\n')
        f.write('        <DataArray type="Float32" Name="Points" NumberOfComponents="3" format="ascii">\n')
        f.write(points_str + '\n')
        f.write('        </DataArray>\n')
        f.write('      </Points>\n')

        # Polys
        f.write('      <Polys>\n')
        f.write('        <DataArray type="Int32" Name="connectivity" format="ascii">\n')
        f.write(connectivity_str + '\n')
        f.write('        </DataArray>\n')
        f.write('        <DataArray type="Int32" Name="offsets" format="ascii">\n')
        f.write(offsets_str + '\n')
        f.write('        </DataArray>\n')
        f.write('      </Polys>\n')

        # Point Data
        f.write('      <PointData Scalars="MorphedValue">\n')
        f.write('        <DataArray type="Float32" Name="MorphedValue" format="ascii">\n')
        f.write(scalars_str + '\n')
        f.write('        </DataArray>\n')
        f.write('        <DataArray type="Float32" Name="NormalizedUV" format="ascii">\n')
        f.write(uvs_str + '\n')
        f.write('        </DataArray>\n')
        f.write('      </PointData>\n')

        f.write('    </Piece>\n')
        f.write('  </PolyData>\n')
        f.write('</VTKFile>\n')
