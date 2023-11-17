import os
import sys
import subprocess
import asyncio
import sys
import speech_recognition as sr
import pyttsx3
import subprocess
import threading
import openai
from resources import connect
from resources import livechat
from colorama import *
import re
from concurrent.futures import ThreadPoolExecutor
mode = 0
r = sr.Recognizer()
r.dynamic_energy_threshold = False
r.energy_threshold=300
mic = sr.Microphone(device_index=0)
# pyttsx3 Set-up
engine = pyttsx3.init()
# engine.setProperty('rate', 180) #200 is the default speed, this makes it slower
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id) # 0 for male, 1 for female

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
    if os.environ.get('DEVICE'):
        print(Fore.RED + 'DEVICE IN USE FOR Faster-Whisper=', os.environ['DEVICE'])
        if os.environ['FASTWHISPER']:
            from faster_whisper import WhisperModel
            model_size = os.environ['MODEL_SIZE']
            model_device = "cuda" if os.environ['DEVICE'] == "cuda" else "cpu"
            model_compute_type = "float16" if os.environ['DEVICE'] == "cuda" else "int8"
            model = WhisperModel(model_size, device=model_device, compute_type=model_compute_type)
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

async def print_response_stream(user_input, history):
    cur_len = 0
    final_message = ''
    #SEND TO THE AI
    async for new_history in connect.run(user_input, history):
        cur_message = new_history['visible'][-1][1][cur_len:]
        cur_len += len(cur_message)
        final_message = final_message + cur_message
        print(cur_message, end='')
        sys.stdout.flush()  # If we don't flush, we won't see tokens in realtime.
    final_message = re.sub(r'\*.*?\*', '', final_message) # Remove Texto de acões entre(*exemplo*)
    engine.say(f"{final_message}")
    engine.runAndWait()
    #return generate_voice(final_message)

def generate_voice(response):
            engine.say(f"{response}")
            engine.runAndWait()

def chat(updatein, fastwhisper, device):
    history = {'internal': [], 'visible': []}
    try:
       mode = input("Mode ("+Fore.BLUE+"1-Mic, "+Fore.RED+"2-Youtube Live, "+Fore.MAGENTA+"3-Twitch Live, "+Fore.YELLOW+"4-Console Chat): "+Fore.WHITE+"5-Android Socket):")
       if mode == "1":
           while True:
            audio = listen_for_voice_OLD(timeout=None)
            try:
                if fastwhisper:
                    from faster_whisper import WhisperModel
                    model_size = "large-v2"
                    model_device = "cuda" if device == "cuda" else "cpu"
                    model_compute_type = "float16" if device == "cuda" else "int8"
                    model = WhisperModel(model_size, device=model_device, compute_type=model_compute_type)
                    if audio:
                        user_input, language, language_probability = fasterwhisper(audio, model,)
                        print(Style.BRIGHT + Fore.YELLOW + "You said: "+ Fore.WHITE, user_input) # Checking
                    else:
                        raise ValueError(Style.BRIGHT + Fore.RED + "Empty audio input")
                else:    
                    user_input = r.recognize_google(audio)
            except Exception as e:
                print("Exception:",e)
                continue
            if "quit" in user_input.lower():
                break
            if updatein != '':
                if "update chat" in user_input.lower():
                        update = updatein
                        with open (update, "r") as file:
                            update = file.read()
            try:
                if "en" in language or "pt" in language and language_probability >= 0.4:
                    print(Fore.WHITE)
                    asyncio.run(print_response_stream(user_input, history))
                else:
                    print(Style.BRIGHT + Fore.RED +"False input?")
            except:
                print(Style.BRIGHT + Fore.RED +"Token limit exceeded, clearing messsages list and restarting")
       elif mode == "2":
        live_id = input("Livestream ID: ")
        # Threading is used to capture livechat and answer the chat at the same time
        t = threading.Thread(target=livechat.preparation)
        t.start()
        livechat.Yt(live_id)
       elif mode == "3":
        # Threading is used to capture livechat and answer the chat at the same time
           print("To use this mode, make sure to change utils/twitch_config.py to your own config")
           t = threading.Thread(target=livechat.preparation)
           t.start()
           livechat.twitch()
       elif mode == "4":    
           with ThreadPoolExecutor(max_workers=5) as executor:
            while True:
                user_input = input("\nChat:")
                future = executor.submit(asyncio.run, print_response_stream(user_input, history))
       elif mode == "5":
           import socket    
           with ThreadPoolExecutor(max_workers=3) as executor:
            try:
                server_ip = '0.0.0.0'  # Ou o IP da sua máquina na LAN
                server_port = 9596
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind((server_ip, server_port))
                server_socket.listen(1)
                print(f"Servidor ouvindo em {server_ip}:{server_port}")
                conn, addr = server_socket.accept()
                print(f"Conexão de {addr}")
                with open('audio_received.wav', 'wb') as audio_file:
                    audio = conn.recv(1024)
                    while audio:
                        audio_file.write(audio)
                        audio = conn.recv(1024)
                conn.close()
                server_socket.close()
                if fastwhisper:
                    from faster_whisper import WhisperModel
                    model_size = "large-v2"
                    model_device = "cuda" if device == "cuda" else "cpu"
                    model_compute_type = "float16" if device == "cuda" else "int8"
                    model = WhisperModel(model_size, device=model_device, compute_type=model_compute_type)
                    if audio:
                        user_input, language, language_probability = fasterwhisper(audio, model,)
                        print(Style.BRIGHT + Fore.YELLOW + "You said: "+ Fore.WHITE, user_input) # Checking
                    else:
                        raise ValueError(Style.BRIGHT + Fore.RED + "Empty audio input")
                else:    
                    user_input = r.recognize_google(audio)
            except:
                print(Style.BRIGHT + Fore.RED +"Coonection Closed?")
    except KeyboardInterrupt:
        t.join()
        print("Stopped")
        
def fasterwhisper(audio, model):
    response = ""
    with open('speech.wav','wb') as f:
        f.write(audio.get_wav_data())
    speech = open('speech.wav', 'rb')
    segments, info= model.transcribe(speech, vad_filter=True, beam_size=5)
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    for segment in segments:
        response = response + segment.text
    return response, info.language, info.language_probability

def listen_for_voice_OLD(timeout:int|None=5):
    with mic as source:
            print(Style.BRIGHT + Fore.GREEN+"\n>Listening...")
            r.adjust_for_ambient_noise(source, duration=0.2)
            try:
                audio = r.listen(source, timeout)
            except:
                return []
    return audio

def audio_listener(timeout):
    with mic as source:
        print(Fore.CYAN + "\n>Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=timeout)
        except sr.WaitTimeoutError:
            print(">Timeout reached. Stopping listening.")
            audio = None
        return audio

if __name__ == "__main__":
    LOAD_ENV()
    Check()
    while True:
        chat(updatein='', fastwhisper=os.environ['FASTWHISPER'], device= os.environ['DEVICE'])