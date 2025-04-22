import tkinter as tk
import time
from utils.voice import listen_and_transcribe
from utils.wake import listen_for_wake_word
from utils.api import ask_groq, classify_command
from utils.tasks import handle_task
from utils.execute_ai_task import execute_ai_task
from utils.assistant_popup_ui import AssistantPopup

def assistant_loop():
    print("🟢 GroqMate is running. Waiting for wake word...")

    # Initialize popup (but it is hidden initially)
    popup = AssistantPopup()

    while True:
        if listen_for_wake_word():
            print("👂 Wake word detected. Listening for command...")

            # Show popup and set initial status
            popup.show()
            popup.set_response("Listening...", processing=False)

            # Capture the user's voice command after the wake word
            command = listen_and_transcribe()

            if not command:
                print("⚠️ No voice input detected. Try again.")
                continue

            print(f"🗣️ Heard: {command}")

            # Show the request in the header of the popup
            popup.set_header(f"Request: {command}")

            # Classify the command type (task or question)
            command_type = classify_command(command)
            print(f"📌 Classified as: {command_type}")

            # Show "Processing" in the response bar
            popup.set_response("Processing...", processing=True)

            # Handle task or question accordingly
            if command_type == "task":
                try:
                    task_data = handle_task(command)

                    if isinstance(task_data, dict):
                        result = execute_ai_task(task_data)
                        popup.set_response(f"Task Result: {result}", processing=False)  # Show task result
                    else:
                        popup.set_response("⚠️ Invalid task data.", processing=False)
                except Exception as e:
                    print(f"❌ Task error: {e}")
                    popup.set_response(f"❌ Task error: {e}", processing=False)

            elif command_type == "question":
                try:
                    response = ask_groq(command)
                    popup.set_response(f"Answer: {response}", processing=False)  # Show answer
                except Exception as e:
                    print(f"❌ Error during Q&A: {e}")
                    popup.set_response(f"❌ Error: {e}", processing=False)
            else:
                print("🤔 Couldn't confidently classify the command. Trying to handle it as a task...")
                try:
                    task_data = handle_task(command)
                    if isinstance(task_data, dict):
                        result = execute_ai_task(task_data)
                        popup.set_response(f"Fallback Task Result: {result}", processing=False)  # Show fallback result
                    else:
                        popup.set_response("⚠️ Fallback task handler returned invalid data.", processing=False)
                except Exception as e:
                    print(f"❌ Error in fallback task handling: {e}")
                    popup.set_response(f"❌ Error in fallback handling: {e}", processing=False)

if __name__ == "__main__":
    assistant_loop()
