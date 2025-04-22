import tkinter as tk

class AssistantPopup:
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.withdraw()  # Hide initially
        self.root.title("GroqMate Assistant")
        self.root.configure(bg="#1e1e2f")
        self.root.attributes("-topmost", True)  # Always on top
        self.root.overrideredirect(True)  # Remove the default title bar

        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Initial size of the popup (around 1/4 of the screen height)
        self.popup_width = 400
        self.popup_height = int(screen_height / 4)
        self.root.geometry(f"{self.popup_width}x{self.popup_height}+{screen_width - self.popup_width - 50}+{screen_height - self.popup_height - 50}")

        # Frame to hold all elements
        self.frame = tk.Frame(self.root, bg="#1e1e2f", bd=0, highlightthickness=0)
        self.frame.pack(fill="both", expand=True)

        # Custom header bar with request/question
        self.header_frame = tk.Frame(self.frame, bg="#2a2a3b", height=25)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)

        # Close button inside the header bar
        self.close_btn = tk.Button(self.header_frame, text="❌", font=("Segoe UI", 10),
                                   command=self.close, bg="#2a2a3b", fg="#ffffff",
                                   activebackground="#3a3a4f", activeforeground="#ffffff",
                                   relief="flat", width=3, height=1, bd=0)
        self.close_btn.pack(side=tk.LEFT, padx=5, pady=3)

        self.header_label = tk.Label(self.header_frame, text="", font=("Segoe UI", 12, "bold"),
                                     fg="#ffffff", bg="#2a2a3b", anchor="w", padx=10, pady=5)
        self.header_label.pack(side=tk.LEFT, fill="both", expand=True)

        # Scrollable Frame for response text
        self.scrollable_frame = tk.Canvas(self.frame, bg="#1e1e2f")
        self.scrollable_frame.pack(fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.scrollable_frame.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.scrollable_frame.config(yscrollcommand=self.scrollbar.set)

        self.response_label = tk.Label(self.scrollable_frame, text="", font=("Segoe UI", 10),
                                       fg="#ffffff", bg="#1e1e2f", anchor="w", padx=10, pady=10,
                                       wraplength=self.popup_width - 20)  # Wrap text
        self.response_label.pack(fill="both", expand=True)

        # Response bar at the bottom left for "Listening" or "Processing"
        self.response_bar = tk.Label(self.frame, text="Listening...", font=("Segoe UI", 10),
                                     fg="#ffffff", bg="#2a2a3b", anchor="w", padx=10, pady=10)
        self.response_bar.pack(side=tk.BOTTOM, fill="x", expand=False)

    def set_header(self, text):
        # Set the header to show the request/question
        self.header_label.config(text=text)
        self.root.update()

    def set_response(self, text, processing=False):
        # Set the response message (Listening, Processing, or the final answer/task result)
        if processing:
            self.response_bar.config(text="Processing...")
        else:
            self.response_bar.config(text="")
            self.response_label.config(text=text)  # Set the AI response in the scrollable area

        # Adjust the height of the popup if the response is large
        self.adjust_popup_size(text)
        self.root.update()

    def adjust_popup_size(self, text):
        """Adjust the size of the popup based on the length of the response text"""
        # Check the length of the text
        lines = text.split('\n')
        max_lines = len(lines)
        if max_lines > 10:  # If the response is large
            new_height = min(int(self.popup_height + max_lines * 10), self.root.winfo_screenheight() - 50)  # Cap the height
            self.root.geometry(f"{self.popup_width}x{new_height}+{self.root.winfo_x()}+{self.root.winfo_y()}")
        else:
            self.root.geometry(f"{self.popup_width}x{self.popup_height}+{self.root.winfo_x()}+{self.root.winfo_y()}")

    def show(self):
        self.root.deiconify()  # Show the popup
        self.root.lift()
        self.root.update()

    def close(self):
        self.root.withdraw()  # Hide the popup
