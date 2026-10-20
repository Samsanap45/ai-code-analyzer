const codeEditor = document.getElementById("code");
const lineNumbers = document.getElementById("lineNumbers");
const languageBadge = document.getElementById("languageBadge");
const analyzeButton = document.getElementById("analyzeBtn");
const languageSelect = document.getElementById("languageSelect");

// Prevent code analysis output from being interpreted as HTML
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, function (char) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }[char];
    });
}


// Show only the short message of an issue; the quoted line preview
// (if any) appears when the mouse is held over it
function formatIssue(issue) {
    const match = String(issue).match(/^([^"]*?):\s*"(.*)"$/);

    if (!match) {
        return escapeHTML(issue);
    }

    return '<span title="' + escapeHTML(match[2]) + '">' + escapeHTML(match[1]) + "</span>";
}

// Turn a list of line numbers into text such as " (line 12, +2 more)"
function lineLabel(lines) {
    if (!Array.isArray(lines) || !lines.length) {
        return "";
    }

    let text = " (line " + lines[0];

    if (lines.length > 1) {
        text += ", +" + (lines.length - 1) + " more";
    }

    return text + ")";
}


// Save some text as a file in the browser
function saveTextFile(filename, text, mimeType) {

    const blob = new Blob(
        [text],
        { type: mimeType + ";charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(function () {
        URL.revokeObjectURL(url);
    }, 1000);
}


// Make the documentation text look right in Markdown
function textToMarkdown(text) {

    const lines = [];

    text.split("\n").forEach(function (line) {

        const trimmed = line.trim();

        // "========== CODE DOCUMENTATION ==========" is not needed
        if (/^=+\s.*\s=+$/.test(trimmed)) {
            return;
        }

        // "Overview:" / "Functions:" become small headings
        const heading = trimmed.match(/^([A-Z][A-Za-z ]{1,30}):$/);

        if (heading) {
            lines.push("", "### " + heading[1], "");
            return;
        }

        // Show characters such as _ * < > exactly as written
        // (otherwise __init__ turns bold and <name> disappears)
        const safe = line
            .replace(/([\\`*_])/g, "\\$1")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/^(\s*)#/, "$1\\#");

        // Two spaces at the end keep each line on its own line
        lines.push(trimmed ? safe.replace(/\s+$/, "") + "  " : "");
    });

    // No more than one empty line in a row
    return lines.join("\n").replace(/\n{3,}/g, "\n\n");
}


// Build the whole result as a Markdown document
function buildMarkdown(result, analysis, documentation) {

    const functions = analysis.functions || [];
    const classes = analysis.classes || [];
    const variables = analysis.variables || [];
    const functionLines = analysis.function_lines || {};
    const classLines = analysis.class_lines || {};
    const methods = analysis.methods || {};

    const out = [];

    out.push("# Code Documentation", "");
    out.push("- **Language:** " + (result.language || "Unknown"));
    out.push("- **Lines:** " + (Number(analysis.total_lines) || 0));
    out.push("- **Functions:** " + functions.length);
    out.push("- **Classes:** " + classes.length);
    out.push("- **Variables:** " + variables.length, "");

    out.push("## Code Structure", "");

    out.push("### Functions", "");
    if (functions.length) {
        functions.forEach(function (name) {
            out.push("- `" + name + "`" + lineLabel(functionLines[name]));
        });
    } else {
        out.push("None");
    }
    out.push("");

    out.push("### Classes", "");
    if (classes.length) {
        classes.forEach(function (name) {
            const found = Array.isArray(methods[name]) ? methods[name] : [];
            out.push(
                "- `" + name + "`" + lineLabel(classLines[name]) +
                (found.length
                    ? " - methods: " + found.map(function (m) {
                          return "`" + m + "`";
                      }).join(", ")
                    : "")
            );
        });
    } else {
        out.push("None");
    }
    out.push("");

    out.push("### Variables", "");
    if (variables.length) {
        variables.forEach(function (name) {
            out.push("- `" + name + "`");
        });
    } else {
        out.push("None");
    }
    out.push("");

    out.push("## Documentation", "");
    out.push(
        result.doc_source === "ai"
            ? "_Written by AI._"
            : "_Generated from templates, not by AI._"
    );
    out.push("", textToMarkdown(documentation), "");

    return out.join("\n");
}


// ANALYZE CODE
analyzeButton.addEventListener("click", async function () {

    const code = codeEditor.value;
    const resultBox = document.getElementById("result");

    if (!code.trim()) {
        alert("Please enter some code first.");
        return;
    }

    analyzeButton.textContent = "Analyzing...";
    analyzeButton.disabled = true;

    resultBox.innerHTML =
        '<p class="loading-note">Analyzing your code, please wait...</p>';

    try {

        const response = await fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code: code,
                language: languageSelect.value
            })
        });

        if (!response.ok) {
            let message = "Server returned status " + response.status;
            try {
                const errorData = await response.json();
                if (errorData.error) {
                    message = errorData.error;
                }
            } catch (e) {
                // response was not JSON, keep the default message
            }
            throw new Error(message);
        }

        const result = await response.json();

        languageBadge.textContent = result.language || "Unknown";

        const analysis = result.analysis || {};
        const quality = result.quality || {};

        const functions = analysis.functions || [];
        const classes = analysis.classes || [];
        const variables = analysis.variables || [];

        const functionLines = analysis.function_lines || {};
        const classLines = analysis.class_lines || {};

        const issues = quality.issues || [];
        const suggestions = quality.suggestions || [];

        // DISPLAY RESULTS
        resultBox.innerHTML = `

            <h2>Analysis Results</h2>

            <!-- SUMMARY CARDS -->

            <div class="summary-grid">

                <div class="summary-card">
                    <span class="card-label">LANGUAGE</span>
                    <strong>${escapeHTML(result.language || "Unknown")}</strong>
                </div>

                <div class="summary-card">
                    <span class="card-label">LINES</span>
                    <strong>${Number(analysis.total_lines) || 0}</strong>
                </div>

                <div class="summary-card">
                    <span class="card-label">FUNCTIONS</span>
                    <strong>${functions.length}</strong>
                </div>

                <div class="summary-card">
                    <span class="card-label">CLASSES</span>
                    <strong>${classes.length}</strong>
                </div>

            </div>


            <!-- CODE STRUCTURE -->

            <div class="result-card">

                <h3>Code Structure</h3>

                <div class="structure-grid">

                    <div>
                        <span>Functions</span>
                        ${functions.length
                            ? `<ul class="item-list">${functions.map(name => `<li>${escapeHTML(name)}<span class="line-ref">${escapeHTML(lineLabel(functionLines[name]))}</span></li>`).join("")}</ul>`
                            : "<p>None</p>"}
                    </div>

                    <div>
                        <span>Classes</span>
                        ${classes.length
                            ? `<ul class="item-list">${classes.map(function (name) {
                                  const found = (analysis.methods || {})[name] || [];
                                  return `<li>${escapeHTML(name)}<span class="line-ref">${escapeHTML(lineLabel(classLines[name]))}</span>` + (found.length
                                      ? `<span class="methods"> (${found.map(escapeHTML).join(", ")})</span>`
                                      : "") + `</li>`;
                              }).join("")}</ul>`
                            : "<p>None</p>"}
                    </div>

                    <div>
                        <span>Variables</span>
                        ${variables.length
                            ? `<ul class="item-list">${variables.map(name => `<li>${escapeHTML(name)}</li>`).join("")}</ul>`
                            : "<p>None</p>"}
                    </div>

                </div>

            </div>


            <!-- DOCUMENTATION -->

            <div class="result-card">

                <div class="documentation-header">
                    <h3>Documentation (${result.doc_source === "ai"
                        ? "AI-generated"
                        : "template-based"})</h3>

                    <div class="documentation-actions">

                        <button
                            id="copyDocsBtn"
                            class="secondary-btn"
                            type="button">
                            Copy Documentation
                        </button>

                        <button
                            id="downloadDocsBtn"
                            class="secondary-btn"
                            type="button">
                            Download .txt
                        </button>

                        <button
                            id="downloadMdBtn"
                            class="secondary-btn"
                            type="button">
                            Download .md
                        </button>

                    </div>
                </div>

                ${result.ai_note
                    ? `<p class="ai-note">${escapeHTML(result.ai_note)}</p>`
                    : ""}
                <pre id="documentationText"></pre>

            </div>


            <!-- CODE QUALITY -->

            <div class="quality-grid">

                <div class="quality-card">

                    <h3>Issues</h3>

                    <ul>
                        ${
                            issues.length
                            ? issues.map(issue =>
                                `<li>${formatIssue(issue)}</li>`
                              ).join("")
                            : "<li>No major issues detected.</li>"
                        }
                    </ul>

                </div>


                <div class="quality-card">

                    <h3>Suggestions</h3>

                    <ul>
                        ${
                            suggestions.length
                            ? suggestions.map(suggestion =>
                                `<li>${escapeHTML(suggestion)}</li>`
                              ).join("")
                            : "<li>No suggestions.</li>"
                        }
                    </ul>

                </div>

            </div>

        `;


        // DISPLAY DOCUMENTATION AS PLAIN TEXT
        const documentationText =
            document.getElementById("documentationText");

        documentationText.textContent =
            result.documentation || "No documentation generated.";


        // COPY DOCUMENTATION
        const copyDocsBtn =
            document.getElementById("copyDocsBtn");

        copyDocsBtn.addEventListener("click", async function () {

            try {

                await navigator.clipboard.writeText(
                    documentationText.textContent
                );

                copyDocsBtn.textContent = "Copied!";

                setTimeout(function () {
                    copyDocsBtn.textContent = "Copy Documentation";
                }, 1500);

            } catch (error) {

                console.error("Copy failed:", error);

                alert(
                    "Copy failed. Please select the documentation and copy it manually."
                );

            }

        });


        // DOWNLOAD DOCUMENTATION (.txt)
        const downloadDocsBtn =
            document.getElementById("downloadDocsBtn");

        downloadDocsBtn.addEventListener("click", function () {
            saveTextFile(
                "code-documentation.txt",
                documentationText.textContent,
                "text/plain"
            );
        });


        // DOWNLOAD DOCUMENTATION (.md)
        const downloadMdBtn =
            document.getElementById("downloadMdBtn");

        downloadMdBtn.addEventListener("click", function () {
            saveTextFile(
                "code-documentation.md",
                buildMarkdown(result, analysis, documentationText.textContent),
                "text/markdown"
            );
        });


    } catch (error) {

        console.error("Analysis error:", error);

        resultBox.innerHTML = `
            <div class="result-card">
                <h2>Something went wrong</h2>
                <p>Unable to analyze the code. Please try again.</p>
                <p>${escapeHTML(error.message)}</p>
            </div>
        `;

    } finally {

        analyzeButton.textContent = "Analyze Code";
        analyzeButton.disabled = false;

    }

});


// UPDATE LINE NUMBERS
function updateLineNumbers() {

    const lines = codeEditor.value.split("\n").length;

    let numbers = "";

    for (let i = 1; i <= lines; i++) {
        numbers += i + "\n";
    }

    lineNumbers.textContent = numbers;
}


// SYNCHRONIZE EDITOR SCROLLING
codeEditor.addEventListener("input", updateLineNumbers);

codeEditor.addEventListener("scroll", function () {
    lineNumbers.scrollTop = codeEditor.scrollTop;
});

// FILE UPLOAD
const fileInput = document.getElementById("fileInput");
const fileButton = document.getElementById("fileBtn");
const fileNameLabel = document.getElementById("fileName");
const editorFilename = document.querySelector(".filename");

fileButton.addEventListener("click", function () {
    fileInput.click();
});

fileInput.addEventListener("change", function () {

    const file = fileInput.files[0];

    if (!file) {
        return;
    }

    // Same limit as the server (5 MB)
    if (file.size > 5 * 1024 * 1024) {
        alert("File is too large. Please choose a file under 5 MB.");
        fileInput.value = "";
        return;
    }

    const reader = new FileReader();

    reader.onload = function () {
        codeEditor.value = reader.result;
        codeEditor.scrollTop = 0;
        lineNumbers.scrollTop = 0;
        fileNameLabel.textContent = file.name;
        editorFilename.textContent = file.name;
        languageBadge.textContent = "Auto Detect";
        updateLineNumbers();
    };

    reader.onerror = function () {
        alert("Could not read that file. Please try another one.");
    };

    reader.readAsText(file);

    // Allow choosing the same file again later
    fileInput.value = "";
});


updateLineNumbers();