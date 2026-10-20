import unittest

from tests import _path  # noqa: F401
from modules.language_detector import detect_language


class DetectorTests(unittest.TestCase):
    def test_python(self):
        self.assertEqual(detect_language("def add(a, b):\n    return a + b\n"), "Python")

    def test_python_class(self):
        self.assertEqual(detect_language("class A:\n    pass\n"), "Python")

    def test_java(self):
        code = "public class A {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}\n"
        self.assertEqual(detect_language(code), "Java")

    def test_cpp(self):
        code = "#include <iostream>\nint main() {\n    std::cout << 1;\n    return 0;\n}\n"
        self.assertEqual(detect_language(code), "C++")

    def test_c(self):
        code = "#include <stdio.h>\nint main() {\n    printf(\"hi\");\n    return 0;\n}\n"
        self.assertEqual(detect_language(code), "C")

    def test_javascript(self):
        self.assertEqual(detect_language("const x = 1;\nconsole.log(x);\nfunction f() { return x; }\n"), "JavaScript")


if __name__ == "__main__":
    unittest.main()