# === api.py ===
import os
import re
import json
import requests
from dotenv import load_dotenv

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

def rule_based_classify_command(cmd: str) -> str:
    cmd = cmd.lower().strip()
    cmd = re.sub(r'^"|"$', '', cmd).strip()

    # 🎯 Prioritize ending-based screen phrases
    screen_phrases = [
        "on my screen", "on the screen", "in the screen", 
        "what's on my screen", "what is on the screen", "solve on screen"
    ]
    if any(cmd.endswith(phrase) for phrase in screen_phrases):
        return "screen_vision"

    # 💬 Questions
    if any(kw in cmd for kw in ["tell me", "give me", "what is", "who is", "how does", "explain"]):
        return "question"

    # 💻 Code
    if re.search(r"(generate|write|make)\s+(a|an)?\s*(python|java(script)?|html|css|sql|bash|go|c\+\+|c|rust|typescript)( code)?", cmd):
        return "code"

    # ✍️ Write into active window
    if re.search(r"(type|write).*(here|active window|current screen|over here)", cmd):
        return "write_active"

    # 📄 Write into file
    if re.search(r"write.*into.*\.(txt|py|md|log)", cmd):
        return "write_file"

    # 🧾 Field typing
    if re.search(r"type .+ into .+", cmd):
        return "type_into_field"

    # 🖱️ Click
    if re.search(r"click( on)? .+", cmd):
        return "click"

    # 🔊 Volume
    if re.search(r"set volume to|volume up|volume down|increase volume|decrease volume", cmd):
        return "volume"

    # ⏰ Timer or alarm
    if re.search(r"(set timer|set alarm|remind me)", cmd):
        return "alarm_timer"

    # 📋 UI listing
    if re.search(r"list elements|screen elements|show screen elements", cmd):
        return "list_elements"

    # 🌐 Web search
    if re.search(r"(search|google|look up)\s+.+", cmd):
        return "search_web"

    # 🚀 App open
    if re.search(r"\b(open|launch|start)\s+[\w\s]+", cmd):
        return "open_app"

    return "other"



def analyze_write_command(command):
    cmd = command.lower().strip()
    response = {
        "type": "task",
        "subtype": "write",
        "mode": None,
        "details": {}
    }

    match_file = re.search(r'(?:in|into)\s+([\w\-.]+\.(txt|py|md|log|cpp|js|html))', cmd)
    if match_file:
        filename = match_file.group(1)
        response["mode"] = "file"
        response["details"]["filename"] = filename
        response["details"]["exists"] = os.path.exists(filename)
        return response

    if any(word in cmd for word in ["here", "over here", "current window", "current screen", "active window"]):
        response["mode"] = "active_window"
        return response

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
def is_screen_vision_command(cmd: str) -> bool:
    cmd = cmd.lower().strip()
    screen_phrases = [
        "what's on my screen", "describe screen", "explain this",
        "solve this", "solve the problem", "analyze the screen", "help with this",
        "solve on screen"
    ]
    if any(phrase in cmd for phrase in screen_phrases):
        return True

    patterns = [
        r"solve (.+?) on screen",
        r"solve (question|problem) \w+",
        r"help me with (question|problem)? \w+",
        r"answer (question|problem)? \w+",
        r"what (is|does) (this|that|it)"
    ]
    return any(re.search(p, cmd) for p in patterns)
