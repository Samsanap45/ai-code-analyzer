import time
import unittest

from tests import _path  # noqa: F401  (adds backend to the import path)
from modules.code_analyzer import analyze_code


PYTHON_CART = '''class ShoppingCart:
    def __init__(self):
        self.items = []

    def add_item(self, name, price, quantity=1):
        """Add an item to the cart."""
        self.items.append({"name": name, "price": price})

    def total(self):
        return sum(i["price"] for i in self.items)


def apply_discount(amount, percent):
    return amount - (amount * percent / 100)


cart = ShoppingCart()
final_price = apply_discount(cart.total(), 10)
'''

JAVA = '''public class Calculator {
    private int total = 0;

    public int add(int a, int b) {
        int result = a + b;
        return result;
    }

    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println(calc.add(1, 2));
    }
}
'''


class PythonTests(unittest.TestCase):
    def test_functions_classes_methods_variables(self):
        r = analyze_code(PYTHON_CART, "Python")
        self.assertEqual(r["total_lines"], 18)
        self.assertEqual(r["classes"], ["ShoppingCart"])
        self.assertEqual(r["functions"], ["__init__", "add_item", "total", "apply_discount"])
        self.assertEqual(r["methods"], {"ShoppingCart": ["__init__", "add_item", "total"]})
        self.assertEqual(r["variables"], ["cart", "final_price"])

    def test_line_numbers(self):
        r = analyze_code(PYTHON_CART, "Python")
        self.assertEqual(r["class_lines"], {"ShoppingCart": [1]})
        self.assertEqual(r["function_lines"]["add_item"], [5])
        self.assertEqual(r["function_lines"]["apply_discount"], [13])

    def test_docstring_content_is_not_code(self):
        code = 'def f():\n    """\n    Example: x = 5\n    """\n    z = 1\n    return z\n'
        r = analyze_code(code, "Python")
        self.assertEqual(r["variables"], ["z"])

    def test_tuple_assignment_finds_every_name(self):
        r = analyze_code("a, b = 1, 2\n", "Python")
        self.assertEqual(r["variables"], ["a", "b"])

    def test_multiline_call_is_one_statement(self):
        code = "result = compute(\n    1,\n    2,\n)\nnext_value = 3\n"
        r = analyze_code(code, "Python")
        self.assertEqual(r["variables"], ["result", "next_value"])


class JavaTests(unittest.TestCase):
    def test_java_class(self):
        r = analyze_code(JAVA, "Java")
        self.assertEqual(r["classes"], ["Calculator"])
        self.assertEqual(r["functions"], ["add", "main"])
        self.assertEqual(r["methods"], {"Calculator": ["add", "main"]})
        self.assertIn("total", r["variables"])
        self.assertIn("result", r["variables"])
        self.assertIn("calc", r["variables"])


class CppTests(unittest.TestCase):
    def test_std_namespace_is_not_a_variable(self):
        code = "#include <string>\nint main() {\n    std::string name = \"x\";\n    return 0;\n}\n"
        r = analyze_code(code, "C++")
        self.assertEqual(r["functions"], ["main"])
        self.assertEqual(r["variables"], ["name"])


class JavaScriptTests(unittest.TestCase):
    def test_html_inside_template_literal_is_not_code(self):
        code = (
            "function render(items) {\n"
            "    const html = `<ul class=\"list\" id=\"main\"><li type=\"a\">${items.length}</li></ul>`;\n"
            "    return html;\n"
            "}\n"
        )
        r = analyze_code(code, "JavaScript")
        self.assertEqual(r["functions"], ["render"])
        self.assertEqual(r["variables"], ["html"])

    def test_regex_with_backtick_does_not_break_the_rest(self):
        code = (
            "const safe = text.replace(/[`*_]/g, \"\");\n"
            "function after() {\n"
            "    const later = 1;\n"
            "}\n"
        )
        r = analyze_code(code, "JavaScript")
        self.assertEqual(r["functions"], ["after"])
        self.assertEqual(r["variables"], ["safe", "later"])

    def test_callback_bodies_are_analysed(self):
        code = "items.forEach(function (item) {\n    const doubled = item * 2;\n});\n"
        r = analyze_code(code, "JavaScript")
        self.assertEqual(r["variables"], ["doubled"])


class LineCountTests(unittest.TestCase):
    def test_windows_and_unix_line_endings_agree(self):
        unix = "x = 1\ny = 2\n"
        windows = "x = 1\r\ny = 2\r\n"
        self.assertEqual(analyze_code(unix, "Python")["total_lines"], 2)
        self.assertEqual(analyze_code(windows, "Python")["total_lines"], 2)


class BigInputTests(unittest.TestCase):
    def test_thousands_of_lines_are_fast(self):
        code = PYTHON_CART * 100          # about 1800 lines
        start = time.time()
        r = analyze_code(code, "Python")
        self.assertLess(time.time() - start, 2.0)
        self.assertEqual(r["total_lines"], 1800)
        self.assertEqual(r["classes"], ["ShoppingCart"])


if __name__ == "__main__":
    unittest.main()