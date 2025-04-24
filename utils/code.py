import os
import re
from utils.api import ask_groq

LANG_EXTENSIONS = {
    "python": "py",
    "c plus plus":"cpp",
    "c++": "cpp",
    "cpp": "cpp",
    "c": "c",
    "java": "java",
    "javascript": "js",
    "js": "js",
    "html": "html",
    "bash": "sh"
}

def extract_filename_from_prompt(prompt):
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", prompt.lower())
    keywords = [word for word in cleaned.split() if word not in {
        "generate", "a", "an", "the", "code", "to", "for", "in", "on", "of", "write"
    }]
    if not keywords:
        return "generated_code"
    return "_".join(keywords[:4])

def write_code_to_vscode(code: str, prompt: str):
    lang = "txt"
    for key in LANG_EXTENSIONS:
        if key in prompt.lower():
            lang = LANG_EXTENSIONS[key]
            break

    base_name = extract_filename_from_prompt(prompt)
    filename = f"{base_name}.{lang}"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    os.system(f"code {filename}")
    return filename

def generate_code_from_command(cmd):
    print(f"🧠 Asking Groq to generate code for: '{cmd}'")

    code = ask_groq(
        cmd,
        system_message=(
            "You are a code assistant. Generate only the code in response to the user's request. "
            "Do not include explanations, markdown formatting, or comments unless explicitly requested."
        )
    )

    filename = write_code_to_vscode(code, cmd)
    return {
        "action": "save_file",
        "target": filename,
        "content": code
    }
