import re


def extract_function_body(code, function_name):
    lines = code.splitlines()
    escaped_name = re.escape(function_name)

    # Find Python function
    for i, line in enumerate(lines):
        if re.match(
            r"^\s*(async\s+)?def\s+" + escaped_name + r"\s*\(",
            line
        ):
            body = []
            indent = len(line) - len(line.lstrip())

            for next_line in lines[i + 1:]:
                if next_line.strip() == "":
                    body.append(next_line)
                    continue

                next_indent = len(next_line) - len(next_line.lstrip())

                if next_indent <= indent:
                    break

                body.append(next_line)

            return "\n".join(body)

    # Find Java method
    for i, line in enumerate(lines):
        if re.search(
            r"\b" + escaped_name + r"\s*\([^;]*\)\s*\{",
            line
        ):
            body = []
            depth = 0
            started = False

            for current_line in lines[i:]:
                for char in current_line:
                    if char == "{":
                        depth += 1
                        started = True
                    elif char == "}":
                        depth -= 1

                        if started and depth == 0:
                            return "\n".join(body)

                if started:
                    body.append(current_line)

            return "\n".join(body)

    return ""


def extract_parameters(code, function_name):
    escaped_name = re.escape(function_name)

    patterns = [
        r"^\s*(?:async\s+)?def\s+" + escaped_name + r"\s*\(([^)]*)\)",
        r"\b" + escaped_name + r"\s*\(([^)]*)\)"
    ]

    for line in code.splitlines():
        for pattern in patterns:
            match = re.search(pattern, line)

            if match:
                return match.group(1).strip() or "None"

    return "None"


def infer_function_purpose(function_name, body):
    body = body.strip()

    if not body:
        return "Function body could not be identified."

    if function_name == "main":
        if "new " in body:
            return "Program entry point; creates objects and executes statements."
        return "Program entry point; executes program statements."

    if "System.out.print" in body or "print(" in body:
        return "Displays output."

    if "return" in body and "%" in body and "== 0" in body:
        return "Checks whether a number is even."

    if "return" in body and "%" in body and "!= 0" in body:
        return "Checks whether a number is odd."

    if "return" in body and "+" in body:
        return "Adds or combines values and returns the result."

    if "return" in body and "-" in body:
        return "Subtracts values and returns the result."

    if "return" in body and "*" in body:
        return "Multiplies values and returns the result."

    if "return" in body and "/" in body:
        return "Divides values and returns the result."

    if "return" in body:
        return "Returns a calculated or retrieved value."

    if "if " in body or "else" in body or "switch" in body:
        return "Uses conditional logic."

    if "for " in body or "while " in body:
        return "Repeats operations using a loop."

    if "new " in body:
        return "Creates an object."

    return "Performs the operations defined in its body."


def generate_documentation(code, analysis):
    documentation = []

    documentation.append("========== CODE DOCUMENTATION ==========")
    documentation.append("\nOverview:")
    documentation.append(
        f"This code contains {analysis['total_lines']} lines."
    )

    if analysis.get("functions"):
        documentation.append("\nFunctions:")

        for function in analysis["functions"]:
            body = extract_function_body(code, function)
            parameters = extract_parameters(code, function)
            purpose = infer_function_purpose(function, body)

            documentation.append(f"\n- Function: {function}()")
            documentation.append(f"  Parameters: {parameters}")
            documentation.append(f"  Purpose: {purpose}")
            documentation.append(
                "  Note: Purpose is inferred using code patterns."
            )

    if analysis.get("classes"):
        documentation.append("\nClasses:")

        for class_name in analysis["classes"]:
            documentation.append(
                f"- {class_name}: Class identified in the source code."
            )

    if analysis.get("variables"):
        documentation.append("\nVariables:")

        for variable in analysis["variables"]:
            documentation.append(
                f"- {variable}: Variable identified in the source code."
            )

    return "\n".join(documentation)


if __name__ == "__main__":
    sample_code = """class Calculator {
    int add(int a, int b) {
        return a + b;
    }

    public static void main(String[] args) {
        Calculator c = new Calculator();
        System.out.println(c.add(5, 3));
    }
}"""

    sample_analysis = {
        "total_lines": len(sample_code.splitlines()),
        "functions": ["add", "main"],
        "classes": ["Calculator"],
        "variables": ["c"]
    }

    print(generate_documentation(sample_code, sample_analysis))