import unittest
import os
import shutil
import numpy as np
from src.porkchop_mesh import DataGrid, PorkchopMesh
from src.mesh_exporter import write_vtp

class TestMeshExporter(unittest.TestCase):
    def setUp(self):
        # Create a simple mesh for testing
        data = np.zeros((2, 2))
        x = [0, 1]
        y = [0, 1]
        grid = DataGrid(data, x, y)
        self.mesh = PorkchopMesh(grid)
        self.mesh.generate_mesh()

        # Create a temp dir for output
        self.test_dir = 'test_output'
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # Also clean up any files written to root or parent (if any tests accidentally pass)
        if os.path.exists('test_output.vtp'):
            os.remove('test_output.vtp')
        # We try to avoid polluting parent dirs

    def test_valid_write(self):
        filepath = os.path.join(self.test_dir, 'valid.vtp')
        write_vtp(filepath, self.mesh)
        self.assertTrue(os.path.exists(filepath))

    def test_path_traversal(self):
        # Try to write to parent directory
        # We need a filename that includes '..'
        # Note: In a real attack, this allows writing anywhere.
        # In this test environment, we just check if the function rejects '..' string.

        # We expect this to raise ValueError once fixed.
        # Currently it will likely succeed (and write a file to parent dir), or fail due to permissions.
        # If it succeeds, we'll have to manually clean it up.

        filename = '../sentinel_test_traversal.vtp'

        with self.assertRaises(ValueError):
            write_vtp(filename, self.mesh)

        # Cleanup if it failed to raise (meaning it wrote the file)
        if os.path.exists('sentinel_test_traversal.vtp'):
             os.remove('sentinel_test_traversal.vtp')
        if os.path.exists('../sentinel_test_traversal.vtp'):
             os.remove('../sentinel_test_traversal.vtp')

    def test_invalid_extension(self):
        filename = os.path.join(self.test_dir, 'wrong_ext.txt')
        with self.assertRaises(ValueError):
            write_vtp(filename, self.mesh)

if __name__ == '__main__':
    unittest.main()
