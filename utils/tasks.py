import os
import re
import time
import threading
import subprocess
import pyautogui
import json
from datetime import datetime, timedelta
from utils.screenpipe import click_by_label, type_into_field, type_text_into_active_window
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import ctypes
from utils.api import ask_groq
from utils.code import write_code_to_vscode

# ----------- Volume Control Functions -------------
def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))

def get_current_volume():
    return int(get_volume_interface().GetMasterVolumeLevelScalar() * 100)

def set_volume(percent):
    get_volume_interface().SetMasterVolumeLevelScalar(percent / 100.0, None)

def adjust_volume(change, absolute=False):
    if absolute:
        set_volume(change)
        return f"🔊 Volume set to {change}%."
    else:
        current = get_current_volume()
        new_volume = max(0, min(current + change, 100))
        set_volume(new_volume)
        return f"🔊 Volume {'increased' if change > 0 else 'decreased'} to {new_volume}%."

# ----------- Screenshot -------------
def take_screenshot():
    filename = f"screenshot_{int(time.time())}.png"
    pyautogui.screenshot(filename)
    return f"📸 Screenshot saved as {filename}"

# ----------- Timer/Alarm -------------
def set_timer_or_alarm(command):
    now = datetime.now()
    cmd = command.lower()

    match_timer = re.search(r'(timer.*?)(\d+)\s*(seconds?|minutes?|hours?)', cmd)
    if match_timer:
        val = int(match_timer.group(2))
        unit = match_timer.group(3)
        delay = val * (3600 if 'hour' in unit else 60 if 'min' in unit else 1)

        def ring(): print("⏰ Timer done!")
        threading.Timer(delay, ring).start()
        return f"⏲️ Timer set for {val} {unit}."

    match_alarm = re.search(r'(alarm.*?)(\d{1,2}):(\d{2})', cmd)
    if match_alarm:
        h, m = int(match_alarm.group(2)), int(match_alarm.group(3))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target < now:
            target += timedelta(days=1)
        delay = (target - now).total_seconds()

        def ring(): print("⏰ Alarm ringing!")
        threading.Timer(delay, ring).start()
        return f"⏰ Alarm set for {h}:{m:02d}."

    return None

# ----------- Launch Apps, Save Files -------------
def launch_app(app_name):
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"🚀 Launching {app_name}..."
    except Exception as e:
        return f"❌ Failed to launch {app_name}: {e}"

def save_to_file(filename, content):
    if not filename.endswith(".txt") and not filename.endswith(".py"):
        filename += ".txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"💾 Content saved to {filename}"
    except Exception as e:
        return f"❌ Error saving to file: {e}"

