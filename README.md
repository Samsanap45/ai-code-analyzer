# ai-code-analyzer

A small web app that analyzes source code and generates documentation for it.
Paste or upload your code, click **Analyze Code**, and get a summary, the structure of the code, documentation, and quality tips.

## Features

- Supports Python, Java, C++, C and JavaScript (auto-detected, or pick the language yourself)
- Finds functions, classes, methods and variables, with their line numbers
- Handles large files (up to 5 MB)
- Documentation written by Google Gemini (free tier), with an automatic fallback to built-in template documentation when no API key is set
- Quality check: long lines, TODO/FIXME comments, print statements
- Copy the documentation, or download it as `.txt` or `.md`

## Requirements

- Python 3.9 or newer

## Install

```
git clone https://github.com/Samsanap45/ai-code-analyzer.git
cd ai-code-analyzer
py -m pip install -r requirements.txt
```

## Run

```
py backend\app.py
```

Then open http://127.0.0.1:5000 in your browser.

## AI documentation (optional)

Without a key the app still works and uses template documentation.
To turn on Gemini documentation, get a free API key from Google AI Studio and set it as an environment variable. Never put the key in a code file.

PowerShell, for the current terminal only:

```
$env:GEMINI_API_KEY="your-key-here"
```

Or save it for all future terminals:

```
setx GEMINI_API_KEY "your-key-here"
```

Note: on the free tier, Google may use the code you send to improve its products. Do not send private or confidential code.

## Run the tests

From the project folder:

```
py -m unittest discover -s tests -t .
```

## Project structure

```
ai-code-analyzer
├── backend
│   ├── app.py          Flask app and /analyze endpoint
│   ├── modules         code analyzer, quality checker, language detector, documentation
│   ├── static          script.js, style.css
│   └── templates       index.html
├── tests               automated tests
├── requirements.txt
└── README.md
```

## Limitations

The analyzer uses pattern matching, not a full parser, so unusual code styles can occasionally be misread.