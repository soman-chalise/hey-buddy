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

threading.Thread(target=track_activity, daemon=True).start()

ui_root = None  

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
    from utils.voice import listen_and_transcribe
    from utils.api import rule_based_classify_command
    from utils.tasks import handle_task

    global ui_root
    ui_root.withdraw()

    while True:
        update_status("🎙️ Listening for wake word...")
        listen_for_wake_word()

        ui_root.deiconify()
        ui_root.update_idletasks()
        ui_root.update()
        show_response("")  


        show_listening()

        command = listen_and_transcribe()
        if not command:
            update_status("❌ No command detected.")
            show_response("❌ No speech detected.")
            continue

        update_status(f"🗣️ You said: {command}")
        show_transcribed(command)

        command_type = rule_based_classify_command(command)
        result = handle_task(command, command_type)

        action = result.get("action")
        target = result.get("target", "")
        content = result.get("content", "")

        message_lines = [f"🗣️ You said: {command}"]

        if action in ["insert_text", "save_file", "open_app", "open_url"]:
            summary = {
                "insert_text": "⌨️ Typed text into active window.",
                "save_file": f"💾 Code saved to `{target}`.",
                "open_app": f"🚀 Launched `{target}`.",
                "open_url": f"🌐 Opened: {target}"
            }.get(action, f"✅ Task: {action}")
            message_lines.append(summary)

        elif content:
            message_lines.append(content)

        combined_message = "\n".join(message_lines)
        show_response(combined_message)

        handle_response(action, content, target)




def main():
    global ui_root
    ui_root = create_ui()
    ui_root.update_idletasks() 
    ui_root.withdraw()       

    threading.Thread(target=listen_for_commands, daemon=True).start()

    print("🚀 GroqMate is running. Waiting for wake word...")
    ui_root.mainloop()  

if __name__ == "__main__":
    main()
