import os, sys
from colorama import *
from resources import kokoro
from resources import assistant_p
from resources.utils import get_file_paths

def LOAD_ENV():
    # If user didn't rename example.env
    if os.path.exists("example.env") and not os.path.exists(".env"):
        os.rename("example.env", ".env")
        print(Style.BRIGHT + Fore.RED +"Renamed example.env to .env")
    else:
        print(Fore.LIGHTGREEN_EX+"***AI Starting***")
        print("Loading .env")

    # Load settings from .env file
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split('=', 1)
            os.environ[key] = value

def Check():
    # Check virtual env
    if os.environ.get('VIRTUAL_ENV'):
        # The VIRTUAL_ENV environment variable is set
        print(Style.BRIGHT+Fore.GREEN+'You are in a virtual environment:', os.environ['VIRTUAL_ENV'])
    elif sys.base_prefix != sys.prefix:
        # sys.base_prefix and sys.prefix are different
        print(Style.BRIGHT+Fore.BLUE+'You are in a virtual environment:', sys.prefix)
    else:
        # Not in a virtual environment
        print(Style.BRIGHT + Fore.RED + 'You are not in a virtual environment, we\'ll continue anyways')

LOAD_ENV()
Check()
# The only variables that need to be modifed in .ENV
foldername = os.environ.get('foldername')
personality = os.environ.get('personality')
attention_personality = os.environ.get('attention_personality')
voicename = os.environ.get('voicename')
assistant_name = os.environ.get('assistant_name')
tts = os.environ.get('TTS')
video_id = os.environ.get('video_id')
speech_recog = os.environ.get('speech_recog')
rvc_model_path = os.environ.get('rvc_model_path')
gptmodel = os.environ.get('gptmodel')
model_size = os.environ['MODEL_SIZE']            
model_device = "cuda" if os.environ['DEVICE'] == "cuda" else "cpu"
model_compute_type = "float16" if os.environ['DEVICE'] == "cuda" else "int8"
if os.environ.get('DEVICE'):
    print(Fore.RED + 'DEVICE IN USE FOR Faster-Whisper=', os.environ['DEVICE'])
script_dir = os.path.dirname(os.path.abspath(__file__))
        

foldername_dir, personality_dir, keys = get_file_paths(script_dir, 
                                                        foldername, 
                                                        personality)

_kokoro = kokoro.Kokoro(personality = personality_dir, 
                            keys = keys, 
                            save_folderpath = foldername_dir,
                            gptmodel = gptmodel,
                            voice_name = voicename,
                            tts = tts,
                            model_size = model_size,
                            model_device = model_device,
                            model_compute_type = model_compute_type,
                            speech_recog = speech_recog,
                            tortoise_autoplay=False,
                            rvc_model_path=rvc_model_path
                            )

assistant = assistant_p.AssistantP(_kokoro)
assistant.run()
