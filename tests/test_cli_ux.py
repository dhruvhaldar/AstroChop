import unittest
from cli_utils import format_duration, get_c3_color, get_c3_rating, get_vinf_rating, Style

class TestCliUx(unittest.TestCase):
    def test_format_duration_days_only(self):
        # Less than 30 days -> just days
        self.assertEqual(format_duration(5.5), "5.5 days")
        self.assertEqual(format_duration(29.0), "29.0 days")

    def test_format_duration_months(self):
        # Approx 30.44 days per month
        # 45 days -> ~1.5 months -> "1 month, 15 days"
        self.assertEqual(format_duration(45), "1 month, 15 days")
        self.assertEqual(format_duration(65), "2 months, 4 days")

    def test_format_duration_years(self):
        # > 365 days
        self.assertEqual(format_duration(400), "1 year, 1 month")
        self.assertEqual(format_duration(750), "2 years, 1 month")

    def test_get_c3_color(self):
        # Excellent < 15
        self.assertEqual(get_c3_color(10.0), Style.GREEN)
        # Good < 20
        self.assertEqual(get_c3_color(18.0), Style.GREEN)
        # Acceptable < 30
        self.assertEqual(get_c3_color(25.0), Style.YELLOW)
        # High >= 30
        self.assertEqual(get_c3_color(35.0), Style.RED)

    def test_get_c3_rating(self):
        # < 15 Excellent
        self.assertEqual(get_c3_rating(10.0), (Style.GREEN, "(Excellent)"))
        # <= 20 Good
        self.assertEqual(get_c3_rating(18.0), (Style.GREEN, "(Good)"))
        # <= 30 Acceptable
        self.assertEqual(get_c3_rating(25.0), (Style.YELLOW, "(Acceptable)"))
        # > 30 High
        self.assertEqual(get_c3_rating(35.0), (Style.RED, "(High Energy)"))

    def test_get_vinf_rating(self):
        # <= 4.5 Good
        self.assertEqual(get_vinf_rating(3.0), (Style.GREEN, "(Good)"))
        self.assertEqual(get_vinf_rating(4.5), (Style.GREEN, "(Good)"))
        # <= 6.0 Acceptable
        self.assertEqual(get_vinf_rating(5.5), (Style.YELLOW, "(Acceptable)"))
        # > 6.0 High
        self.assertEqual(get_vinf_rating(7.0), (Style.RED, "(High)"))