# ----------- Main Task Handler -------------
def handle_task(command):
    import re
    import json
    from utils.api import ask_groq
    from utils.code import write_code_to_vscode
    from utils.screenpipe import click_by_label, type_into_field, type_text_into_active_window, list_ui_elements
    from utils.tasks import set_timer_or_alarm, adjust_volume, take_screenshot
    from utils.vision import analyze_screen_with_groq_vision

    cmd = command.lower()

    # 🔍 Vision-based screen help
    if any(phrase in cmd for phrase in [
        "what's on my screen", "what do you see", "help with this", "explain this",
        "solve this", "answer this question", "solve the problem on the screen", "what is this question"
    ]):
        result = analyze_screen_with_groq_vision(prompt=command)
        return {
            "action": "message_only",
            "target": "",
            "content": result
        }

    # ✍️ Insert plain text into current window
    if match := re.match(r"write\s+(.+)", cmd):
        return {"action": "insert_text", "target": "", "content": match.group(1).strip()}

    # 📄 Write file with generated content
    match = re.match(r"(.+?)\s+(?:in|into)\s+([\w\-.]+\.(txt|py|md|log))", cmd)
    if match:
        prompt, filename = match.group(1).strip(), match.group(2).strip()
        generated = ask_groq(
            f"Write {prompt}. Only return the result.",
            system_message="You are a creative AI. Respond ONLY with the content — no markdown or explanation."
        )
        return {"action": "save_file", "target": filename, "content": generated}
        
    if match := re.search(r'(search|look up|google)\s+(.*)', cmd):
            query = match.group(2).strip()
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            return {
                "action": "open_url",
                "target": url,
                "content": ""
            }
    # 👨‍💻 Code generation
    if match := re.match(r"(write|generate|make)\s+(a|an)?\s*(python|javascript|java|c\+\+|c|html|css|bash|sql|rust|go|typescript)\s+(.+)", cmd):
        prompt = match.group(0)
        code = ask_groq(
            f"{prompt}. Only return the code block, no explanation.",
            system_message="You are a coding assistant. Return ONLY the code — no explanation, no markdown."
        )
        code = re.sub(r"```(?:\w+)?", "", code).replace("```", "").strip()
        write_code_to_vscode(code)
        return {"action": "write_only", "target": "", "content": "✅ Code generated and opened in VS Code."}

    # 🖱️ Click UI label
    if match := re.search(r'click (?:on )?(.*)', cmd):
        return {"action": "write_only", "target": "", "content": click_by_label(match.group(1).strip())}

    # ⌨️ Type into field
    if match := re.search(r'type (.+) into (.+)', cmd):
        return {"action": "write_only", "target": "", "content": type_into_field(match.group(2).strip(), match.group(1).strip())}

    # ⌨️ Type into active window
    if match := re.search(r'type here (.+)', cmd):
        type_text_into_active_window(match.group(1).strip())
        return {"action": "write_only", "target": "", "content": f"⌨️ Typing '{match.group(1).strip()}' into active window."}

    # 🎛️ Screenshot
    if "screenshot" in cmd:
        return {"action": "write_only", "target": "", "content": take_screenshot()}

    # 🔊 Volume control
    if re.search(r'(set|volume to|change volume to)\s*([0-9]+)', cmd):
        volume = int(re.findall(r'[0-9]+', cmd)[0])
        return {"action": "write_only", "target": "", "content": adjust_volume(volume, absolute=True)}

    if re.search(r'(increase|decrease).*volume.*by\s*([0-9]+)', cmd):
        delta = int(re.findall(r'[0-9]+', cmd)[0])
        if "decrease" in cmd: delta = -delta
        return {"action": "write_only", "target": "", "content": adjust_volume(delta)}

    if re.search(r'volume.*([0-9]+)', cmd):
        volume = int(re.findall(r'[0-9]+', cmd)[0])
        return {"action": "write_only", "target": "", "content": adjust_volume(volume, absolute=True)}

    # ⏰ Timers and alarms
    alarm_result = set_timer_or_alarm(cmd)
    if alarm_result:
        return {"action": "write_only", "target": "", "content": alarm_result}

    # 🚀 App launching
    if match := re.search(r'\b(open|launch|start)\s+([\w\s]+)', cmd):
        return {"action": "open_app", "target": match.group(2).strip(), "content": ""}

    # 💬 Natural language "tell me..."
    if cmd.startswith("tell me ") or cmd.startswith("tell "):
        prompt = command.strip().capitalize()
        generated = ask_groq(
            prompt,
            system_message="You are a creative assistant. Respond conversationally and directly. Avoid links or markdown. Just give a natural response in plain text."
        )
        return {
            "action": "message_only",
            "target": "",
            "content": generated
        }

    # 🧠 Fallback to Groq instruction
    response = ask_groq(command)
    print(f"🤖 Groq Response: {response}")

    try:
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON found", response, 0)

        action_obj = json.loads(json_match.group(0))
        action = action_obj.get("action")
        target = action_obj.get("target")
        content = action_obj.get("content")

        if action:
            return {
                "action": action,
                "target": target or "",
                "content": content or ""
            }

        return {
            "action": "write_only",
            "target": "",
            "content": f"I couldn't understand how to handle this task: {command}"
        }

    except json.JSONDecodeError:
        print("⚠️ Failed to parse Groq response as JSON.")
        return {
            "action": "write_only",
            "target": "",
            "content": f"I couldn't parse Groq's response for: {command}"
        }



    
def generate_and_type_content(command):
    """
    Uses Groq to convert a natural language command into a file-writing action.
    Expects Groq to return a JSON like:
    {
      "file_name": "notes.txt",
      "content": "This is what should go into the file."
    }
    Then writes the content to the file.
    """
    system_message = (
        "You are a file-writing assistant. Given a user command like "
        "'write hello in text.txt' or 'save this to file xyz.txt', respond ONLY with a JSON object "
        "in this format: {\"file_name\": \"filename.txt\", \"content\": \"what to write in the file\"}. "
        "Do not include any other explanation, just the raw JSON."
    )

    response = ask_groq(command, system_message=system_message)

    try:
        data = json.loads(response)

        file_name = data.get("file_name")
        content = data.get("content")

        if not file_name or not content:
            return "❌ Invalid response format from Groq."

        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)

        return f"✅ Successfully wrote to {file_name}"

    except json.JSONDecodeError:
        return f"❌ Groq did not return valid JSON:\n{response}"
    except Exception as e:
        return f"❌ Failed to write to file: {e}"