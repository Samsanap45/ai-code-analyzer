def get_code():
    print("====================================")
    print("   AI CODE DOCUMENTATION SYSTEM")
    print("====================================")

    print("\nPaste your code below.")
    print("Type END on a new line when finished.\n")

    code_lines = []

    while True:
        line = input()

        if line == "END":
            break

        code_lines.append(line)

    code = "\n".join(code_lines)

    return code


# Test the module
if __name__ == "__main__":
    code = get_code()

    print("\n========== YOUR CODE ===========")
    print(code)