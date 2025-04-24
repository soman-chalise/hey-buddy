import os
import re
import time
import threading
import subprocess
import pyautogui
import json
from datetime import datetime, timedelta
from utils.screenpipe import click_by_label, type_into_field, type_text_into_active_window, list_ui_elements,launch_app_via_terminator
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import ctypes
from utils.api import ask_groq, is_screen_vision_command
from utils.code import write_code_to_vscode
from utils.vision import analyze_screen_with_groq_vision

# ----------- Volume Control -------------
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

# ----------- Launch Apps -------------
def launch_app(app_name):
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"🚀 Launching {app_name}..."
    except Exception as e:
        return f"❌ Failed to launch {app_name}: {e}"

# ----------- Save Files -------------
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
def handle_task(command, command_type=None):
    cmd = command.lower().strip()

    # If not provided, classify now
    if not command_type:
        from utils.api import rule_based_classify_command
        command_type = rule_based_classify_command(cmd)

    # 🔍 Question → show popup
    if command_type == "question":
        generated = ask_groq(
            command.strip().capitalize(),
            system_message="You are a helpful assistant. Answer clearly and conversationally. No markdown or links."
        )
        return {
            "action": "message_only",
            "target": "",
            "content": generated
        }

    # 💻 Code generation
    if command_type == "code":
        code = ask_groq(
            command.strip(),
            system_message="You are a coding assistant. Return ONLY the code — no explanation, no markdown."
        )
        code = re.sub(r"```(?:\w+)?", "", code).replace("```", "").strip()
        write_code_to_vscode(code,cmd)
        filename = write_code_to_vscode(code, cmd)
        return {
                "action": "save_file",
                "target": filename,
                "content": code
            }



    # 📄 Write to specific file
    if command_type == "write_file":
        match = re.match(r"write\s+(.+?)\s+(?:in|into)\s+([\w\-.]+\.(txt|py|md|log|json|cpp|html))", cmd)
        if match:
            content, filename = match.group(1).strip(), match.group(2).strip()
            generated = ask_groq(
                f"Write an article or content about: {content}",
                system_message="You are a helpful assistant. Respond ONLY with the requested content — no markdown or explanation."
            )
            return {"action": "save_file", "target": filename, "content": generated}

    # 🧠 Groq Vision: Describe screen
    if command_type == "screen_vision":
        result = analyze_screen_with_groq_vision(prompt=command , mode="screen_qa")
        return {
            "action": "message_only",
            "target": "",
            "content": result
        }


    # 🧾 List UI elements
    if "list elements" in cmd or "list screen elements" in cmd:
        return {
            "action": "message_only",
            "target": "",
            "content": list_ui_elements()
        }

    # 🖱️ Click label
    if match := re.search(r'click (?:on )?(.*)', cmd):
        return {
            "action": "write_only",
            "target": "",
            "content": click_by_label(match.group(1).strip())
        }

    # ⌨️ Type X into Y
    if match := re.search(r'type (.+?) into (.+)', cmd):
        return {
            "action": "write_only",
            "target": "",
            "content": type_into_field(match.group(2).strip(), match.group(1).strip())
        }

    # ⌨️ Type into active window
    if match := re.search(r'type here (.+)', cmd):
        type_text_into_active_window(match.group(1).strip())
        return {
            "action": "write_only",
            "target": "",
            "content": "⌨️ Typing into active window... (Click to stop)"
        }

    # 🧠 Groq Vision: Describe screen
    if is_screen_vision_command(cmd):
        result = analyze_screen_with_groq_vision(prompt=command)
        return {
            "action": "message_only",
            "target": "",
            "content": result
        }

    # ✍️ Write plain text
    if re.search(r"(type|write).*?(here|over here|on screen|in active window)", cmd.lower()):
        return {
            "action": "insert_text",
            "target": "",
            "content": cmd.strip()  # ✅ Send full command to screenpipe
    }

    # 📄 Write to specific file
    if match := re.match(r"write\s+(.*?)\s+(?:in|into)\s+([\w\-.]+\.(txt|py|md|log|json|cpp|html))", cmd):
        content, filename = match.group(1).strip(), match.group(2).strip()
        generated = ask_groq(
            f"Write an article or content about: {content}",
            system_message="You are a helpful assistant. Respond ONLY with the requested content — no markdown or explanation."
        )
        return {"action": "save_file", "target": filename, "content": generated}

    # 🔍 Web search
    if match := re.search(r'(search|look up|google)\s+(.*)', cmd):
        query = match.group(2).strip()
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return {"action": "open_url", "target": url, "content": ""}

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
        
    # 📊 Show smart dashboard
    if any(kw in cmd for kw in ["show analytics", "display analytics", "open dashboard", "show dashboard", "display screen time", "show screen time"]):
        try:
            subprocess.Popen(["python", "utils/tk_dashboard.py"])
            return {"action": "write_only", "target": "", "content": "📊 Opening Smart Activity Dashboard..."}
        except Exception as e:
            return {"action": "write_only", "target": "", "content": f"❌ Failed to open dashboard: {e}"}

    # 🧠 Fallback: let Groq decide
    # 🧠 Fallback: let Groq decide
    response = ask_groq(command)
    print(f"🤖 Groq Response: {response}")

    try:
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON found", response, 0)

        action_obj = json.loads(json_match.group(0))
        action = action_obj.get("action", "").lower()
        target = action_obj.get("target", "")
        content = action_obj.get("content", "")

        # CASE: Treat "other" as question
        if action == "other":
            return {
                "action": "message_only",
                "target": "",
                "content": ask_groq(
                    command,
                    system_message="You are a helpful assistant. Answer the question clearly. No markdown or extras."
                )
            }

        # CASE: Action is known and valid
        if action in [
            "open_app", "insert_text", "message_only", "write_only", "save_file", 
            "open_url", "screen_vision"
        ]:
            return {
                "action": action,
                "target": target,
                "content": content
            }

        # Unknown action
        return {
            "action": "message_only",
            "target": "",
            "content": f"⚠️ Sorry, I don't know how to handle that action: '{action}'"
        }

    except json.JSONDecodeError:
        print("⚠️ Failed to parse Groq response as JSON.")
        return {
            "action": "message_only",
            "target": "",
            "content": "⚠️ I couldn't understand the response. Please try rephrasing your command."
        }
