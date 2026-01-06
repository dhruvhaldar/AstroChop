import unittest
import numpy as np
from src.ephemeris import get_ephemeris

class TestEphemerisVectorized(unittest.TestCase):
    def test_vectorized_ephemeris_earth(self):
        # Create a range of dates
        jd_start = 2451545.0
        jd_arr = np.linspace(jd_start, jd_start + 100, 50)

        # Vectorized call
        r_vec, v_vec = get_ephemeris('earth', jd_arr)

        # Check shapes
        self.assertEqual(r_vec.shape, (3, 50))
        self.assertEqual(v_vec.shape, (3, 50))

        # Check against scalar calls
        for i, jd in enumerate(jd_arr):
            r_scalar, v_scalar = get_ephemeris('earth', jd)
            np.testing.assert_allclose(r_vec[:, i], r_scalar, rtol=1e-12)
            np.testing.assert_allclose(v_vec[:, i], v_scalar, rtol=1e-12)

    def test_vectorized_ephemeris_mars(self):
        # Create a range of dates
        jd_start = 2451545.0
        jd_arr = np.linspace(jd_start, jd_start + 200, 50)

        # Vectorized call
        r_vec, v_vec = get_ephemeris('mars', jd_arr)

        # Check shapes
        self.assertEqual(r_vec.shape, (3, 50))
        self.assertEqual(v_vec.shape, (3, 50))

        # Check against scalar calls
        for i, jd in enumerate(jd_arr):
            r_scalar, v_scalar = get_ephemeris('mars', jd)
            np.testing.assert_allclose(r_vec[:, i], r_scalar, rtol=1e-12)
            np.testing.assert_allclose(v_vec[:, i], v_scalar, rtol=1e-12)

    def test_scalar_still_works(self):
        jd = 2451545.0
        r, v = get_ephemeris('earth', jd)
        self.assertEqual(r.shape, (3,))
        self.assertEqual(v.shape, (3,))

if __name__ == '__main__':
    unittest.main()
