import unittest
from cli_utils import format_duration, get_c3_rating, get_vinf_rating, Style

class TestCliUx(unittest.TestCase):
    def test_format_duration_days_only(self):
        # Less than 30 days -> just days
        self.assertEqual(format_duration(5.5), "5.5 days")
        self.assertEqual(format_duration(29.0), "29.0 days")

    def test_format_duration_months(self):
        # Approx 30.44 days per month
        # 45 days -> ~1.5 months -> "1 month, 15 days"
        # Let's see how we want to implement it.
        # Maybe just "1.5 months (45 days)" is fine, but "1 month, 15 days" is friendlier.
        # Let's stick to the plan: "1 month, 15 days"
        self.assertEqual(format_duration(45), "1 month, 15 days")
        self.assertEqual(format_duration(65), "2 months, 4 days")

    def test_format_duration_years(self):
        # > 365 days
        self.assertEqual(format_duration(400), "1 year, 1 month")
        self.assertEqual(format_duration(750), "2 years, 1 month")

    def test_get_c3_rating(self):
        # Excellent < 15
        self.assertEqual(get_c3_rating(10.0), (Style.GREEN, "(Excellent)"))
        # Good < 20
        self.assertEqual(get_c3_rating(18.0), (Style.GREEN, "(Good)"))
        # Acceptable < 30
        self.assertEqual(get_c3_rating(25.0), (Style.YELLOW, "(Acceptable)"))
        # High >= 30
        self.assertEqual(get_c3_rating(35.0), (Style.RED, "(High Energy)"))

    def test_get_vinf_rating(self):
        # Excellent < 4.5
        self.assertEqual(get_vinf_rating(3.0), (Style.GREEN, "(Excellent)"))
        # Manageable <= 6.0
        self.assertEqual(get_vinf_rating(5.5), (Style.YELLOW, "(Manageable)"))
        # High > 6.0
        self.assertEqual(get_vinf_rating(7.0), (Style.RED, "(High)"))
