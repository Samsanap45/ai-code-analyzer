import re


# Words that look like function names but are really statements
CONTROL_WORDS = {
    "if", "for", "while", "switch", "catch", "return", "new", "else",
    "do", "try", "finally", "throw", "case", "default", "sizeof",
    "typeof", "await", "yield", "delete", "synchronized"
}

# Lines starting with these are statements, not declarations
STATEMENT_STARTS = (
    "return ", "return(", "else ", "elif ", "raise ", "yield ",
    "await ", "print ", "new ", "throw "
)

# Lines starting with these are not variable assignments
NOT_ASSIGNMENT_STARTS = (
    "#", "//", "==", "if ", "elif ", "while ", "for ",
    "return ", "assert ", "with "
)

MODIFIERS = (
    r"(?:@\w+(?:\([^)]*\))?\s+)*"
    r"(?:(?:public|private|protected|static|final|abstract|"
    r"synchronized|native|virtual|inline|extern|constexpr|friend|"
    r"override|async|export|default)\s+)*"
)

# Words that can come before a type:  const char*, unsigned int ...
TYPE_PREFIX = r"(?:(?:const|unsigned|signed|long|short|struct|enum|volatile)\s+)*"

# A type name, optionally with generic arguments:  Map<String, Integer>
TYPE = r"[\w:.?*&$]+(?:<[^()=;]*>)?[\w\[\]*&?]*"

# Generic parameters before a return type:  <T extends Comparable<T>> T
GENERIC_PARAMS = r"(?:<[^()]*>\s+)?"

PYTHON_DEF = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
PYTHON_CLASS = re.compile(r"^class\s+([A-Za-z_]\w*)")

BRACE_CLASS = re.compile(
    r"^" + MODIFIERS + r"(?:class|interface)\s+([A-Za-z_$]\w*)"
)

# Java / C / C++ style: optional modifiers, a return type, then the name
TYPED_METHOD = re.compile(
    r"^" + MODIFIERS + GENERIC_PARAMS + TYPE_PREFIX + TYPE + r"\s+"
    r"([A-Za-z_]\w*)\s*\([^;]*\)\s*"
    r"(?:const\s*)?(?:throws\s+[\w., ]+)?\s*(?:\{[^{}]*\}|\{)?\s*$"
)

# JavaScript style functions
JS_FUNCTION = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*"
    r"([A-Za-z_$]\w*)\s*\("
)
JS_ARROW = re.compile(
    r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$]\w*)\s*=\s*"
    r"(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$]\w*\s*=>)"
)

# Method without a return type (JS methods, constructors), only used
# when the line sits directly inside a class body
UNTYPED_METHOD = re.compile(
    r"^(?:(?:static|async|get|set|public|private|protected)\s+)*"
    r"([A-Za-z_$#]\w*)\s*\([^)]*\)\s*(?:\{[^{}]*\}|\{)?\s*$"
)

BRACE_LANGUAGES = {"Java", "C++", "C", "JavaScript"}


# Characters that, just before "=", make it part of another operator
# (==, !=, <=, >=, +=, -=, :=, ...) instead of a plain assignment
_NOT_PLAIN_ASSIGN = set("=!<>+-*/%&|^:@~")

_DECL_WORDS = re.compile(
    r"^(?:(?:public|private|protected|static|final|transient|"
    r"const|volatile|let|var)\s+)+"
)

_IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")

_NOT_A_TYPE = {
    "lambda", "return", "yield", "await", "del", "global", "nonlocal",
    "assert", "raise", "print", "not", "in", "is", "and", "or", "else",
    "elif", "import", "from", "with", "as", "case", "throw", "new"
}


def _split_assignments(line, comment_style):
    """Split a line at its top-level "=" signs.

    "=" inside brackets, strings or comments is ignored, and so are
    ==, !=, <=, >=, +=, => and similar operators.
    """
    parts, current = [], []
    depth = 0
    quote = None
    i = 0

    while i < len(line):
        ch = line[i]

        if quote:
            current.append(ch)

            if ch == "\\" and i + 1 < len(line):
                current.append(line[i + 1])
                i += 2
                continue

            if ch == quote:
                quote = None

        elif ch in "\"'":
            quote = ch
            current.append(ch)

        elif comment_style == "python" and ch == "#":
            break

        elif comment_style != "python" and line[i:i + 2] == "//":
            break

        elif ch in "([{":
            depth += 1
            current.append(ch)

        elif ch in ")]}":
            depth = max(depth - 1, 0)
            current.append(ch)

        elif ch == "=" and depth == 0:
            before = line[i - 1] if i > 0 else ""
            after = line[i + 1] if i + 1 < len(line) else ""

            if after in ("=", ">") or before in _NOT_PLAIN_ASSIGN:
                current.append(ch)
            else:
                parts.append("".join(current))
                current = []

        else:
            current.append(ch)

        i += 1

    parts.append("".join(current))
    return parts


