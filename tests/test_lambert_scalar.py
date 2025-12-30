
import unittest
import numpy as np
from lambert import lambert, stumpff_c_s

class TestLambertScalar(unittest.TestCase):
    def test_scalar_input(self):
        r1 = np.array([1.5e8, 0, 0])
        r2 = np.array([0, 1.5e8, 0])
        dt = 100 * 86400
        mu = 1.327e11

        # This calls lambert with 1D arrays (single vectors)
        # Internally it should handle it.
        v1, v2 = lambert(r1, r2, dt, mu)

        self.assertTrue(np.all(np.isfinite(v1)))
        self.assertTrue(np.all(np.isfinite(v2)))
        self.assertEqual(v1.shape, (3,))

    def test_scalar_denom_zero(self):
        # Case where denom becomes 0 (identical points)
        # r1 = r2, dt small?
        r1 = np.array([1.5e8, 0, 0])
        r2 = np.array([1.5e8, 0, 0])
        dt = 100
        mu = 1.327e11

        # dnu = 0 -> denom = 1 - 1 = 0
        # This should trigger the zero handling
        try:
            v1, v2 = lambert(r1, r2, dt, mu)
        except Exception as e:
            self.fail(f"Scalar zero denom failed: {e}")

if __name__ == '__main__':
    unittest.main()
