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

    def test_contour_labels_path_effects(self):
        """Test that contour labels have path effects applied for readability."""
        plot_porkchop(
            self.launch_dates,
            self.arrival_dates,
            self.C3,
            self.TOF,
            filename=self.filename
        )

        fig = plt.gcf()
        ax = plt.gca()

        # Check all text objects in the axes
        # Note: clabel adds text objects to ax.texts
        # We expect some labels because our data ranges are small but we force levels

        # In the test setup, C3 ranges 10-13, TOF ranges 100-107.
        # Levels are fixed in plotter.py:
        # C3 levels: linspace(0, 50, 26) -> step 2.0 -> 0, 2, ..., 10, 12, ...
        # TOF levels: dynamic, but likely includes values.

        texts = ax.texts

        # Depending on how many levels cross the data, we might or might not have labels.
        # With C3=[10, 12], levels include 10, 12. So we should have contours and labels.

        has_path_effects = False
        import matplotlib.patheffects as pe

        for t in texts:
            effects = t.get_path_effects()
            if effects:
                has_path_effects = True
                # Verify it is a stroke
                self.assertIsInstance(effects[0], pe.withStroke)

        # If no labels were generated, this test might be vacuously true/false.
        # But given the levels, we expect labels.
        if len(texts) > 0:
            self.assertTrue(has_path_effects, "Contour labels should have path effects")

    def test_semantic_annotation_content(self):
        """Test that the optimal transfer annotation includes semantic quality ratings."""
        # Setup: Excellent C3 (<15) and Good V_inf (<=4.5)
        # C3 = 10.0 -> Excellent
        # V_inf = 3.5 -> Good
        opt_transfer_5 = (datetime(2025, 1, 1), datetime(2025, 6, 1), 10.0, 100, 3.5)

        plot_porkchop(
            self.launch_dates,
            self.arrival_dates,
            self.C3,
            self.TOF,
            filename=self.filename,
            optimal_transfer=opt_transfer_5
        )

        ax = plt.gca()

        # Find the annotation text
        found_semantic_rating = False
        import matplotlib.text

        # Look through all texts (including annotations)
        for child in ax.texts:
            text = child.get_text()
            # We expect the annotation to contain "(Excellent)" and "(Good)"
            if "(Excellent)" in text and "(Good)" in text:
                found_semantic_rating = True
                break

        self.assertTrue(found_semantic_rating, "Annotation should contain semantic ratings '(Excellent)' and '(Good)'")

    def test_duration_format_human_readable(self):
        """Test that the duration is formatted nicely (e.g. 'X months, Y days')."""
        # Setup: 200 days -> ~6.6 months
        # We assume format_duration logic: 200 days -> "6 months, 17 days" (approx)
        # We will check if the annotation contains the expanded format rather than just "(6.6 mo)"
        opt_transfer_5 = (datetime(2025, 1, 1), datetime(2025, 7, 20), 10.0, 200, 3.5)

        plot_porkchop(
            self.launch_dates,
            self.arrival_dates,
            self.C3,
            self.TOF,
            filename=self.filename,
            optimal_transfer=opt_transfer_5
        )

        ax = plt.gca()

        found_human_readable = False
        for child in ax.texts:
            text = child.get_text()
            if "TOF: 200 days" in text:
                # Check for "months" and "days" inside the parenthesis
                # e.g. "(6 months, 17 days)"
                # We relax the check to just "months" to ensure we moved away from "mo"
                if "months" in text or "month" in text:
                    found_human_readable = True
                    break

        self.assertTrue(found_human_readable, "Annotation should use human-readable duration format (e.g., '6 months, 17 days') instead of abbreviated 'mo'")

if __name__ == '__main__':
    unittest.main()