def _clean_element(element):
    """One item of a tuple / destructuring pattern -> a plain name or None."""
    element = element.strip().lstrip("*").lstrip(".").strip()
    element = element.split("=")[0].strip()      # default value:  {a = 1}

    if ":" in element:                           # rename:  {a: b}
        element = element.split(":")[-1].strip()

    return element if _IDENT.match(element) else None


def _target_names(target):
    """Variable names created by the left-hand side of an assignment."""

    target = target.strip()

    # Drop leading words such as const / let / var / final / static
    target = _DECL_WORDS.sub("", target).strip()

    if not target:
        return []

    # Plain name:  x = 5
    if _IDENT.match(target):
        return [target]

    # Destructuring / tuple in brackets:  (a, b) = ...   let [p, q] = ...
    # also C++ structured bindings:  auto [a, b] = ...
    wrapped = re.match(
        r"^(?:(?:const\s+)?auto\s*&{0,2}\s*)?[\[({](.+)[\])}]$",
        target
    )

    if wrapped:
        names = [_clean_element(e) for e in wrapped.group(1).split(",")]
        return [n for n in names if n]

    # Bare Python tuple:  a, b = ...    first, *rest = ...
    if "," in target and not any(c in target for c in "<>():[]{}"):
        names = [_clean_element(e) for e in target.split(",")]

        if all(names):
            return names

        return []

    # Python type hint:  x: int = 5   (but not the C++ scope operator ::)
    hinted = re.match(r"^([A-Za-z_]\w*)\s*:(?!:)\s*[^=]+$", target)

    if hinted:
        return [hinted.group(1)]

    # Words that can never be a type ("lambda q=1" is not a declaration)
    if target.split()[0] in _NOT_A_TYPE:
        return []

    # Java / C / C++ declaration:  int x,  int *p,  int a[3],  Map<K, V> m
    declaration = re.match(
        r"^" + TYPE_PREFIX + TYPE + r"[\s*&]+([A-Za-z_$][\w$]*)"
        r"(?:\s*\[[^\]]*\])*\s*$",
        target
    )

    if declaration:
        return [declaration.group(1)]

    return []


def _find_variables(line, comment_style="python"):
    """Return the names of the variables assigned on this line."""

    if "=" not in line or line.startswith(NOT_ASSIGNMENT_STARTS):
        return []

    parts = _split_assignments(line, comment_style)

    if len(parts) < 2:
        return []

    separator = r";" if comment_style == "python" else r"[;,]"
    names = []

    # Everything before the last "=" is a target:  a = b = 0  -> a and b
    for index, target in enumerate(parts[:-1]):

        # After the first "=", the text holds the previous value and then
        # the next declarator:  int x = 1, y = 2;  ->  "1, y"
        if index > 0:
            target = re.split(separator, target)[-1]

        names.extend(_target_names(target))

    return names


def _clean_for_braces(line):
    """Remove strings and line comments so their braces are not counted."""
    line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    line = re.sub(r"'(?:\\.|[^'\\])*'", "''", line)
    line = re.sub(r"//.*$", "", line)
    return line


def _regex_end(line, start):
    """Index just after the regex literal that starts at line[start], or start."""
    j = start + 1
    in_class = False

    while j < len(line):
        c = line[j]

        if c == "\\":
            j += 2
            continue

        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            j += 1

            while j < len(line) and line[j].isalpha():
                j += 1                      # flags: g, i, m ...

            return j

        j += 1

    return start


def _starts_regex(line, i):
    """True if the "/" at line[i] begins a regex literal (not division or a comment)."""
    if line[i + 1:i + 2] in ("/", "*", ""):
        return False

    before = line[:i].rstrip()

    if before and before[-1] not in "(,=:[!&|?{};":
        return False

    return _regex_end(line, i) != i


