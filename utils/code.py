import subprocess
import os
import re

# Mapping of language keywords to file extensions
EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "html": ".html",
    "css": ".css",
    "c++": ".cpp",
    "cpp": ".cpp",
    "c": ".c",
    "java": ".java",
    "typescript": ".ts",
    "go": ".go",
    "rust": ".rs",
    "bash": ".sh",
    "shell": ".sh",
    "json": ".json",
    "sql": ".sql",
}

def detect_language_and_extension(code: str, default_ext=".txt"):
    for lang, ext in EXTENSIONS.items():
        if re.search(rf"\b{lang}\b", code, re.IGNORECASE):
            return lang, ext
    return "text", default_ext

def write_code_to_vscode(code: str, base_filename="generated_code"):
    lang, ext = detect_language_and_extension(code)
    filename = f"{base_filename}{ext}"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"✅ Code saved as {filename} ({lang})")

    try:
        subprocess.Popen(["code", filename])
    except FileNotFoundError:
        # Try default install location if 'code' command isn't in PATH
        vscode_path = r"C:\Users\soman\AppData\Local\Programs\Microsoft VS Code\Code.exe"
        if os.path.exists(vscode_path):
            subprocess.Popen([vscode_path, filename])
        else:
            print("❌ VS Code not found. Please make sure it's installed.")
