SUPPORTED_LANGUAGES = {
    "Python": [".py"],
    "Java": [".java"],
    "C++": [".cpp", ".cc"],
    "JavaScript": [".js"],
    "C": [".c"]
}


def get_supported_languages():

    return list(SUPPORTED_LANGUAGES.keys())


def is_supported(language):

    return language in SUPPORTED_LANGUAGES


# Test the module
if __name__ == "__main__":

    languages = get_supported_languages()

    print("========== SUPPORTED LANGUAGES ==========")

    for language in languages:
        print("-", language)

    print("\nIs Python supported?", is_supported("Python"))
    print("Is Ruby supported?", is_supported("Ruby"))