def _strip_template_literals(lines):
    """Blank out JavaScript template literals (`...`), keeping line numbers.

    Their text (often HTML such as  id="x"  or  class="y") is not code, so it
    must not be read as variables, and their { } must not count as scopes.
    Each literal is replaced by "" and everything inside it is removed.
    """
    result = []
    stack = []              # "T" = inside template text, number = ${ } depth
    in_block_comment = False

    for line in lines:
        out = []
        quote = None
        i = 0

        while i < len(line):
            ch = line[i]
            top = stack[-1] if stack else None

            # Inside the text of a template literal
            if top == "T":
                if ch == "\\":
                    i += 2
                    continue

                if ch == "`":
                    stack.pop()
                elif line[i:i + 2] == "${":
                    stack.append(0)
                    i += 2
                    continue

                i += 1
                continue

            # Code: top level, or inside ${ ... } of a template literal
            if in_block_comment:
                if line[i:i + 2] == "*/":
                    in_block_comment = False

                    if not stack:
                        out.append("*/")

                    i += 2
                    continue

            elif quote:
                if ch == "\\":
                    if not stack:
                        out.append(line[i:i + 2])

                    i += 2
                    continue

                if ch == quote:
                    quote = None

            elif line[i:i + 2] == "//":
                if not stack:
                    out.append(line[i:])

                break

            elif line[i:i + 2] == "/*":
                in_block_comment = True

                if not stack:
                    out.append("/*")

                i += 2
                continue

            elif ch == "/" and _starts_regex(line, i):
                # A regex literal such as  /([\\`*_])/g  - copy it as it is,
                # so a backtick inside it is not taken for a template start
                end = _regex_end(line, i)

                if not stack:
                    out.append(line[i:end])

                i = end
                continue

            elif ch in "\"'":
                quote = ch

            elif ch == "`":
                if not stack:
                    out.append('""')

                stack.append("T")
                i += 1
                continue

            elif isinstance(top, int):
                if ch == "{":
                    stack[-1] = top + 1
                elif ch == "}":
                    if top == 0:
                        stack.pop()
                        i += 1
                        continue

                    stack[-1] = top - 1

            if not stack:
                out.append(ch)

            i += 1

        result.append("".join(out))

    return result


def _paren_delta(line, comment_style):
    """Opening minus closing brackets on a line, ignoring strings/comments."""
    cleaned = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    cleaned = re.sub(r"'(?:\\.|[^'\\])*'", "''", cleaned)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned)

    if comment_style == "python":
        cleaned = re.sub(r"#.*$", "", cleaned)
    else:
        cleaned = re.sub(r"//.*$", "", cleaned)

    return cleaned.count("(") - cleaned.count(")")


def _triple_quote_flags(lines):
    """For each line: True if it is inside or touches a triple-quoted string."""
    flags = []
    in_triple = None

    for line in lines:
        stripped = line.strip()

        if in_triple:
            flags.append(True)

            if in_triple in stripped:
                in_triple = None

            continue

        flags.append('"""' in stripped or "\'\'\'" in stripped)

        for quote in ('"""', "\'\'\'"):
            if stripped.count(quote) % 2 == 1:
                in_triple = quote
                break

    return flags


def _join_continuations(lines, comment_style):
    """Join statements that continue on the next line inside parentheses.

    Returns a list of (text, line_number) where line_number is the line the
    statement starts on in the original code (1 = first line).
    """
    protected = (
        _triple_quote_flags(lines) if comment_style == "python"
        else [False] * len(lines)
    )
    skip_start = ("#",) if comment_style == "python" else ("//", "/*", "*")

    joined = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        depth = 0

        if stripped and not stripped.startswith(skip_start) and not protected[i]:
            depth = _paren_delta(line, comment_style)

        # "foo(function () {" opens a block: the next lines are its body,
        # not the rest of a split signature
        if depth > 0 and comment_style != "python" and stripped.endswith("{"):
            depth = 0

        if depth > 0:
            parts = [line.rstrip()]
            j = i + 1

            while j < len(lines) and depth > 0 and j - i <= 15 and not protected[j]:
                depth += _paren_delta(lines[j], comment_style)
                parts.append(lines[j].strip())
                j += 1

            if depth <= 0:
                joined.append((" ".join(parts), i + 1))
                i = j
                continue

        joined.append((line, i + 1))
        i += 1

    return joined


