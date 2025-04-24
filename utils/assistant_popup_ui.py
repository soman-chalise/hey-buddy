import tkinter as tk
from tkinter import ttk
import sys

if sys.platform == "win32":
    import ctypes

BG_COLOR = "#141628"
TEXT_COLOR = "#ffffff"
ACCENT_COLOR = "#6366f1"
STATUS_BG = "#1e2038"
FONT = ("Segoe UI", 11)
TITLE_FONT = ("Segoe UI", 14, "bold")

status_label = None
response_text = None
canvas = None
scrollbar = None

def create_ui():
    global status_label, response_text, canvas, scrollbar

    root = tk.Tk()
    root.overrideredirect(True)  
    root.attributes("-topmost", True) 

    window_width = 450
    window_height = 300

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = screen_width - window_width - 20
    y = screen_height - window_height - 50
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)

    if sys.platform == "win32":
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
        style = style & ~0x00020000  
        ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background=ACCENT_COLOR,
        troughcolor=STATUS_BG,
        bordercolor=STATUS_BG,
        arrowcolor=ACCENT_COLOR,
        relief="flat"
    )

    # === Layout ===
    container = tk.Frame(root, bg=STATUS_BG)
    container.pack(fill="both", expand=True, padx=10, pady=10)

    # === Top bar with title and close button ===
    top_bar = tk.Frame(container, bg=ACCENT_COLOR)
    top_bar.pack(fill="x")

    tk.Label(top_bar, text=" Hey-Buddy Assistant", font=TITLE_FONT, fg="#ffffff", bg=ACCENT_COLOR).pack(side="left", padx=10)

    close_btn = tk.Button(
        top_bar, text="×", font=("Segoe UI", 14), fg="#ffffff", bg=ACCENT_COLOR,
        bd=0, relief="flat", activebackground="#4f52d3", cursor="hand2",
        command=root.withdraw

    )
    close_btn.pack(side="right", padx=10)

    # === Scrollable response area ===
    response_frame = tk.Frame(container, bg=STATUS_BG)
    response_frame.pack(fill="both", expand=True, pady=(10, 5))

    canvas = tk.Canvas(response_frame, bg=STATUS_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(response_frame, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")

    scroll_frame = tk.Frame(canvas, bg=STATUS_BG)
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack_forget()

    response_text = tk.Label(scroll_frame, text="", font=FONT, fg="#c0c3ff", bg=STATUS_BG, justify="left", wraplength=400)
    response_text.pack(anchor="w")

    # === Bottom-left status bar ===
    status_label = tk.Label(root, text="Status: Idle", font=FONT, fg="#aaaaaa", bg=BG_COLOR, anchor="w")
    status_label.pack(side="left", anchor="sw", padx=10, pady=5)

    return root


def update_status(message):
    if status_label:
        status_label.config(text=f"Status: {message}")

def show_listening():
    update_status("🎙️ Listening...")

def show_transcribed(text):
    update_status(f"📝 Transcribed: {text}")

def show_response(text):
    if response_text:
        response_text.config(text=text)
        update_scrollbar_visibility()

def update_scrollbar_visibility():
    canvas.update_idletasks()
    scroll_height = canvas.bbox("all")[3]
    visible_height = canvas.winfo_height()

    if scroll_height > visible_height:
        scrollbar.pack(side="right", fill="y")
    else:
        scrollbar.pack_forget()
