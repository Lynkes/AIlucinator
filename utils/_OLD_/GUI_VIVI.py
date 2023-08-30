import tkinter as tk

class TerminalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Classic Terminal")
        self.root.configure(bg="#292D3E")  # Set background color

        self.mode = None

        self.create_widgets()

    def create_widgets(self):
        self.terminal_output = tk.Text(self.root, wrap=tk.WORD, bg="#1E1E1E", fg="white")
        self.terminal_output.pack(fill=tk.BOTH, expand=True)
        self.terminal_output.config(state=tk.DISABLED)  # Initially disable editing

        self.input_entry = tk.Entry(self.root, bg="#2E2E2E", fg="white", insertbackground="white")
        self.input_entry.pack(fill=tk.X)
        self.input_entry.bind("<Return>", self.handle_input)

        self.mode_frame = tk.Frame(self.root, bg="#292D3E")
        self.mode_frame.pack()

        self.button_mic = tk.Button(self.mode_frame, text="Mic", command=lambda: self.toggle_mode("Mic"), bg="#383C4A", fg="white")
        self.button_mic.pack(side=tk.LEFT, padx=10, pady=5)

        self.button_youtube = tk.Button(self.mode_frame, text="YouTube Live", command=lambda: self.toggle_mode("YouTube Live"), bg="#383C4A", fg="white")
        self.button_youtube.pack(side=tk.LEFT, padx=10, pady=5)

        self.button_twitch = tk.Button(self.mode_frame, text="Twitch Live", command=lambda: self.toggle_mode("Twitch Live"), bg="#383C4A", fg="white")
        self.button_twitch.pack(side=tk.LEFT, padx=10, pady=5)

    def toggle_mode(self, mode):
        if self.mode == mode:
            self.mode = None
            self.button_mic.config(relief=tk.RAISED)
            self.button_youtube.config(relief=tk.RAISED)
            self.button_twitch.config(relief=tk.RAISED)
        else:
            self.mode = mode
            self.button_mic.config(relief=tk.SUNKEN if mode == "Mic" else tk.RAISED)
            self.button_youtube.config(relief=tk.SUNKEN if mode == "YouTube Live" else tk.RAISED)
            self.button_twitch.config(relief=tk.SUNKEN if mode == "Twitch Live" else tk.RAISED)

    def handle_input(self, event):
        input_text = self.input_entry.get()
        self.input_entry.delete(0, tk.END)

        self.terminal_output.config(state=tk.NORMAL)
        self.terminal_output.insert(tk.END, f">>> {input_text}\n", "input")
        if self.mode:
            self.terminal_output.insert(tk.END, f"Mode: {self.mode}\n", "mode")
        self.terminal_output.config(state=tk.DISABLED)
        self.terminal_output.tag_config("input", foreground="white")
        self.terminal_output.tag_config("mode", foreground="#5DADE2")
        self.terminal_output.see(tk.END)  # Scroll to the end of the terminal

if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalApp(root)
    root.mainloop()
