import unittest
import os
import shutil
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock
from plotter import plot_porkchop
from datetime import datetime
import errno

class TestPlotterSecurity(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Mock data
        self.launch_dates = [datetime(2023, 1, 1), datetime(2023, 1, 2)]
        self.arrival_dates = [datetime(2023, 2, 1), datetime(2023, 2, 2)]
        self.C3 = np.array([[10, 20], [30, 40]])
        self.TOF = np.array([[100, 110], [120, 130]])

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.test_dir)

    def test_plot_porkchop_symlink_attack(self):
        """Test that plot_porkchop refuses to write to a symlink."""
        target_file = 'target.png'
        symlink_file = 'symlink.png'

        # Create a dummy target file
        with open(target_file, 'w') as f:
            f.write('original content')

        # Create a symlink
        try:
            os.symlink(target_file, symlink_file)
        except OSError:
            self.skipTest("Symlinks not supported on this OS")

        # Mock plt.savefig to avoid actual plotting overhead/errors
        with patch('matplotlib.pyplot.savefig') as mock_save:
            # Expect a ValueError due to security check
            with self.assertRaises(ValueError) as cm:
                plot_porkchop(self.launch_dates, self.arrival_dates, self.C3, self.TOF, filename=symlink_file)

            self.assertIn("symbolic link", str(cm.exception))

    def test_plot_porkchop_normal_write(self):
        """Test that normal file writing works."""
        filename = 'output.png'

        # We need to mock plt.savefig but verify it receives a file object if we change the code
        with patch('matplotlib.pyplot.savefig') as mock_save:
            plot_porkchop(self.launch_dates, self.arrival_dates, self.C3, self.TOF, filename=filename)

            # Verify savefig called with file object
            args, _ = mock_save.call_args
            self.assertTrue(hasattr(args[0], 'write'), "savefig should be called with a file-like object")

if __name__ == '__main__':
    unittest.main()
