import asyncio
import json
import sys
import speech_recognition as sr
import pyttsx3
import keyboard
import pytchat
import time
import re
import subprocess
import threading
import socket
from emoji import demojize
from utils.translate import *
from utils.subtitle import *
from utils.promptMaker import *
from utils.twitch_config import *

usewhisper = 'true'
ia_name='hey'
mode = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Ardha"
blacklist = ["Nightbot", "streamelements"]
r = sr.Recognizer()
r.dynamic_energy_threshold = False
r.energy_threshold=300
mic = sr.Microphone(device_index=0)
# pyttsx3 Set-up
engine = pyttsx3.init()
# engine.setProperty('rate', 180) #200 is the default speed, this makes it slower
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id) # 0 for male, 1 for female

try:
    import websockets
except ImportError:
    print("Websockets package not found. Make sure it's installed.")

# For local streaming, the websockets are hosted without ssl - ws://
HOST = '172.28.246.131:5005'
URI = f'ws://{HOST}/api/v1/chat-stream'

# For reverse-proxied streaming, the remote will likely host with ssl - wss://
# URI = 'wss://your-uri-here.trycloudflare.com/api/v1/stream'

async def run(user_input, history):
    # Note: the selected defaults change from time to time.
    request = {
        'user_input': user_input,
        'max_new_tokens': 1000,
        'history': history,
        'mode': 'chat',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'character': 'Example',
        'instruction_template': 'None',
        'your_name': 'You',

        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_prompt_size': 2048,
        'chat_generation_attempts': 1,
        'chat-instruct_command': 'Continue the chat dialogue below. Write a single reply for the character "<|character|>".\n\n<|prompt|>',

        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',  
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': []
    }
    async with websockets.connect(URI, ping_interval=None) as websocket:
        await websocket.send(json.dumps(request))

        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)

            match incoming_data['event']:
                case 'text_stream':
                    yield incoming_data['history']
                case 'stream_end':
                    return


async def print_response_stream(user_input, history):
    cur_len = 0
    async for new_history in run(user_input, history):
        cur_message = new_history['visible'][-1][1][cur_len:]
        cur_len += len(cur_message)
        final_message = final_message + cur_message
        print(cur_message, end='')
        sys.stdout.flush()  # If we don't flush, we won't see tokens in realtime.
    generate_voice(final_message)
        

# Takes user voice input from microphone and returns the audio.
# If there's no audio, it will return an empty array


def listen_for_voice(timeout:int|None=5):
    with mic as source:
            print("\n Listening...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = r.listen(source, timeout)
            except:
                return []
    print("no longer listening")
    return audio


def generate_voice(response):
            engine.say(f"{response}")
            engine.runAndWait()


# function to capture livechat from youtube
def yt_livechat(video_id):
        global chat

        live = pytchat.create(video_id=video_id)
        while live.is_alive():
        # while True:
            try:
                for c in live.get().sync_items():
                    # Ignore chat from the streamer and Nightbot, change this if you want to include the streamer's chat
                    if c.author.name in blacklist:
                        continue
                    # if not c.message.startswith("!") and c.message.startswith('#'):
                    if not c.message.startswith("!"):
                        # Remove emojis from the chat
                        chat_raw = re.sub(r':[^\s]+:', '', c.message)
                        chat_raw = chat_raw.replace('#', '')
                        # chat_author makes the chat look like this: "Nightbot: Hello". So the assistant can respond to the user's name
                        chat = c.author.name + ' berkata ' + chat_raw
                        print(chat)
                        
                    time.sleep(1)
            except Exception as e:
                print("Error receiving chat: {0}".format(e))


def twitch_livechat():
    global chat
    sock = socket.socket()
    sock.connect((server, port))
    sock.send(f"PASS {token}\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\n".encode('utf-8'))
    regex = r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)"

    while True:
        try:
            resp = sock.recv(2048).decode('utf-8')

            if resp.startswith('PING'):
                    sock.send("PONG\n".encode('utf-8'))

            elif not user in resp:
                resp = demojize(resp)
                match = re.match(regex, resp)

                username = match.group(1)
                message = match.group(2)

                if username in blacklist:
                    continue
                
                chat = username + ' said ' + message
                print(chat)

        except Exception as e:
            print("Error receiving chat: {0}".format(e))


def preparation():
    global conversation, chat_now, chat, chat_prev
    while True:
        # If the assistant is not speaking, and the chat is not empty, and the chat is not the same as the previous chat
        # then the assistant will answer the chat
        chat_now = chat
        if is_Speaking == False and chat_now != chat_prev:
            # Saving chat history
            conversation.append({'role': 'user', 'content': chat_now})
            chat_prev = chat_now
            #ARUMAR RESPOSTA DE CHAT YT, TWICH #openai_answer() 
        time.sleep(1)

def chat(updatein='', useEL=False, usewhisper=False):
    history = {'internal': [], 'visible': []}
    try:
       # You can change the mode to 1 if you want to record audio from your microphone
       # or change the mode to 2 if you want to capture livechat from youtube
       mode = input("Mode (1-Mic, 2-Youtube Live, 3-Twitch Live): ")
       if mode == "1":
           while True:
            audio = listen_for_voice(timeout=None)
            try:
                if usewhisper:
                    if audio:
                        user_input = whisper(audio)
                        print("You said: ", user_input) # Checking
                    else:
                        raise ValueError("Empty audio input")
                else:    
                    user_input = r.recognize_google(audio)
                
            except Exception as e:
                print(e)
                continue
            if "open chrome" in user_input.lower() or "open chrome." in user_input.lower():
                subprocess.Popen('C:\Program Files\Google\Chrome\Application\chrome.exe')
            if "open notepad" in user_input.lower() or "open notepad." in user_input.lower():
                subprocess.Popen('notepad.exe')
            if "quit" in user_input.lower() or "quit." in user_input.lower():
                raise SystemExit
            
            # This merely appends the list of dictionaries, it doesn't overwrite the existing
            # entries.  It should change the behavior of chatGPT though based on the text file.
            if updatein != '':
                if "update chat" in user_input.lower():
                        update = updatein
                        with open (update, "r") as file:
                            update = file.read()
            try:
                asyncio.run(print_response_stream(user_input, history))
                
            except:
                print("Token limit exceeded, clearing messsages list and restarting")

       elif mode == "2":
        live_id = input("Livestream ID: ")
        # Threading is used to capture livechat and answer the chat at the same time
        t = threading.Thread(target=preparation)
        t.start()
        yt_livechat(live_id)
       elif mode == "3":
        # Threading is used to capture livechat and answer the chat at the same time
           print("To use this mode, make sure to change utils/twitch_config.py to your own config")
           t = threading.Thread(target=preparation)
           t.start()
           twitch_livechat()
    except KeyboardInterrupt:
        t.join()
        print("Stopped")


def whisper(self, audio):
    '''
    Uses the Whisper API to generate audio for the response text. 
    Args:
        audio (AudioData) : AudioData instance used in Speech Recognition, needs to be written to a
                            file before uploading to openAI.
    Returns:
        response (str): text transcription of what Whisper deciphered
    '''
    r.recognize_google(audio) # raise exception for bad/silent audio
    with open('speech.wav','wb') as f:
        f.write(audio.get_wav_data())
    speech = open('speech.wav', 'rb')
    model_id = "whisper-1"
    completion = openai.Audio.transcribe(model=model_id, file=speech)
    response = completion['text']
    return response


if __name__ == '__main__':
    chat()