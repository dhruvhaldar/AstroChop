import unittest
import numpy as np
from src.porkchop_mesh import DataGrid, PorkchopMesh

class TestPorkchopMesh(unittest.TestCase):
    def test_datagrid(self):
        data = np.array([[1, 2], [3, 4]])
        x = [0, 1]
        y = [0, 1]
        grid = DataGrid(data, x, y)
        self.assertEqual(grid.width, 2)
        self.assertEqual(grid.height, 2)

    def test_mesh_generation(self):
        data = np.zeros((3, 3))
        data[1, 1] = 1.0 # Bump in the middle
        x = [0, 1, 2]
        y = [0, 1, 2]
        grid = DataGrid(data, x, y)
        mesh = PorkchopMesh(grid)
        mesh.generate_mesh(z_scale=10.0, morph_type='linear')

        # Check vertices
        self.assertEqual(len(mesh.vertices), 9)
        # Check center vertex (index 4)
        center_v = mesh.vertices[4]
        self.assertEqual(center_v[0], 1)
        self.assertEqual(center_v[1], 1)
        self.assertEqual(center_v[2], 10.0)

        # Check indices
        # 3x3 grid has 2x2 cells = 4 cells
        # 4 cells * 2 tris/cell = 8 tris
        self.assertEqual(len(mesh.indices), 8)

    def test_intersection(self):
        # 2x2 grid, flat plane at z=0
        data = np.zeros((2, 2))
        x = [-1, 1]
        y = [-1, 1]
        grid = DataGrid(data, x, y)
        mesh = PorkchopMesh(grid)
        mesh.generate_mesh()

        # Ray from top down to (0,0,0)
        ray_origin = np.array([0.0, 0.0, 10.0])
        ray_dir = np.array([0.0, 0.0, -1.0])

        t, idx, pt = mesh.intersect_ray(ray_origin, ray_dir)

        self.assertIsNotNone(t)
        self.assertAlmostEqual(pt[0], 0.0)
        self.assertAlmostEqual(pt[1], 0.0)
        self.assertAlmostEqual(pt[2], 0.0)

        # Ray missing (outside grid)
        ray_origin_miss = np.array([5.0, 0.0, 10.0])
        t, idx, pt = mesh.intersect_ray(ray_origin_miss, ray_dir)
        self.assertIsNone(t)

if __name__ == '__main__':
    unittest.main()
