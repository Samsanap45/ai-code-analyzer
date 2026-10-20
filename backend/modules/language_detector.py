import re


# Lines that only Python writes: "def name(...):" and "class Name(...):"
# (they end with a colon, while Java / C / C++ / JavaScript use "{")
PYTHON_STRONG = re.compile(
    r"^\s*(?:async\s+)?def\s+\w+\s*\(.*\)\s*(?:->\s*[^:]+)?:\s*$"
    r"|^\s*class\s+\w+\s*(?:\([^)]*\))?\s*:\s*$",
    re.MULTILINE
)


def detect_language(code):

    # Python first when it has a clear Python-only line, so a Python file
    # that merely mentions "std::" or "printf(" in a string or comment
    # is not mistaken for C or C++
    if PYTHON_STRONG.search(code):
        return "Python"

    # Java (checked first: Java files also contain "import " lines)
    if (
        "public class " in code
        or "public static void main" in code
        or "System.out.print" in code
        or re.search(r"^\s*import\s+java\.", code, re.MULTILINE)
    ):
        return "Java"

    # C++
    if (
        "#include <iostream>" in code
        or "using namespace std" in code
        or "std::" in code
    ):
        return "C++"

    # C
    if "#include <stdio.h>" in code or "printf(" in code:
        return "C"

    # Python (clear Python markers, checked before JavaScript so that a
    # Python comment containing the word "function" is not misread)
    if re.search(r"^\s*(async\s+)?def\s+\w+\s*\(", code, re.MULTILINE):
        return "Python"

    # JavaScript
    if (
        "console.log(" in code
        or re.search(r"\bfunction\s*\w*\s*\(", code)
        or "=>" in code
        or re.search(r"^\s*(const|let)\s+\w+\s*=", code, re.MULTILINE)
    ):
        return "JavaScript"

    # Python (looser markers)
    if "import " in code or "print(" in code:
        return "Python"

    return "Unknown"