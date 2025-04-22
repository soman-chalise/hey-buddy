import tkinter as tk
from tkinter import ttk
import json
import os
from collections import defaultdict
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.assistant_popup_ui import AssistantPopup
from utils.tasks import handle_task
from utils.execute_ai_task import execute_ai_task

LOG_FILE = "activity_log.jsonl"

MODERN_COLORS = [
    "#ff6f61", "#6b5b95", "#88b04b", "#f7cac9", "#92a8d1",
    "#955251", "#b565a7", "#009b77", "#dd4124", "#45b8ac"
]

from utils.api import classify_command, ask_groq

def show_chat_popup(question, answer):
    chat_win = tk.Toplevel()
    chat_win.title("GroqMate Q&A")
    chat_win.configure(bg="#1e1e2f")
    chat_win.geometry("420x300+100+100")
    chat_win.attributes("-topmost", True)

    text = tk.Text(chat_win, bg="#1e1e2f", fg="#ffffff", wrap="word", font=("Segoe UI", 10), bd=0)
    text.pack(fill="both", expand=True, padx=10, pady=10)
    text.tag_config("question", foreground="#80dfff", font=("Segoe UI", 10, "bold"))
    text.tag_config("answer", foreground="#ffffff")

    text.insert("end", f"You: {question}\n\n", "question")
    text.insert("end", f"Assistant: {answer}\n", "answer")
    text.config(state="disabled")


def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def parse_duration(duration_str):
    mins, secs = 0, 0
    try:
        if "m" in duration_str:
            parts = duration_str.split("m")
            mins = int(parts[0].strip())
            if "s" in parts[1]:
                secs = int(parts[1].replace("s", "").strip())
        elif "s" in duration_str:
            secs = int(duration_str.replace("s", "").strip())
    except:
        pass
    return mins * 60 + secs

def format_duration(seconds):
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s"

def aggregate(logs):
    usage = defaultdict(int)
    details = defaultdict(list)
    for entry in logs:
        title = entry["title"]
        base_app = title.split(" - ")[-1]
        duration = parse_duration(entry["duration"])
        usage[base_app] += duration
        details[base_app].append(entry)
    return usage, details

def assign_colors(keys):
    color_map = {}
    for i, key in enumerate(keys):
        color_map[key] = MODERN_COLORS[i % len(MODERN_COLORS)]
    return color_map

