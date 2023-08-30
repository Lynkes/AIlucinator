import os
import sys
import subprocess
import asyncio
import sys
import speech_recognition as sr
import pyttsx3
import subprocess
import threading
from resources import connect
from resources import livechat
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


script_path = os.path.dirname(__file__)
index_url = os.environ.get('INDEX_URL', "")
python = sys.executable
skip_install = False

def run(command, desc=None, errdesc=None, custom_env=None, live=False):
    if desc is not None:
        print(desc)

    if live:
        result = subprocess.run(command, shell=True, env=os.environ if custom_env is None else custom_env)
        if result.returncode != 0:
            raise RuntimeError(f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}""")

        return ""

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=os.environ if custom_env is None else custom_env)

    if result.returncode != 0:

        message = f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}
stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout)>0 else '<empty>'}
stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr)>0 else '<empty>'}
"""
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")


def run_pip(args, desc=None):
    if skip_install:
        return

    index_url_line = f' --index-url {index_url}' if index_url != '' else ''
    return run(f'"{python}" -m pip {args} --prefer-binary{index_url_line}', desc=f"Installing {desc}", errdesc=f"Couldn't install {desc}")


def prepare_environment():
    global skip_install
    requirements_file = os.environ.get('REQS_FILE', "requirements.txt")
    print(f"Python {sys.version}")
    
    if not os.path.isfile(requirements_file):
        requirements_file = os.path.join(script_path, requirements_file)
    run_pip(f"install -r \"{requirements_file}\"", "requirements for Python-APP Virtual environment")
#######################################################################################################################################################################################

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
    #SEND OUTPUT TO TTS
    return generate_voice(final_message)


def generate_voice(response):
            engine.say(f"{response}")
            engine.runAndWait()


def chat(updatein='', useEL=False, usewhisper=False):
    history = {'internal': [], 'visible': []}
    try:
       # You can change the mode to 1 if you want to record audio from your microphone
       # or change the mode to 2 if you want to capture livechat from youtube
       mode = input("Mode (1-Mic, 2-Youtube Live, 3-Twitch Live, 4-TEST): ")
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
             user_input="me fale as coisas que voce mais gosta."
             asyncio.run(print_response_stream(user_input, history))
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
    #completion = openai.Audio.transcribe(model=model_id, file=speech)
    #response = completion['text']
    #return response


# Takes user voice input from microphone and returns the audio.
# If there's no audio, it will return an empty array
def listen_for_voice(timeout:int|None):
    with mic as source:
            print("\n Listening...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = r.listen(source, timeout)
            except:
                return []
    return audio



###TEST###
################################################################################
def listen_for_voice_NEW(timeout: int = None):

    def audio_listener():
        with mic as source:
            print("\n>Listening...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = r.listen(source, timeout=timeout)
            except sr.WaitTimeoutError:
                print(">Timeout reached. Stopping listening.")
                audio = None
    audio = None
    audio_thread = threading.Thread(target=audio_listener)
    try:
        audio_thread.start()
        audio_thread.join(timeout)  # Wait for the thread to finish or timeout
    except KeyboardInterrupt:
        pass  # Handle user interruption if needed
    return audio
#################################################################################

if __name__ == "__main__":
    prepare_environment()
    print("***AI Starting***")
    chat()