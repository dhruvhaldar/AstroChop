import unittest
import numpy as np
from src.lambert import lambert, stumpff_c, stumpff_s

class TestLambert(unittest.TestCase):
    def test_stumpff(self):
        self.assertAlmostEqual(stumpff_c(0), 0.5)
        self.assertAlmostEqual(stumpff_s(0), 1.0/6.0)
        
    def test_lambert_basic(self):
        # Test case: 90 deg transfer in circular orbit
        # r1 = [R, 0, 0], r2 = [0, R, 0]
        # dt = period / 4
        # Period = 2*pi * sqrt(R^3/mu)
        # dt = pi/2 * sqrt(R^3/mu)
        
        R = 1.0e8 # km
        mu = 1.0e11 # km^3/s^2
        
        r1 = np.array([R, 0, 0])
        r2 = np.array([0, R, 0])
        
        dt = np.pi/2 * np.sqrt(R**3/mu)
        
        v1, v2 = lambert(r1, r2, dt, mu)
        
        # Expected velocity for circular orbit: v = sqrt(mu/R)
        v_circ = np.sqrt(mu/R)
        
        # v1 should be [0, v_circ, 0] (prograde)
        # v2 should be [-v_circ, 0, 0]
        
        np.testing.assert_allclose(v1, [0, v_circ, 0], atol=1e-3)
        np.testing.assert_allclose(v2, [-v_circ, 0, 0], atol=1e-3)

if __name__ == '__main__':
    unittest.main()
