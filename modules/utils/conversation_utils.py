import json
import os
import re
import subprocess
import globals
from typing import Any, List, Optional, Sequence, Tuple
#PATHS i need
'''
conversations\GLaDOS
Allucinator-Refactor\conversations\GLaDOS\chroma
Allucinator-Refactor\conversations\GLaDOS\conversation_{all}.json
Allucinator-Refactor\conversations\GLaDOS\GLaDOS.txt
Allucinator-Refactor\conversations\GLaDOS\filtered_words.txt
Allucinator-Refactor\conversations\GLaDOS\keyword_map.json
'''

def check_quit(user_input:str):
    if user_input.lower() == "quit" or "quit." in user_input.lower():
        raise SystemExit

# Moved over to yaml, but if json format is needed, replace .yaml with
# .json and use json.dump(messages, file, indent=4, ensure_ascii=False)
def get_suffix(save_foldername: str):
    os.makedirs(save_foldername, exist_ok=True)
    base_filename = 'conversation'
    suffix = 0
    filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.json')

    while os.path.exists(filename):
        suffix += 1
        filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.json')
    
    return suffix

def load_inprogress(save_foldername):
    base_filename = 'conversation'
    print("LOADING-CONVERSATION")
    suffix = 0
    while True:
        filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.json')
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                messages = json.load(file)
                return messages
        else:
            break  # Exit the loop if the file doesn't exist
        suffix += 1

def save_inprogress(messages, save_foldername):
    suffix = get_suffix(save_foldername)
    os.makedirs(save_foldername, exist_ok=True)
    base_filename = 'conversation'
    filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.json')

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(messages, file, ensure_ascii=False, indent=4)

def get_executable_path(keyword_map, action, name):
    for mapping in keyword_map:
        if mapping['action'].lower() == action.lower() and mapping['name'].lower() == name.lower():
            return mapping['path']
    return None

# Load the filtered words from a text file
def load_filtered_words(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]
    
# Load the keyword map from a JSON file
def load_keyword_map(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)['mappings']

def filter_paragraph(paragraph, filtered_words=None, keyword_map=None) -> list:
    # Initialize control flags
    filtered_words_scan = bool(filtered_words)
    keyword_map_scan = bool(keyword_map)

    if not filtered_words:
        filtered_words = []
        print("filtered_words is Empty")
    if not keyword_map:
        keyword_map = []
        print("keyword_map is Empty")

    # Remove all text enclosed in '**'
    paragraph = re.sub(r'\*.*?\*', '', paragraph)
    
    paragraph = paragraph.replace('\n', ' ')  # Replace new lines with spaces
    sentences = paragraph.split('. ')
    filtered_list = []
    current_sentence = ""

    for sentence in sentences:
        # Replace filtered words
        if filtered_words_scan:
            for word in filtered_words:
                sentence = sentence.replace(word, 'filtered')

        # Process keyword map actions
        if keyword_map_scan:
            words = sentence.split()
            for i in range(len(words) - 1):
                action = words[i].lower()
                name = words[i + 1].lower()
                path = get_executable_path(keyword_map, action, name)
                if path:
                    print(f"Found executable path for '{action} {name}': {path}")
                    user_query = input("\nDo you allow the execution ('Y' or 'N'): ")
                    if user_query.lower() == 'y':
                        subprocess.run([path])
                    else:
                        print(f"Execution of {action} {name} not allowed.")

        # Split sentence by conjunctions and commas for natural pauses
        sentence_parts = sentence.split(', ')  # Split by commas
        for part in sentence_parts:
            if len(current_sentence + part) <= len(paragraph)/2:  # Example length limit for a natural sentence
                current_sentence += part + ', '
            else:
                if current_sentence.strip():  # Check if the current sentence is not just spaces
                    filtered_list.append(current_sentence.strip())
                current_sentence = part + ', '

    # Append any remaining sentence
    if current_sentence.strip():
        filtered_list.append(current_sentence.strip())

    return filtered_list

def read_paragraph_from_file(file_path) -> str:
    with open(file_path, 'r') as file:
        paragraph = file.read()
    return paragraph

def get_path(name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, name)

def create_directory(name):
    dir_name = get_path(name)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def get_file_paths(script_dir:str, foldername:str, personality:str, system_change:str|None=None):
        foldername_dir = os.path.join(script_dir, f"conversations/{foldername}")
        personality_dir = get_personality_dir(foldername_dir, personality)
        if system_change:
            syschange_dir = os.path.join(script_dir, f"system_changes/{system_change}")
            return foldername_dir, personality_dir, syschange_dir
        else:
            return foldername_dir, personality_dir
        
def get_personality_dir(foldername_dir, personality):
     personality_dir = os.path.join(foldername_dir + "/" + personality + ".txt")
     return personality_dir

def process_sentence(current_sentence: List[str]):
        """
        Join text, remove inflections and actions, and send to the TTS queue.

        The LLM like to *whisper* things or (scream) things, and prompting is not a 100% fix.
        We use regular expressions to remove text between ** and () to clean up the text.
        Finally, we remove any non-alphanumeric characters/punctuation and send the text
        to the TTS queue.
        """
        sentence = "".join(current_sentence)
        sentence = re.sub(r"\*.*?\*|\(.*?\)", "", sentence)
        sentence = (
            sentence.replace("\n\n", ". ")
            .replace("\n", ". ")
            .replace("  ", " ")
            .replace(":", " ")
        )
        if sentence:
            return sentence
        else:
            return None
            #self.tts_generation_queue.put(sentence)

def process_line(line):
        """
        Processes a single line of text from the LLM server.

        Args:
            line (dict): The line of text from the LLM server.
        """

        if not line["stop"]:
            token = line["response"]
            return token
        return None

def clean_raw_bytes(line):
        """
        Cleans the raw bytes from the LLM server for processing.

        Coverts the bytes to a dictionary.

        Args:
            line (bytes): The raw bytes from the LLM server.
        """
        line = line.decode("utf-8")
        line = line.removeprefix("data: ")
        line = json.loads(line)
        return line