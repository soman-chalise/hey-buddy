import os
import sys
import subprocess
import time
import threading
import psutil

# Add the local SDK path
sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "desktop_use"))
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from desktop_use import DesktopUseClient

# -------------------------------
# ✅ Ensure server.exe is running
# -------------------------------
def ensure_terminator_server_running():
    exe_name = "server.exe"

    # Check if already running
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
            print("🟢 Terminator server already running.")
            return

    # Start server.exe from current folder
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

# Start the server before creating the client
ensure_terminator_server_running()
client = DesktopUseClient()

# --------------------
# Click by label
# --------------------
def click_by_label(label):
    try:
        element = client.locator(f"name:{label.lower().strip()}")
        element.click()
        return f"🖱️ Clicked '{label}'"
    except Exception as e:
        return f"❌ Failed to click '{label}': {e}"

# --------------------
# Type into a labeled field
# --------------------
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
stop_typing_flag = False

def type_text_into_active_window(text):
    global stop_typing_flag
    stop_typing_flag = False

    def typing_task():
        try:
            element = client.locator("active:true")
            for char in text:
                if stop_typing_flag:
                    print("⛔ Typing interrupted.")
                    break
                element.type_text(char)
        except Exception as e:
            print(f"❌ Could not type into screen: {e}")

    thread = threading.Thread(target=typing_task)
    thread.start()

    print("🔄 Press [Enter] to stop typing...")
    try:
        input()
        stop_typing_flag = True
    except KeyboardInterrupt:
        stop_typing_flag = True

# --------------------
# Read all UI labels on screen
# --------------------
def list_ui_elements():
    try:
        elements_response = client.locator("any").all()
        labels = [el["label"] for el in elements_response["elements"] if el.get("label")]
        if not labels:
            return "🔍 No labeled UI elements found on screen."
        return f"🧾 Found elements: {', '.join(labels)}"
    except Exception as e:
        return f"❌ Could not list UI elements: {e}"
