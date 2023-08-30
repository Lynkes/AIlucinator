import tkinter as tk
from tkinter import font

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculator")

        self.entry_font = font.Font(size=20)
        self.button_font = font.Font(size=15, weight='bold')

        self.entry = tk.Entry(root, font=self.entry_font, bd=10, insertwidth=4, width=15)
        self.entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        self.create_buttons()

    def create_buttons(self):
        button_texts = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
        ]

        for text, row, col in button_texts:
            button = tk.Button(self.root, text=text, font=self.button_font, command=lambda t=text: self.button_click(t))
            button.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Configure button colors for a nicer look
            if text.isnumeric() or text == '.':
                button.configure(bg="#E0E0E0")
            elif text == '=':
                button.configure(bg="#4CAF50", fg="white")
            else:
                button.configure(bg="#F5A623")

    def button_click(self, value):
        if value == "=":
            try:
                result = eval(self.entry.get())
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, str(result))
            except:
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, "Error")
        else:
            current_text = self.entry.get()
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, current_text + value)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
