import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import numpy as np
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from plotter import plot_porkchop

class TestSecurityPlotterTOCTOU(unittest.TestCase):
    def setUp(self):
        # Mock data for plot_porkchop
        self.launch_dates = [datetime(2023, 1, 1), datetime(2023, 1, 2)]
        self.arrival_dates = [datetime(2023, 6, 1), datetime(2023, 6, 2)]
        self.C3 = np.zeros((2, 2))
        self.TOF = np.zeros((2, 2))
        self.filename = 'test_secure_plot.png'

    @patch('os.open')
    @patch('os.fdopen')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.subplots')
    def test_plot_porkchop_uses_secure_open(self, mock_subplots, mock_savefig, mock_fdopen, mock_open):
        # Setup mocks
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        # Mock os.open to return a fake file descriptor
        mock_fd = 123
        mock_open.return_value = mock_fd

        # Mock os.fdopen to return a fake file object
        mock_file = MagicMock()
        mock_fdopen.return_value = mock_file
        mock_file.__enter__.return_value = mock_file

        # Call the function
        # We need to ensure the file is created in CWD or handle the path check
        # The existing path check uses os.path.realpath(filename) vs CWD
        # So providing a simple filename should pass the path check if we are in a writable dir

        try:
            plot_porkchop(self.launch_dates, self.arrival_dates, self.C3, self.TOF, filename=self.filename)
        except ValueError as e:
            # If it fails due to existing checks (e.g. extension), we fail the test
            self.fail(f"plot_porkchop raised ValueError: {e}")

        # Assert that os.open was called
        # This is the key assertion: we expect os.open to be called instead of plt.savefig opening the file directly
        # If the code uses plt.savefig(filename), os.open will NOT be called (or not with our expected flags)

        # We expect flags: os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
        # Note: O_NOFOLLOW is platform dependent, but we assumed it exists based on earlier check.

        expected_flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if hasattr(os, 'O_NOFOLLOW'):
            expected_flags |= os.O_NOFOLLOW

        # Verify os.open called with correct filename and flags
        # We use any for mode (3rd arg)
        mock_open.assert_called()
        args, kwargs = mock_open.call_args
        self.assertEqual(args[0], self.filename)
        self.assertEqual(args[1], expected_flags)

        # Verify plt.savefig was called with the file object, not the filename
        mock_savefig.assert_called()
        args_save, _ = mock_savefig.call_args
        # The first argument should be the file object returned by fdopen
        self.assertEqual(args_save[0], mock_file)

if __name__ == '__main__':
    unittest.main()
