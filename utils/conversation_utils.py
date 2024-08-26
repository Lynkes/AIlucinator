import os

def save_conversation(messages: list, suffix: str, save_folderpath: str) -> None:
    """
    Saves the conversation messages to a file.
    
    :param messages: The conversation messages to save.
    :param suffix: Suffix to append to the filename.
    :param save_folderpath: The folder path where the conversation will be saved.
    """
    filename = os.path.join(save_folderpath, f"conversation_{suffix}.json")
    with open(filename, 'w') as f:
        json.dump(messages, f, indent=4)
    print(f"Conversation saved to {filename}")
