import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from src.plotter import plot_porkchop
import os

class TestReproTOFUx(unittest.TestCase):
    def setUp(self):
        self.filename = 'repro_test.png'
        # Data for a very short mission (10-20 days)
        # The current hardcoded range is 100-1000, so this should result in NO contours
        self.launch_dates = [datetime(2025, 1, 1), datetime(2025, 1, 2)]
        self.arrival_dates = [datetime(2025, 1, 15), datetime(2025, 1, 16)]
        self.C3 = np.array([[10, 12], [11, 13]])
        self.TOF = np.array([[10, 12], [11, 13]]) # Range 10-13 days

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    @patch('src.plotter.plt.subplots')
    def test_tof_contours_dynamic_for_short_trips(self, mock_subplots):
        # Mock the axes and figure
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        # Call the function
        try:
            plot_porkchop(
                self.launch_dates,
                self.arrival_dates,
                self.C3,
                self.TOF,
                filename=self.filename
            )
        except Exception:
            # We don't care about file writing errors here (mock doesn't create file)
            pass

        # Inspect calls to ax.contour
        # We expect two calls: one for C3 (white), one for TOF (red/dashed)
        contour_calls = mock_ax.contour.call_args_list

        found_tof = False
        tof_levels = None

        for call in contour_calls:
            _, kwargs = call
            if kwargs.get('colors') == 'magenta':
                found_tof = True
                tof_levels = kwargs.get('levels')
                break

        self.assertTrue(found_tof, "TOF contour plot should be called")

        # Verify that levels are now suitable for the data range (10-13)
        # Dynamic levels should cover the range
        data_min = self.TOF.min()
        data_max = self.TOF.max()

        # Convert levels to list for inspection
        levels_list = list(tof_levels)

        # Check that at least one level is within the data range
        levels_in_range = [l for l in levels_list if data_min <= l <= data_max]

        self.assertTrue(len(levels_in_range) > 0, f"Dynamic levels {levels_list} do not cover data range [{data_min}, {data_max}]")

        # Check that levels are roughly integers (since they come from linspace().astype(int))
        self.assertTrue(all(isinstance(x, (int, np.integer)) for x in levels_list), "Levels should be integers")

if __name__ == '__main__':
    unittest.main()
