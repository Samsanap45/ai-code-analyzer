import re

# How each language writes comments and prints output
COMMENT_MARKERS = {
    "Python": ("#",),
    "Java": ("//", "/*"),
    "C++": ("//", "/*"),
    "C": ("//", "/*"),
    "JavaScript": ("//", "/*"),
}

# Used when the language is Unknown: accept any style
ANY_COMMENT = ("#", "//", "/*")

PRINT_PATTERNS = {
    "Python": (r"\bprint\(",),
    "Java": (r"System\.out\.print",),
    "C++": (r"std::cout\b", r"\bcout\s*<<"),
    "C": (r"\bprintf\(",),
    "JavaScript": (r"\bconsole\.log\(",),
}

ALL_PRINT_PATTERNS = tuple(p for group in PRINT_PATTERNS.values() for p in group)

LONG_LINE_LIMIT = 100
MAX_LONG_LINES_LISTED = 5


def _remove_strings(line):
    """Empty the text inside quotes so markers in strings are ignored."""
    line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    return re.sub(r"'(?:\\.|[^'\\])*'", "''", line)


def _split_comment(line, markers):
    """Return (code_part, has_comment) for one line."""
    cleaned = _remove_strings(line)
    cut = None

    for marker in markers:
        position = cleaned.find(marker)

        if position != -1 and (cut is None or position < cut):
            cut = position

    if cut is not None:
        return cleaned[:cut], True

    return cleaned, False


def _preview(line, limit=60):
    """The start of a line, short enough to show in a message."""
    text = line.strip()

    if len(text) <= limit:
        return text

    return text[:limit].rstrip() + "..."


def _line_list(numbers, limit=5):
    """"3, 18, 40" - or "3, 18, 40, 52, 60 and 2 more" for long lists."""
    shown = ", ".join(str(number) for number in numbers[:limit])

    if len(numbers) > limit:
        shown += f" and {len(numbers) - limit} more"

    return shown


def _is_block_comment_line(stripped):
    """A line like "* text" or "*/" inside a /* ... */ block (not "*p = 5")."""
    return bool(re.match(r"^\*(?:\s|/|$)", stripped))


def check_code_quality(code, language=None):

    issues = []
    suggestions = []

    # Split exactly like the editor does, so "Line 42" matches the screen
    lines = code.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Check for empty code
    if not code.strip():
        issues.append("Code is empty.")

    # Check line length (list the first few, then count the rest)
    long_lines = [
        number for number, line in enumerate(lines, start=1)
        if len(line) > LONG_LINE_LIMIT
    ]

    for line_number in long_lines[:MAX_LONG_LINES_LISTED]:
        line = lines[line_number - 1]
        issues.append(
            f"Line {line_number} is {len(line)} characters long "
            f"(limit {LONG_LINE_LIMIT}): \"{_preview(line)}\""
        )

    if len(long_lines) > MAX_LONG_LINES_LISTED:
        hidden = len(long_lines) - MAX_LONG_LINES_LISTED
        issues.append(
            f"...and {hidden} more lines longer than "
            f"{LONG_LINE_LIMIT} characters."
        )

    # Check comments (using the comment style of the detected language)
    markers = COMMENT_MARKERS.get(language, ANY_COMMENT)

    has_comment = False
    code_without_comments = []

    for line in lines:
        stripped = line.strip()

        if language != "Python" and _is_block_comment_line(stripped):
            has_comment = True
            code_without_comments.append("")
            continue

        code_part, found = _split_comment(line, markers)

        if found:
            has_comment = True

        code_without_comments.append(code_part)

    # Python docstrings count as documentation too
    if language in ("Python", None) and ('"""' in code or "\'\'\'" in code):
        has_comment = True

    if not has_comment:
        suggestions.append(
            "Consider adding comments to explain important parts of the code."
        )

    # Check print / debug output (ignoring comments and text inside strings)
    patterns = PRINT_PATTERNS.get(language, ALL_PRINT_PATTERNS)

    print_lines = [
        number for number, code_part in enumerate(code_without_comments, start=1)
        if any(re.search(pattern, code_part) for pattern in patterns)
    ]

    if print_lines:
        where = "line" if len(print_lines) == 1 else "lines"
        suggestions.append(
            "Avoid unnecessary print statements in production code "
            f"(on {where} {_line_list(print_lines)})."
        )

    # Check TODO/FIXME
    todo_lines = [
        number for number, line in enumerate(lines, start=1)
        if re.search(r"\b(TODO|FIXME)\b", line)
    ]

    for line_number in todo_lines[:MAX_LONG_LINES_LISTED]:
        issues.append(
            f"TODO or FIXME on line {line_number}: "
            f"\"{_preview(lines[line_number - 1])}\""
        )

    if len(todo_lines) > MAX_LONG_LINES_LISTED:
        hidden = len(todo_lines) - MAX_LONG_LINES_LISTED
        issues.append(f"...and {hidden} more TODO or FIXME comments.")

    return {
        "issues": issues,
        "suggestions": suggestions
    }


# Test the module
if __name__ == "__main__":

    sample_code = """def calculate(a, b):
    result = a + b
    print(result)
    return result
"""

    result = check_code_quality(sample_code, "Python")

    print("\n========== CODE QUALITY ==========")

    print("\nIssues:")

    if result["issues"]:
        for issue in result["issues"]:
            print("-", issue)
    else:
        print("- No major issues detected.")

    print("\nSuggestions:")

    if result["suggestions"]:
        for suggestion in result["suggestions"]:
            print("-", suggestion)
    else:
        print("- No suggestions.")