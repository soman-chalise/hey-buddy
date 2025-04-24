# === screenpipe.py (Restored original working logic) ===
import subprocess
import requests
import time
import os
import psutil
from desktop_use import DesktopUseClient, Locator, ApiError, sleep
import threading
import pyautogui

# ✅ Ensure Terminator's server.exe is running
def ensure_terminator_server_running():
    exe_name = "server.exe"
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
            print("🟢 Terminator server already running.")
            return

    server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "server.exe"))
    if os.path.exists(server_path):
        try:
            subprocess.Popen([server_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("🚀 Launched Terminator server.")
            time.sleep(1.5)
        except Exception as e:
            print(f"❌ Failed to start Terminator server: {e}")
    else:
        print("❌ server.exe not found in project directory.")

ensure_terminator_server_running()
client = DesktopUseClient()

# 🖱️ Click by label
def click_by_label(label):
    try:
        element = client.locator(f'name:{label}')
        element.click()
        return f"🖱️ Clicked '{label}'"
    except ApiError as e:
        return f"❌ API error clicking '{label}': {e}"
    except Exception as e:
        return f"❌ Failed to click '{label}': {e}"

# ⌨️ Type into field
from desktop_use import DesktopUseClient, sleep, ApiError

client = DesktopUseClient()

def type_into_field(label, text):
    try:
        clean_label = label.lower().replace("the ", "").strip()
        element = client.locator(f"name:{clean_label}")
        element.click()
        element.type_text(text)
        return f"⌨️ Typed '{text}' into '{clean_label}'"
    except Exception as e:
        return f"❌ Failed to type into '{label}': {e}"

# --------------------
# Type into the active window (interruptible)
# --------------------

def ask_groq_typing_prompt(user_input):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    model = "llama3-8b-8192"

    system_prompt = (
        "You are a typing assistant.\n\n"
        "If the command starts with 'type', remove the word 'type' and any filler like 'here', 'over here', "
        "'on screen', 'in current window', etc., and return ONLY the main sentence the user wants to type.\n"
        "Keep formatting and wording exactly the same.\n"
        "For example, 'type I am an AI over here' should return: I am an AI\n\n"
        "If the command starts with 'write', generate and return a response related to the prompt.\n\n"
        "Always respond ONLY with the string to type — no markdown, formatting, explanation, or extra content."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }

    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Groq error: {e}"

import pyautogui
import threading
import requests
import os
from pynput import mouse

stop_typing_flag = False

def ask_groq_typing_prompt(user_input, system_prompt):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    model = "llama3-8b-8192"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }

    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Groq error: {e}"

def ask_groq_typing_prompt(user_input, system_prompt):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    model = "llama3-8b-8192"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }

    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Groq error: {e}"

def type_text_into_active_window(full_command):
    global stop_typing_flag
    stop_typing_flag = False

    def on_mouse_click(x, y, button, pressed):
        global stop_typing_flag
        if pressed:
            print("🖱️ Mouse click detected — stopping typing.")
            stop_typing_flag = True
            return False

    def typing_task():
        try:
            original_input = full_command.strip()
            input_words = original_input.lower().split()

            if not input_words:
                print("⚠️ Empty command. Skipping.")
                return

            # ✅ Forgiving detection (if 'write' or 'type' in first 3 words)
            if "type" in input_words[:3]:
                system_prompt = (
                    "You are a typing assistant. Remove 'type' and any filler like 'here', 'over here', etc. "
                    "Return only the literal message to type — no extra text, no formatting."
                )
            elif "write" in input_words[:3]:
                system_prompt = (
                    "You are a helpful assistant. Generate a full, meaningful response to the user's prompt. "
                    "Return only the plain text — no markdown, no prefix, no explanation."
                )
            else:
                print("⚠️ Unrecognized command start — skipping.")
                return

            print(f"🧠 Sending to Groq: '{original_input}'")
            text_to_type = ask_groq_typing_prompt(original_input, system_prompt)

            if not text_to_type or "please provide" in text_to_type.lower():
                print("⚠️ Groq returned invalid or empty output.")
                return

            print(f"⌨️ Typing: {text_to_type}")
            listener = mouse.Listener(on_click=on_mouse_click)
            listener.start()

            for char in text_to_type:
                if stop_typing_flag:
                    print("⛔ Typing interrupted.")
                    break
                pyautogui.typewrite(char)
                pyautogui.sleep(0.05)

            listener.stop()
            print("✅ Typing finished.")

        except Exception as e:
            print(f"❌ Typing task failed: {e}")

    threading.Thread(target=typing_task).start()
# 🧾 List UI elements
def list_ui_elements():
    try:
        elements = client.get_ui_elements()
        return "\n".join([f"{el.role}: {el.name}" for el in elements])
    except ApiError as e:
        return f"❌ API error listing UI elements: {e}"
    except Exception as e:
        return f"❌ Failed to list UI elements: {e}"

# 🪟 Get active app name
def get_active_app_name():
    try:
        app_element = client.locator("app").first()
        return app_element.role or "unknown_app"
    except Exception as e:
        print(f"❌ Failed to get active app name: {e}")
        return None

# 🪟 Get active window title
def get_active_window_title():
    try:
        window_element = client.locator("window").first()
        return window_element.role or "unknown_window"
    except Exception as e:
        print(f"❌ Failed to get active window title: {e}")
        return None

# 🚀 Launch app via Terminator
def launch_app_via_terminator(app_name):
    try:
        client.open_application(app_name)
        return f"🚀 Launched {app_name} via Terminator"
    except ApiError as e:
        return f"❌ API error launching {app_name}: {e}"
    except Exception as e:
        return f"❌ Failed to launch {app_name} via Terminator: {e}"