import os
import threading
import time
from utils.voice import listen_and_transcribe
from utils.wake import listen_for_wake_word
from utils.api import rule_based_classify_command
from utils.tasks import handle_task
from utils.activity_tracker import track_activity
from utils.screenpipe import type_text_into_active_window, launch_app_via_terminator
from utils.assistant_popup_ui import create_ui, show_listening, show_transcribed, show_response, update_status

# Start background activity tracker
threading.Thread(target=track_activity, daemon=True).start()

ui_root = None  # Will hold the popup UI window

def handle_response(action, content, target):
    if action == "message_only":
        show_response(content)
        print(f"Response: {content}")

    elif action == "write_only":
        show_response(content)
        print(f"Task: {content}")

    elif action == "insert_text":
        print(f"⌨️ Typing into active window: {content}")
        type_text_into_active_window(content)

    elif action == "save_file":
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"💾 Saved to {target}")

    elif action == "open_url":
        os.system(f'start msedge "{target}"')
        print(f"🌐 Opened URL: {target}")

    elif action == "open_app":
        launch_app_via_terminator(target)
        print(f"🚀 Launched app: {target}")

    elif action == "screen_vision":
        show_listening()
        print(f"🔍 Analyzing screen: {content}")
        from utils.vision import analyze_screen_with_groq_vision
        result = analyze_screen_with_groq_vision(prompt=content, mode="screen_qa")
        show_response(result)
        print(f"🧠 Vision result: {result}")

    else:
        print(f"⚠️ Unknown action: {action}")

def listen_for_commands():
    global ui_root
    ui_root.withdraw()  # Hide the popup initially

    while True:
        update_status("🎙️ Listening for wake word...")
        listen_for_wake_word()

        ui_root.deiconify()  # Show popup after wake word
        show_listening()

        command = listen_and_transcribe()
        if not command:
            update_status("❌ No command detected.")
            continue

        show_transcribed(command)

        command_type = rule_based_classify_command(command)
        result = handle_task(command, command_type)
        action = result.get("action")
        target = result.get("target", "")
        content = result.get("content", "")

        show_response(content)
        handle_response(action, content, target)

def main():
    global ui_root
    ui_root = create_ui()  # Create UI in main thread

    # Start the command listening in a background thread
    threading.Thread(target=listen_for_commands, daemon=True).start()

    print("🚀 GroqMate is running. Waiting for wake word...")
    ui_root.mainloop()  # Must be in the main thread

if __name__ == "__main__":
    main()
