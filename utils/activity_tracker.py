import time
import pygetwindow as gw
from datetime import datetime
import sys
import os
import json
from PIL import ImageGrab
from tkinter import messagebox, Tk


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.vision import analyze_screen_with_groq_vision  # ✅ Use Groq Vision for screenshot summary


LOG_FILE = "activity_log.jsonl"
current_app = None
start_time = time.time()

def get_active_window_title():
    try:
        win = gw.getActiveWindow()
        return win.title if win else None
    except:
        return None

def format_duration(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}m {secs}s"

def summarize_screenshot():
    """Take screenshot and summarize using Groq Vision."""
    screenshot = ImageGrab.grab()
    screenshot_path = "current_screen.png"
    screenshot.save(screenshot_path)
    try:
        summary = analyze_screen_with_groq_vision(image_path=screenshot_path, mode="dashboard")
        return summary
    except Exception as e:
        return f"⚠️ Groq Vision error: {e}"

def log_event_locally(app, duration, summary):
    """Log event locally for pie chart dashboard."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "title": app,
        "duration": duration,
        "summary": summary
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"❌ Failed to log entry: {e}")

def track_activity(interval=5):
    """Main activity tracking loop."""
    global current_app, start_time

    print("🟢 GroqMate Activity Tracker running...")

    while True:
        active = get_active_window_title()

        if active and active != current_app:
            end_time = time.time()
            if current_app:
                duration = end_time - start_time
                try:
                    summary = summarize_screenshot()
                except Exception as e:
                    summary = f"⚠️ Vision error: {e}"

                log_event_locally(current_app, format_duration(duration), summary)

            current_app = active
            start_time = time.time()

        time.sleep(interval)

if __name__ == "__main__":
    track_activity(interval=10)