def launch_dashboard():
    logs = load_logs()
    if not logs:
        root = tk.Tk()
        root.title("GroqMate Dashboard")
        root.configure(bg="#1e1e2e")

        msg = tk.Label(root, text="⚠️ No activity logs yet.", font=("Segoe UI", 14), bg="#1e1e2e", fg="#ffffff")
        msg.pack(expand=True, padx=20, pady=20)

        root.mainloop()
        return

    usage, details = aggregate(logs)
    total_time = sum(usage.values())
    app_colors = assign_colors(usage.keys())

    root = tk.Tk()
    root.title("GroqMate Analytics Dashboard")
    root.geometry("1000x600")
    root.configure(bg="#1e1e2e")
    root.overrideredirect(True)

    root.bind("<Escape>", lambda e: root.destroy())

    top_bar = tk.Frame(root, bg="#181824", height=30)
    top_bar.pack(side=tk.TOP, fill=tk.X)

    def start_move(event):
        root.x = event.x
        root.y = event.y

    def do_move(event):
        x = event.x_root - root.x
        y = event.y_root - root.y
        root.geometry(f"+{x}+{y}")

    top_bar.bind("<ButtonPress-1>", start_move)
    top_bar.bind("<B1-Motion>", do_move)

    close_btn = tk.Button(top_bar, text="✕", font=("Segoe UI", 10, "bold"),
                          bg="#181824", fg="#bbbbbb",
                          activebackground="#222233", activeforeground="#ffffff",
                          bd=0, command=root.destroy)
    close_btn.pack(side=tk.RIGHT, padx=10, pady=3)

    left_frame = tk.Frame(root, bg="#1e1e2e", width=500)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    right_frame = tk.Frame(root, bg="#1e1e2e", width=500)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    title_label = tk.Label(left_frame, text="🧠 GroqMate Activity Insights", font=("Segoe UI", 16, "bold"), bg="#1e1e2e", fg="#ffffff")
    title_label.pack(pady=(10, 0))

    fig, ax = plt.subplots(figsize=(5, 5), facecolor="#1e1e2e")
    canvas = FigureCanvasTkAgg(fig, master=left_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(pady=(20, 10), fill=tk.BOTH, expand=True)

    center_label = tk.Label(left_frame, text="", font=("Segoe UI", 14), bg="#1e1e2e", fg="#ffffff")
    center_label.place(relx=0.5, rely=0.5, anchor="center")

    segment_info_label = tk.Label(left_frame, text="", font=("Segoe UI", 12, "bold"), bg="#1e1e2e", fg="#ffffff", wraplength=400)
    segment_info_label.place(relx=0.5, rely=0.85, anchor="center")

    back_btn = tk.Button(left_frame, text="← All Apps", font=("Segoe UI", 10),
                         bg="#2a2a3b", fg="#bbbbbb",
                         activebackground="#3a3a4f", activeforeground="#ffffff",
                         bd=0, relief="flat",
                         command=lambda: draw_donut())
    back_btn.pack(pady=(10, 0))

    def draw_donut(app_name=None):
        ax.clear()
        ax.set_facecolor("#1e1e2e")
        segment_info_label.config(text="")

        def on_click(event):
            if not hasattr(canvas, 'segments') or not canvas.segments:
                return
            for i, segment in enumerate(canvas.segments):
                if segment.contains(event)[0]:
                    label_clicked = canvas.segment_labels[i]
                    duration_clicked = canvas.segment_durations[i]
                    segment_info_label.config(text=f"{label_clicked}: {format_duration(int(duration_clicked))}")
                    break

        if hasattr(canvas, 'click_cid'):
            canvas.mpl_disconnect(canvas.click_cid)
        canvas.click_cid = canvas.mpl_connect('button_press_event', on_click)

        if app_name:
            entries = details[app_name]
            breakdown = defaultdict(int)
            for e in entries:
                summary = e.get("summary", "Unknown")
                breakdown[summary] += parse_duration(e["duration"])

            if not breakdown:
                return

            labels = list(breakdown.keys())
            times = [v for v in breakdown.values()]
            color_list = [MODERN_COLORS[i % len(MODERN_COLORS)] for i in range(len(labels))]
            wedges, _ = ax.pie(times, labels=None, startangle=140, colors=color_list,
                               wedgeprops=dict(width=0.4, edgecolor="#1e1e2e"))
            canvas.segments = wedges
            canvas.segment_labels = labels
            canvas.segment_durations = times
            center_label.config(text=app_name)
        else:
            labels = list(usage.keys())
            times = [usage[k] for k in labels]
            color_list = [app_colors[k] for k in labels]
            wedges, _ = ax.pie([t / 60 for t in times], labels=None, startangle=140, colors=color_list,
                               wedgeprops=dict(width=0.4, edgecolor="#1e1e2e"))
            canvas.segments = []
            canvas.segment_labels = []
            canvas.segment_durations = []
            center_label.config(text=format_duration(total_time))

        ax.add_artist(plt.Circle((0, 0), 0.70, fc='#1e1e2e'))
        canvas.draw()

    draw_donut()

    app_container = tk.Frame(right_frame, bg="#1e1e2e")
    app_container.place(relx=0.5, rely=0.45, anchor="center")

    def on_app_click(app_name):
        draw_donut(app_name)

    for app in sorted(usage.keys(), key=lambda a: -usage[a]):
        duration_str = format_duration(usage[app])

        btn_frame = tk.Frame(app_container, bg="#2a2a3b", highlightthickness=0)
        btn_frame.pack(fill=tk.X, pady=6, ipadx=4, ipady=4)

        color_bar = tk.Frame(btn_frame, width=6, bg=app_colors[app])
        color_bar.pack(side=tk.LEFT, fill=tk.Y)

        btn = tk.Button(
            btn_frame,
            text=app,
            command=lambda a=app: on_app_click(a),
            font=("Segoe UI", 10),
            bg="#2a2a3b",
            fg="#ffffff",
            activebackground="#3a3a4f",
            activeforeground="#ffffff",
            relief="flat",
            anchor="w",
            padx=10,
            bd=0
        )
        btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        time_lbl = tk.Label(btn_frame, text=duration_str, font=("Segoe UI", 10), bg="#2a2a3b", fg="#aaaaaa")
        time_lbl.pack(side=tk.RIGHT, padx=10)

    command_frame = tk.Frame(right_frame, bg="#1e1e2e")
    command_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

    command_entry = tk.Entry(
        command_frame,
        font=("Segoe UI", 10),
        bg="#2a2a3b",
        fg="#ffffff",
        insertbackground="#ffffff",
        relief="flat"
    )
    command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=6)



    def run_command():
        cmd = command_entry.get().strip()
        if cmd:
            command_entry.delete(0, tk.END)
            command_type = classify_command(cmd)

            if command_type == "question":
                try:
                    answer = ask_groq(
                        cmd,
                        system_message="You are a helpful assistant. Answer clearly in plain language. No links or extra fluff."
                    )
                    show_chat_popup(cmd, answer)
                except Exception as e:
                    popup = AssistantPopup()
                    popup.set_response(f"❌ Question error: {e}", auto_close=False)

            else:
                try:
                    popup = AssistantPopup()
                    popup.set_processing(cmd)
                    result = handle_task(cmd)
                    message = execute_ai_task(result)
                    popup.set_response(message, auto_close=False)
                except Exception as e:
                    popup = AssistantPopup()
                    popup.set_response(f"❌ Task error: {e}", auto_close=False)


if __name__ == "__main__":
    launch_dashboard()
