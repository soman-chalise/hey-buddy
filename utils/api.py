import os
import requests
from dotenv import load_dotenv
import json
import re

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

def ask_groq(prompt, system_message=None):
    if system_message is None:
        system_message = (
            "You are a helpful assistant. For task-related commands, always respond with a single JSON object "
            "in the format: {\"action\": \"open_app\", \"target\": \"<executable_name>\", \"content\": \"...\"}. "
            "Always use actual system-level executable names like 'code' for VS Code, 'notepad.exe' for Notepad, "
            "'msedge' for any web browsing or YouTube-related tasks (use Edge instead of Chrome), "
            "'spotify.exe' for Spotify, etc. "
            "Avoid fuzzy names like 'vs code', 'browser', or 'open YouTube'. If a web link or search is involved, always use 'msedge'. "
            "Do not include explanations or extra commentary — just return the JSON object only."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512,
        "top_p": 1.0,
        "stream": False
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error contacting Groq API: {e}")
        return "Error occurred while processing your request."

def classify_command(command):
    classification_prompt = (
        f"Classify the following command. Respond ONLY with JSON:\n"
        f'{{"type": "task"|"question"|"other", "reason": "<short reason>"}}\n\n'
        f"Command: {command}"
    )

    response = ask_groq(classification_prompt)
    print(f"📦 Raw classification response: {response}")

    try:
        data = json.loads(response)
        return data.get("type", "unknown").lower()
    except json.JSONDecodeError:
        print("⚠️ Failed to parse classification JSON.")
        return "unknown"

def analyze_write_command(command):
    cmd = command.lower().strip()
    response = {
        "type": "task",
        "subtype": "write",
        "mode": None,
        "details": {}
    }

    # Case 1: Writing to a file
    match_file = re.search(r'(?:in|into)\s+([\w\-.]+\.(txt|py|md|log|cpp|js|html))', cmd)
    if match_file:
        filename = match_file.group(1)
        response["mode"] = "file"
        response["details"]["filename"] = filename
        response["details"]["exists"] = os.path.exists(filename)
        return response

    # Case 2: Writing into active window
    if any(word in cmd for word in ["here", "over here", "current window", "current screen", "active window"]):
        response["mode"] = "active_window"
        return response

    # Case 3: Just write something
    if cmd.startswith("write"):
        content = cmd[len("write"):].strip()
        response["mode"] = "inline"
        response["details"]["content"] = content
        return response

    return {"type": "unknown"}

def analyze_search_command(command):
    cmd = command.lower().strip()
    result = {
        "type": "task",
        "subtype": "search",
        "target_site": None,
        "query": None
    }

    match = re.match(r"search (.+?) on (\\w+)", cmd)
    if match:
        result["query"] = match.group(1).strip()
        result["target_site"] = match.group(2).strip()
        return result

    match_simple = re.match(r"search (.+)", cmd)
    if match_simple:
        result["query"] = match_simple.group(1).strip()
        return result

    return {"type": "unknown"}
