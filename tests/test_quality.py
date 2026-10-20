import unittest

from tests import _path  # noqa: F401
from modules.code_quality import check_code_quality


class QualityTests(unittest.TestCase):
    def test_clean_code_has_no_issues(self):
        r = check_code_quality("x = 1\ny = 2\n", "Python")
        self.assertEqual(r["issues"], [])

    def test_long_line_reports_number_and_length(self):
        code = "x = 1\n" + "y = '" + "a" * 120 + "'\n"
        r = check_code_quality(code, "Python")
        self.assertTrue(any(i.startswith("Line 2 is 126 characters long (limit 100)") for i in r["issues"]), r["issues"])

    def test_line_of_exactly_100_is_fine(self):
        r = check_code_quality("x = '" + "a" * 94 + "'\n", "Python")   # 100 characters
        self.assertFalse(any("characters long" in i for i in r["issues"]))

    def test_todo_is_reported_with_its_line(self):
        r = check_code_quality("x = 1\n# TODO: fix this\n", "Python")
        self.assertTrue(any("TODO" in i and "line 2" in i for i in r["issues"]), r["issues"])

    def test_print_statements_get_a_suggestion(self):
        r = check_code_quality("print('hello')\n", "Python")
        self.assertTrue(any("print" in s.lower() for s in r["suggestions"]), r["suggestions"])

    def test_many_long_lines_are_summarised(self):
        code = "".join("v%d = '%s'\n" % (n, "a" * 120) for n in range(10))
        r = check_code_quality(code, "Python")
        self.assertTrue(any("more lines longer than 100" in i for i in r["issues"]), r["issues"])
        self.assertLessEqual(len(r["issues"]), 7)


if __name__ == "__main__":
    unittest.main()