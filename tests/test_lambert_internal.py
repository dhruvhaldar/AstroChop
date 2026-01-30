
import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from lambert import _compute_term_ratio, SQRT2

def reference_term_ratio(z):
    term = np.zeros_like(z, dtype=float)
    ratio = np.zeros_like(z, dtype=float)

    pos = z > 0
    neg = z < 0

    # Positive
    if np.any(pos):
        zp = z[pos]
        sz = np.sqrt(zp)
        sz_2 = sz * 0.5
        sa = np.sin(sz_2)
        ca = np.cos(sz_2)

        term[pos] = -SQRT2 * ca

        # Ratio: (sz - 2*sa*ca) / (2*sqrt(2)*sa^3)
        num = sz - 2 * sa * ca
        den = 2 * SQRT2 * sa**3
        ratio[pos] = num / den

    # Negative
    if np.any(neg):
        zn = -z[neg]
        sz = np.sqrt(zn)
        sz_2 = sz * 0.5
        sa = np.sinh(sz_2)
        ca = np.cosh(sz_2)

        term[neg] = -SQRT2 * ca

        # Ratio: (2*sa*ca - sz) / (2*sqrt(2)*sa^3)
        num = 2 * sa * ca - sz
        den = 2 * SQRT2 * sa**3
        ratio[neg] = num / den

    return term, ratio

class TestLambertInternal(unittest.TestCase):
    def test_term_ratio_large_positive(self):
        # z >= 0.1
        z = np.linspace(0.1, 10.0, 100)

        term_ref, ratio_ref = reference_term_ratio(z)
        term_opt, ratio_opt = _compute_term_ratio(z)

        np.testing.assert_allclose(term_opt, term_ref, rtol=1e-10)
        np.testing.assert_allclose(ratio_opt, ratio_ref, rtol=1e-10)

    def test_term_ratio_large_negative(self):
        # z <= -0.1
        z = np.linspace(-10.0, -0.1, 100)

        term_ref, ratio_ref = reference_term_ratio(z)
        term_opt, ratio_opt = _compute_term_ratio(z)

        np.testing.assert_allclose(term_opt, term_ref, rtol=1e-10)
        np.testing.assert_allclose(ratio_opt, ratio_ref, rtol=1e-10)

    def test_term_ratio_mixed(self):
        # Check specific large values that force "Mixed Regime" (min < -0.1, max > 0.1)
        z_check = np.array([-1.0, 1.0])
        term_ref, ratio_ref = reference_term_ratio(z_check)
        term_opt, ratio_opt = _compute_term_ratio(z_check)

        np.testing.assert_allclose(term_opt, term_ref, rtol=1e-10)
        np.testing.assert_allclose(ratio_opt, ratio_ref, rtol=1e-10)

if __name__ == '__main__':
    unittest.main()
