import numpy as np

class DataGrid:
    """
    Holds the 2D data for the porkchop plot.
    """
    def __init__(self, data, x_axis, y_axis):
        """
        Args:
            data (np.array): 2D array of scalar values (e.g., C3). Shape (ny, nx).
            x_axis (np.array): 1D array of x coordinates (e.g., Launch Dates).
            y_axis (np.array): 1D array of y coordinates (e.g., Arrival Dates).
        """
        self.data = np.array(data)
        self.x_axis = np.array(x_axis)
        self.y_axis = np.array(y_axis)

        if self.data.shape != (len(y_axis), len(x_axis)):
            raise ValueError(f"Data shape {self.data.shape} does not match axes lengths ({len(y_axis)}, {len(x_axis)})")

    @property
    def width(self):
        return len(self.x_axis)

    @property
    def height(self):
        return len(self.y_axis)

class PorkchopMesh:
    """
    Generates a mesh from a DataGrid.
    """
    def __init__(self, data_grid):
        self.grid = data_grid
        self.vertices = None
        self.indices = None
        self.uvs = None # Normalized scalar values
        self.scalars = None # Original or morphed values
        self.x_bounds = None
        self.y_bounds = None
        self.z_bounds = None

    def generate_mesh(self, z_scale=1.0, morph_type='linear'):
        """
        Generates vertices and indices for the mesh.

        Args:
            z_scale (float): Scaling factor for the Z-axis height.
            morph_type (str): 'linear', 'log_e', or 'log_10'. Transforms the Z values.
        """
        nx = self.grid.width
        ny = self.grid.height

        # 1. Process Data (Morphing)
        raw_data = self.grid.data.copy()

        # Handle NaNs or Infs
        raw_data = np.nan_to_num(raw_data, nan=np.nanmax(raw_data) if not np.isnan(raw_data).all() else 0.0)

        if morph_type == 'log_e':
            # Avoid log(0) or log(negative)
            mask = raw_data > 0
            morphed_data = np.zeros_like(raw_data)
            morphed_data[mask] = np.log(raw_data[mask])
            morphed_data[~mask] = np.min(morphed_data[mask]) if np.any(mask) else 0
        elif morph_type == 'log_10':
            mask = raw_data > 0
            morphed_data = np.zeros_like(raw_data)
            morphed_data[mask] = np.log10(raw_data[mask])
            morphed_data[~mask] = np.min(morphed_data[mask]) if np.any(mask) else 0
        else: # linear
            morphed_data = raw_data

        self.scalars = morphed_data

        # 2. Normalize for UVs/Coloring (0..1)
        d_min = np.min(morphed_data)
        d_max = np.max(morphed_data)
        if d_max > d_min:
            self.uvs = (morphed_data - d_min) / (d_max - d_min)
        else:
            self.uvs = np.zeros_like(morphed_data)

        # 3. Generate Vertices
        # X maps to x_axis (Launch Date JD)
        # Y maps to y_axis (Arrival Date JD)
        # Z maps to morphed_data * z_scale

        # Use meshgrid for efficiency
        X, Y = np.meshgrid(self.grid.x_axis, self.grid.y_axis)
        Z = morphed_data * z_scale

        # Flatten
        self.vertices = np.stack((X.flatten(), Y.flatten(), Z.flatten()), axis=1)

        # Store bounds
        self.x_bounds = (np.min(X), np.max(X))
        self.y_bounds = (np.min(Y), np.max(Y))
        self.z_bounds = (np.min(Z), np.max(Z))

        # 4. Generate Indices (Triangles)
        # Grid topology:
        # v0 --- v1
        # |      |
        # v2 --- v3
        # Triangles: (v0, v2, v1) and (v1, v2, v3)

        # Optimization: Vectorized Index Generation
        # Replace nested loops (O(N*M)) with NumPy broadcasting (O(1))

        # Base indices for top-left corners (v0)
        # Grid is (ny) rows by (nx) columns
        x_idx = np.arange(nx - 1)
        y_idx = np.arange(ny - 1)
        X_idx, Y_idx = np.meshgrid(x_idx, y_idx)

        # Calculate v0 for each quad
        v0 = Y_idx * nx + X_idx

        # Calculate other vertices relative to v0
        v1 = v0 + 1
        v2 = v0 + nx
        v3 = v2 + 1

        # Flatten arrays to process as list of quads
        v0 = v0.flatten()
        v1 = v1.flatten()
        v2 = v2.flatten()
        v3 = v3.flatten()

        # Create triangles
        # T1: v0, v2, v1
        t1 = np.stack((v0, v2, v1), axis=1)

        # T2: v1, v2, v3
        t2 = np.stack((v1, v2, v3), axis=1)

        # Interleave triangles to preserve quad locality (T1_0, T2_0, T1_1, T2_1...)
        n_quads = (nx - 1) * (ny - 1)
        indices = np.empty((n_quads * 2, 3), dtype=np.int32)
        indices[0::2] = t1
        indices[1::2] = t2

        self.indices = indices

    def intersect_ray(self, ray_origin, ray_dir):
        """
        Finds the intersection of a ray with the mesh.
        Uses Möller–Trumbore intersection algorithm.
        Returns the closest intersection distance and triangle index.

        Args:
            ray_origin (np.array): [x, y, z]
            ray_dir (np.array): [dx, dy, dz] (should be normalized)

        Returns:
            (t, triangle_index, point): t is distance, index is index in self.indices.
            Returns (None, -1, None) if no intersection.
        """
        # This is a naive O(N) check. A BVH would be better for performance,
        # but for typical porkchop plots (e.g. 100x100), 20k tris is manageable.

        best_t = float('inf')
        best_idx = -1

        # Vectorized implementation of Moller-Trumbore
        # V0: (N, 3), V1: (N, 3), V2: (N, 3)
        tris = self.indices
        v0s = self.vertices[tris[:, 0]]
        v1s = self.vertices[tris[:, 1]]
        v2s = self.vertices[tris[:, 2]]

        edge1 = v1s - v0s
        edge2 = v2s - v0s

        h = np.cross(ray_dir, edge2)
        a = np.einsum('ij,ij->i', edge1, h)

        # Parallel check (epsilon)
        epsilon = 1e-7
        # We assume culling is disabled (back-faces visible) for now, or check sign of a

        mask = np.abs(a) > epsilon

        f = 1.0 / a[mask]
        s = ray_origin - v0s[mask]
        u = f * np.einsum('ij,ij->i', s, h[mask])

        mask_u = (u >= 0.0) & (u <= 1.0)

        # Refine mask
        valid_indices = np.where(mask)[0][mask_u]
        if len(valid_indices) == 0:
            return None, -1, None

        # q = s x edge1
        # v = f * (dir . q)

        # We need to re-slice arrays based on current valid set to save computation?
        # Let's just do it for the reduced set.

        # Re-calc subset
        v0s = v0s[valid_indices]
        edge1 = edge1[valid_indices]
        edge2 = edge2[valid_indices]

        h = np.cross(ray_dir, edge2)
        a = np.einsum('ij,ij->i', edge1, h)
        f = 1.0 / a
        s = ray_origin - v0s
        u = f * np.einsum('ij,ij->i', s, h)

        q = np.cross(s, edge1)
        v = f * np.einsum('j,ij->i', ray_dir, q)

        mask_v = (v >= 0.0) & (u + v <= 1.0)

        valid_indices_final = valid_indices[mask_v]

        if len(valid_indices_final) == 0:
            return None, -1, None

        # Calculate t
        # t = f * (edge2 . q)
        q = q[mask_v]
        edge2 = edge2[mask_v]
        f = f[mask_v]

        t = f * np.einsum('ij,ij->i', edge2, q)

        mask_t = t > epsilon

        valid_indices_final = valid_indices_final[mask_t]
        t_final = t[mask_t]

        if len(t_final) == 0:
            return None, -1, None

        min_arg = np.argmin(t_final)
        best_t = t_final[min_arg]
        best_idx = valid_indices_final[min_arg]

        point = ray_origin + ray_dir * best_t
        return best_t, best_idx, point
