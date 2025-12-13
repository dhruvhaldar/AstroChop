import vtk
import numpy as np

def write_vtp(filename, mesh):
    """
    Writes the PorkchopMesh to a VTK XML PolyData (.vtp) file using the vtk library.

    Args:
        filename (str): Output filename (should end in .vtp).
        mesh (PorkchopMesh): The mesh object to export.
    """
    if mesh.vertices is None or mesh.indices is None:
        raise ValueError("Mesh has not been generated. Call generate_mesh() first.")

    # 1. Create Points
    points = vtk.vtkPoints()
    # vtkPoints expects float data. We can pass the numpy array directly?
    # vtk.util.numpy_support is best for this.
    from vtk.util import numpy_support

    # Ensure float32 or float64
    verts_flat = mesh.vertices.astype(np.float32)
    vtk_points_data = numpy_support.numpy_to_vtk(verts_flat, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_points_data.SetNumberOfComponents(3)
    points.SetData(vtk_points_data)

    # 2. Create Polygons (Cells)
    # The indices array is (N, 3). VTK needs a cell array which is [n, id0, id1, ...].
    # For triangles: [3, v0, v1, v2, 3, v3, v4, v5, ...]
    n_triangles = len(mesh.indices)

    # Prepend '3' to each triangle index set
    # Create column of 3s
    threes = np.full((n_triangles, 1), 3, dtype=np.int64)
    # Stack [3, v0, v1, v2]
    cells_array = np.hstack((threes, mesh.indices))
    cells_flat = cells_array.flatten().astype(np.int64)

    vtk_cells = vtk.vtkCellArray()
    vtk_cells_data = numpy_support.numpy_to_vtkIdTypeArray(cells_flat, deep=True)
    vtk_cells.SetCells(n_triangles, vtk_cells_data)

    # 3. Create PolyData
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(vtk_cells)

    # 4. Add Point Data (Scalars)
    # Morphed Value
    scalars = mesh.scalars.flatten().astype(np.float32)
    vtk_scalars = numpy_support.numpy_to_vtk(scalars, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_scalars.SetName("MorphedValue")
    polydata.GetPointData().SetScalars(vtk_scalars)

    # UVs (Normalized)
    uvs = mesh.uvs.flatten().astype(np.float32)
    vtk_uvs = numpy_support.numpy_to_vtk(uvs, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_uvs.SetName("NormalizedUV")
    polydata.GetPointData().AddArray(vtk_uvs)

    # 5. Write to File
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(filename)
    writer.SetInputData(polydata)
    writer.SetDataModeToAscii() # Or Binary for compactness
    writer.Write()

    print(f"Mesh saved to {filename} using vtk library.")
