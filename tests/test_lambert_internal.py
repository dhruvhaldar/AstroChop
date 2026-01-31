import unittest
import numpy as np
from src.lambert import _compute_term_ratio

class TestLambertInternal(unittest.TestCase):
    def test_mixed_regime(self):
        # Create input covering all regimes
        # Large Pos (> 0.1), Large Neg (< -0.1), Small (in between)
        z = np.array([1.0, 0.5, 0.1, 0.05, 0.0, -0.05, -0.1, -0.5, -1.0])

        term, ratio = _compute_term_ratio(z)

        # Check output validity
        self.assertEqual(term.shape, z.shape)
        self.assertEqual(ratio.shape, z.shape)
        self.assertFalse(np.any(np.isnan(term)))
        self.assertFalse(np.any(np.isnan(ratio)))

        # Compare with known logic (or just consistency)
        # We can compare individual calls vs batched call
        for i in range(len(z)):
            t_i, r_i = _compute_term_ratio(np.array([z[i]]))
            self.assertAlmostEqual(term[i], t_i[0], msg=f"Term mismatch at index {i} (z={z[i]})")
            self.assertAlmostEqual(ratio[i], r_i[0], msg=f"Ratio mismatch at index {i} (z={z[i]})")

if __name__ == '__main__':
    unittest.main()