def _analyze_python(lines):
    lines = _join_continuations(lines, "python")
    functions, classes, variables = [], [], []
    methods = {}
    positions = {"functions": {}, "classes": {}}

    scopes = []          # (indent, kind, name)
    in_triple = None     # the quote style while inside a docstring

    for raw, line_number in lines:
        raw = raw.expandtabs(4)
        stripped = raw.strip()

        # Skip the inside of triple-quoted strings / docstrings
        if in_triple:
            if in_triple in stripped:
                in_triple = None
            continue

        for quote in ('"""', "'''"):
            if stripped.count(quote) % 2 == 1:
                in_triple = quote
                break

        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip())

        while scopes and indent <= scopes[-1][0]:
            scopes.pop()

        class_match = PYTHON_CLASS.match(stripped)

        if class_match:
            name = class_match.group(1)
            classes.append(name)
            positions["classes"].setdefault(name, []).append(line_number)
            methods.setdefault(name, [])
            scopes.append((indent, "class", name))
            continue

        def_match = PYTHON_DEF.match(stripped)

        if def_match:
            name = def_match.group(1)
            functions.append(name)
            positions["functions"].setdefault(name, []).append(line_number)

            if scopes and scopes[-1][1] == "class":
                methods[scopes[-1][2]].append(name)

            scopes.append((indent, "def", name))
            continue

        variables.extend(_find_variables(stripped, "python"))

    return functions, classes, variables, methods, positions


def _analyze_braces(lines):
    lines = _join_continuations(lines, "braces")
    functions, classes, variables = [], [], []
    methods = {}
    positions = {"functions": {}, "classes": {}}

    scopes = []            # (kind, name)
    pending = None         # declaration waiting for its "{" on a later line
    in_block_comment = False

    for raw, line_number in lines:
        line = raw

        # Skip block comments  /* ... */
        if in_block_comment:
            if "*/" in line:
                line = line.split("*/", 1)[1]
                in_block_comment = False
            else:
                continue

        line = re.sub(r"/\*.*?\*/", "", line)

        if "/*" in line:
            line = line.split("/*", 1)[0]
            in_block_comment = True

        stripped = line.strip()

        if not stripped or stripped.startswith(("//", "#", "*")):
            continue

        in_class_body = bool(scopes) and scopes[-1][0] == "class"
        decl_kind = None
        decl_name = None

        class_match = BRACE_CLASS.match(stripped)

        if class_match:
            decl_kind, decl_name = "class", class_match.group(1)
            classes.append(decl_name)
            positions["classes"].setdefault(decl_name, []).append(line_number)
            methods.setdefault(decl_name, [])

        elif not stripped.startswith(STATEMENT_STARTS):
            name = None

            for pattern in (JS_FUNCTION, JS_ARROW, TYPED_METHOD):
                found = pattern.match(stripped)

                if found:
                    name = found.group(1)
                    break

            if name is None and in_class_body:
                found = UNTYPED_METHOD.match(stripped)

                if found:
                    name = found.group(1)

            if name and name not in CONTROL_WORDS:
                decl_kind, decl_name = "function", name
                functions.append(name)
                positions["functions"].setdefault(name, []).append(line_number)

                if in_class_body:
                    methods[scopes[-1][1]].append(name)

        if decl_kind is None:
            variables.extend(_find_variables(stripped, "braces"))

        # Track braces so we know which class we are inside
        cleaned = _clean_for_braces(stripped)

        if decl_kind and "{" not in cleaned:
            pending = (decl_kind, decl_name)
        elif decl_kind is None and pending and ";" in cleaned:
            pending = None

        first_open = True

        for char in cleaned:
            if char == "{":
                if decl_kind and first_open:
                    scopes.append((decl_kind, decl_name))
                elif pending:
                    scopes.append(pending)
                    pending = None
                else:
                    scopes.append(("block", None))

                first_open = False

            elif char == "}":
                if scopes:
                    scopes.pop()

    return functions, classes, variables, methods, positions


def analyze_code(code, language=None):

    # Split exactly like the editor does, so line numbers match the screen
    lines = code.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    if lines and lines[-1] == "":
        lines.pop()

    total_lines = len(lines)

    if language == "JavaScript":
        lines = _strip_template_literals(lines)

    if language == "Python":
        use_python = True
    elif language in BRACE_LANGUAGES:
        use_python = False
    else:
        # Unknown language: guess from the code itself
        use_python = bool(re.search(
            r"^\s*(?:async\s+)?def\s+\w+\s*\(|^\s*class\s+\w+[^{]*:\s*$",
            code,
            re.MULTILINE
        ))

    if use_python:
        functions, classes, variables, methods, positions = _analyze_python(lines)
    else:
        functions, classes, variables, methods, positions = _analyze_braces(lines)

    return {
        "total_lines": total_lines,
        "functions": list(dict.fromkeys(functions)),
        "classes": list(dict.fromkeys(classes)),
        "variables": list(dict.fromkeys(variables)),
        "methods": {
            name: list(dict.fromkeys(found))
            for name, found in methods.items()
        },
        # Line numbers (1 = first line) where each name is defined
        "function_lines": positions["functions"],
        "class_lines": positions["classes"]
    }