import pyautogui
import webbrowser
import subprocess
import time
import pyttsx3

# 🔊 Initialize TTS engine once
tts_engine = pyttsx3.init()

def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

def execute_ai_task(task):
    action = task.get("action")
    target = task.get("target")
    content = task.get("content")

    # ⌨️ Type into the current app
    if action == "write_only" and content:
        if not content.startswith(("✅", "❌", "🧾", "⚠️")):
            pyautogui.write(content, interval=0.05)
        return "✍️ Typed content successfully."

    # ⌨️ Insert directly into the window (used by code or poem gen)
    elif action == "insert_text" and content:
        pyautogui.write(content, interval=0.05)
        return "✍️ Inserted generated text."

    # 🌐 Open a URL
    elif action == "open_url" and target:
        webbrowser.open(target)
        return f"🌐 Opened URL: {target}"

    # 🚀 Open an app
    elif action == "open_app" and target:
        try:
            subprocess.Popen(f'start "" "{target}"', shell=True)
            return f"🚀 Launched {target}"
        except Exception as e:
            return f"❌ Failed to open {target}: {e}"

    # 💬 Simple message response
    elif action in ["send_message", "message_only"] and content:
        print(content)
        speak(content)
        return content

    # 💾 Save to file
    elif action == "save_file":
        filename = target or "output.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content or "")
            return f"💾 Saved to {filename}"
        except Exception as e:
            return f"❌ Error saving file: {e}"

    # ❌ Unknown
    else:
        print(f"⚠️ Unknown action type: {action}")
        return f"❓ Unknown action type: {action}"
