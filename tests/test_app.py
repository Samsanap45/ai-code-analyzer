import os
import unittest

from tests import _path  # noqa: F401
import app as app_module


class AnalyzeEndpointTests(unittest.TestCase):
    def setUp(self):
        # Never call the real AI in tests
        self._saved_key = os.environ.pop("GEMINI_API_KEY", None)
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def tearDown(self):
        if self._saved_key is not None:
            os.environ["GEMINI_API_KEY"] = self._saved_key

    def post(self, payload):
        return self.client.post("/analyze", json=payload)

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"languageSelect", response.data)

    def test_empty_code_is_rejected(self):
        response = self.post({"code": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_missing_code_is_rejected(self):
        self.assertEqual(self.post({}).status_code, 400)

    def test_non_json_body_is_rejected(self):
        response = self.client.post("/analyze", data="hello", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    def test_code_must_be_text(self):
        self.assertEqual(self.post({"code": 123}).status_code, 400)

    def test_python_code_is_analysed(self):
        data = self.post({"code": "def add(a, b):\n    total = a + b\n    return total\n"}).get_json()
        self.assertEqual(data["language"], "Python")
        self.assertEqual(data["analysis"]["total_lines"], 3)
        self.assertEqual(data["analysis"]["functions"], ["add"])
        self.assertEqual(data["analysis"]["variables"], ["total"])
        self.assertEqual(data["analysis"]["function_lines"], {"add": [1]})
        self.assertIn("issues", data["quality"])

    def test_without_api_key_template_docs_and_a_note(self):
        data = self.post({"code": "x = 1\n"}).get_json()
        self.assertEqual(data["doc_source"], "template")
        self.assertIn("no API key", data["ai_note"])
        self.assertTrue(data["documentation"])

    def test_chosen_language_overrides_detection(self):
        code = "int add(int a, int b) { return a + b; }\n"
        data = self.post({"code": code, "language": "C"}).get_json()
        self.assertEqual(data["language"], "C")

    def test_unknown_language_choice_falls_back_to_detection(self):
        data = self.post({"code": "def f():\n    pass\n", "language": "Klingon"}).get_json()
        self.assertEqual(data["language"], "Python")

    def test_too_large_request_gets_a_clear_message(self):
        response = self.post({"code": "x = 1\n" * 1_100_000})   # about 6.6 MB
        self.assertEqual(response.status_code, 413)
        self.assertIn("too large", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()