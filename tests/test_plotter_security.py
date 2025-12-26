import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from plotter import generate_porkchop
import plotter

class TestPlotterSecurity(unittest.TestCase):
    def test_dos_prevention_grid_size_limit(self):
        """
        Test that generate_porkchop raises ValueError if the requested grid size
        exceeds the configured maximum, preventing memory exhaustion (DoS).
        """
        # Create dummy dates
        # We want to trigger the limit.
        # We will patch the limit to be small for testing purposes.

        # 11 launch dates
        start_launch = datetime(2020, 1, 1)
        launch_dates = [start_launch + timedelta(days=i) for i in range(11)]

        # 10 arrival dates
        start_arrival = datetime(2020, 6, 1)
        arrival_dates = [start_arrival + timedelta(days=i) for i in range(10)]

        # Total = 110 points.

        # Patch the MAX_GRID_SIZE to 100
        # Note: We must patch 'plotter.MAX_GRID_SIZE' where it is defined.
        # Since it is not defined yet, this test serves as TDD.
        # Once defined, this patch will work.
        # For now, if we run this before defining it, it might raise AttributeError during patch application
        # or fail the assertion if we don't patch and it uses default (infinity).

        # To handle the "before fix" state gracefully in a TDD workflow:
        # We expect the attribute might not exist yet.

        try:
            with patch('plotter.MAX_GRID_SIZE', 100, create=True):
                # If the code doesn't check it, it won't raise.
                with self.assertRaises(ValueError) as cm:
                    generate_porkchop(launch_dates, arrival_dates)

                self.assertIn("Grid size too large", str(cm.exception))
        except AttributeError:
             # If the code doesn't use the variable, the patch might work (create=True),
             # but the function won't raise.
             pass
        except AssertionError:
             # Code didn't raise ValueError
             print("Security check missing: generate_porkchop did not raise ValueError for oversized grid.")
             # We want this to fail initially
             raise

if __name__ == '__main__':
    unittest.main()
