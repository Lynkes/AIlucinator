import json
import os
import winsound
import sounddevice as sd
import soundfile as sf
import yaml
import subprocess

#PATHS i need
'''
Allucinator-Refactor\conversations\GLaDOS\chroma
Allucinator-Refactor\conversations\GLaDOS\conversation_{all}.json
Allucinator-Refactor\conversations\GLaDOS\GLaDOS.txt
Allucinator-Refactor\conversations\GLaDOS\filtered_words.txt
Allucinator-Refactor\conversations\GLaDOS\keyword_map.json
'''

def check_quit(user_input:str):
    if user_input.lower() == "quit" or "quit." in user_input.lower():
        raise SystemExit

def beep():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        beep_path = os.path.join(script_dir, "resources", "beep.mp3")
        data, samplerate = sf.read(beep_path)
        sd.play(data, samplerate)
    except:
        # If `soundfile` fails, play a system beep instead
        duration = 500
        frequency = 500
        winsound.Beep(frequency, duration)

# Moved over to yaml, but if json format is needed, replace .yaml with
# .json and use json.dump(messages, file, indent=4, ensure_ascii=False)
def get_suffix(save_foldername: str):
    os.makedirs(save_foldername, exist_ok=True)
    base_filename = 'conversation'
    suffix = 0
    filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.yaml')

    while os.path.exists(filename):
        suffix += 1
        filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.yaml')
    
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
                print(messages)
                return messages
        else:
            break  # Exit the loop if the file doesn't exist
        suffix += 1

def save_inprogress(messages, suffix, save_foldername):
    os.makedirs(save_foldername, exist_ok=True)
    base_filename = 'conversation'
    filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.json')

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(messages, file, ensure_ascii=False, indent=4)
        
# Load the keyword map from a JSON file
def load_keyword_map(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)['mappings']

def get_executable_path(keyword_map, action, name):
    for mapping in keyword_map:
        if mapping['action'].lower() == action.lower() and mapping['name'].lower() == name.lower():
            return mapping['path']
    return None

# Load the filtered words from a text file
def load_filtered_words(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def filter_paragraph(paragraph, filtered_words=load_filtered_words("resources/Agent/filtered_words.txt"), keyword_map=load_keyword_map('resources/Agent/keyword_map.json')) -> list:
    #FORCE OFF
    sentence_len= len(paragraph)
    filtered_words_scan= False
    keyword_map_scan= False

    #FORCE OFF
    if filtered_words is None:
        filtered_words = []
        filtered_words_scan= False
        print("filtered_words is Empty")
    else:
        filtered_words_scan= True
    if keyword_map is None:
        keyword_map = []
        keyword_map_scan= False
        print("keyword_map is Empty")
    else:
        keyword_map_scan= True


    paragraph = paragraph.replace('\n', ' ')  # Replace new lines with spaces
    sentences = paragraph.split('. ')
    filtered_list = []
    current_sentence = ""

    for sentence in sentences:
        # Replace filtered words
        if filtered_words_scan == True:
            for word in filtered_words:
                sentence = sentence.replace(word, 'filtered')

        if keyword_map_scan == True:
            # Check and get executable paths from keyword_map
            words = sentence.split()
            for i in range(len(words) - 1):
                action = words[i].lower()
                name = words[i + 1].lower()
                path = get_executable_path(keyword_map, action, name)
                if path:
                    print(f"Found executable path for '{action} {name}': {path}")
                    userquery = input("\nDo you alow the execution ('Y'or 'N'): ")
                    if userquery.lower =="y":
                        result = subprocess.run([path])
                    else:
                        pass


        if len(current_sentence + sentence) <= sentence_len:
            current_sentence += sentence + '. '
        else:
            if current_sentence.strip():  # Check if the current sentence is not just spaces
                filtered_list.append(current_sentence.strip())
            current_sentence = sentence + '. '

    if current_sentence.strip():  # Check if the current sentence is not just spaces
        filtered_list.append(current_sentence.strip())

    return filtered_list

def read_paragraph_from_file(file_path) -> str:
    with open(file_path, 'r') as file:
        paragraph = file.read()
    return paragraph

def play_audio(audio_path):
    try:
        data, samplerate = sf.read(audio_path)
        sd.play(data, samplerate)
        sd.wait()

    except:
        return "FIN"
    # os.remove(audio_path)

def async_play_audio(audio_path):
    data, sample_rate = sf.read(audio_path)
    channels = data.shape[1] if len(data.shape) > 1 else 1
    data = data.astype('float32')  # Convert the data to float32
    with sd.OutputStream(samplerate=sample_rate, channels=channels) as stream:
        stream.write(data)

    # os.remove(audio_path)

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