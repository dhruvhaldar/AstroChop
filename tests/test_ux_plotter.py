import unittest
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from plotter import plot_porkchop
import os

class TestUXPlotter(unittest.TestCase):
    def setUp(self):
        self.filename = 'test_plot_ux.png'
        # Create dummy data
        self.launch_dates = [datetime(2025, 1, 1), datetime(2025, 1, 2)]
        self.arrival_dates = [datetime(2025, 6, 1), datetime(2025, 6, 2)]
        self.C3 = np.array([[10, 12], [11, 13]])
        self.TOF = np.array([[100, 105], [102, 107]])

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_plot_porkchop_annotation(self):
        # Test with standard 4-tuple (backwards compatibility)
        opt_transfer_4 = (datetime(2025, 1, 1), datetime(2025, 6, 1), 10.0, 100)

        plot_porkchop(
            self.launch_dates,
            self.arrival_dates,
            self.C3,
            self.TOF,
            filename=self.filename,
            optimal_transfer=opt_transfer_4
        )
        self.assertTrue(os.path.exists(self.filename))
        os.remove(self.filename)

    def test_plot_porkchop_annotation_extended(self):
        # Test with 5-tuple (new feature with V_inf)
        opt_transfer_5 = (datetime(2025, 1, 1), datetime(2025, 6, 1), 10.0, 100, 3.5)

        plot_porkchop(
            self.launch_dates,
            self.arrival_dates,
            self.C3,
            self.TOF,
            filename=self.filename,
            optimal_transfer=opt_transfer_5
        )
        self.assertTrue(os.path.exists(self.filename))

    def test_legend_elements(self):
        """Test that the legend contains the expected custom elements."""
        plot_porkchop(
            self.launch_dates,
            self.arrival_dates,
            self.C3,
            self.TOF,
            filename=self.filename
        )

        # Get the current figure and axes
        fig = plt.gcf()
        ax = plt.gca()
        legend = ax.get_legend()

        self.assertIsNotNone(legend, "Legend should exist")
        texts = [t.get_text() for t in legend.get_texts()]

        # Check for our new legend entries
        self.assertIn('$C_3$ Energy (White Contours)', texts)
        self.assertIn('Time of Flight', texts)
        # Optimal transfer is not in this plot call, so check it's NOT there
        self.assertNotIn('Optimal Transfer', texts)

if __name__ == '__main__':
    unittest.main()
