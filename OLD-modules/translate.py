from googletrans import LANGUAGES, Translator
import tkinter as tk

def translate_text(text, target_language):
    try:
        translator = Translator()
        translation = translator.translate(text, dest=target_language)
        if translation:
            return translation.text
        else:
            print("Translation failed. Empty response received.")
            return ""
    except Exception as e:
        print(f"Translation error: {e}")
        return ""
    
def Select_language(text):
    root = tk.Tk()
    root.title("Select Prefered Output Language")
    
    # Create language selection dropdown
    language_options = sorted([(code, name) for code, name in LANGUAGES.items()], key=lambda x: x[1])
    language_names = [name for _, name in language_options]
    language_codes = [code for code, _ in language_options]
    language_mapping = dict(zip(language_names, language_codes))
    
    language_dropdown = tk.Combobox(root, values=language_names)
    language_dropdown.pack(padx=10, pady=10)
    language_dropdown.set("English")  # Default language selection
    
    translate_button = tk.Button(root, text="Translate", command=lambda: translate_text(text=text, target_language=language_mapping[language_dropdown.get()]), )
    translate_button.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    Select_language()
