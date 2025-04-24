import tkinter as tk
from tkinter import ttk

popup_ui_root = None
status_var = None
output_text = None

def create_ui():
    global popup_ui_root, status_var, output_text
    popup_ui_root = tk.Tk()
    popup_ui_root.title("GroqMate Assistant")
    popup_ui_root.geometry("400x300")
    popup_ui_root.resizable(False, False)

    header = ttk.Label(popup_ui_root, text="GroqMate", font=("Helvetica", 18, "bold"))
    header.pack(pady=10)

    output_text = tk.Text(popup_ui_root, height=10, wrap="word", font=("Helvetica", 10))
    output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    output_text.config(state=tk.DISABLED)

    status_var = tk.StringVar(value="Waiting for wake word...")
    status_label = ttk.Label(popup_ui_root, textvariable=status_var, font=("Helvetica", 10, "italic"))
    status_label.pack(pady=(0, 10))

    return popup_ui_root

def update_status(status):
    if popup_ui_root:
        popup_ui_root.after(0, lambda: status_var.set(status))

def display_message(message):
    if popup_ui_root:
        def append():
            output_text.config(state=tk.NORMAL)
            output_text.insert(tk.END, message + "\n")
            output_text.config(state=tk.DISABLED)
            output_text.see(tk.END)
        popup_ui_root.after(0, append)

def show_listening():
    update_status("🎙️ Listening for command...")

def show_transcribed(user_input):
    update_status("📝 Processing...")
    display_message(f"You: {user_input}")

def show_response(response):
    update_status("✅ Response received")
    display_message(f"GroqMate: {response}")