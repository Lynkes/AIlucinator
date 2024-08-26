from tkinter import filedialog

def select_folder():
    folder_path = filedialog.askdirectory(title="Select Folder")
    
    if folder_path:
        print(f"Selected Folder: {folder_path}")
        return folder_path
    else:
        print("No folder selected.")

if __name__ == "__main__":
    select_folder()
