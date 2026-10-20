import traceback

from flask import Flask, render_template, request, jsonify

from modules.language_detector import detect_language
from modules.code_analyzer import analyze_code
from modules.ai_documentation import generate_documentation
from modules.code_quality import check_code_quality
from modules.ai_docs import generate_ai_documentation_with_note


app = Flask(__name__)

# Languages the person can pick by hand (anything else means "auto detect")
SUPPORTED_LANGUAGES = {"Python", "Java", "C++", "C", "JavaScript"}

# Reject requests larger than 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


@app.errorhandler(413)
def too_large(error):
    return jsonify({"error": "The code is too large. Please send less than 5 MB."}), 413


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json(silent=True)

    # Anything that is not a JSON object is treated as "no data"
    if not isinstance(data, dict):
        data = {}

    code = data.get("code", "")

    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "No code was received."}), 400

    try:
        # Language: the one the person chose, otherwise detect it
        chosen = data.get("language", "")

        if isinstance(chosen, str) and chosen in SUPPORTED_LANGUAGES:
            language = chosen
        else:
            language = detect_language(code)

        # Code Analysis
        analysis = analyze_code(code, language)

        # Documentation: try AI first, fall back to the template generator
        documentation, ai_note = generate_ai_documentation_with_note(code, language)
        doc_source = "ai"

        if not documentation:
            documentation = generate_documentation(
                code,
                analysis
            )
            doc_source = "template"

        # Code Quality
        quality = check_code_quality(code, language)

    except Exception:
        # Full details go to the terminal, the page gets a short message
        traceback.print_exc()
        return jsonify({
            "error": "Something went wrong while analyzing the code."
        }), 500

    return jsonify({
        "language": language,
        "analysis": analysis,
        "documentation": documentation,
        "doc_source": doc_source,
        "ai_note": ai_note,
        "quality": quality
    })


if __name__ == "__main__":
    app.run(debug=True)