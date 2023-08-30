import asyncio
import json
import sys
import speech_recognition as sr
import pyttsx3

r = sr.Recognizer()
r.dynamic_energy_threshold = False
r.energy_threshold=1000
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
    final_message = ''
    async for new_history in run(user_input, history):
        cur_message = new_history['visible'][-1][1][cur_len:]
        cur_len += len(cur_message)
        final_message = final_message + cur_message
        print(cur_message, end='')
        sys.stdout.flush()  # If we don't flush, we won't see tokens in realtime.
    return generate_voice(final_message)
    
    
    
        

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


if __name__ == '__main__':
    # Basic example
    history = {'internal': [], 'visible': []}

    # "Continue" example. Make sure to set '_continue' to True above
    # arr = [user_input, 'Surely, here is']
    # history = {'internal': [arr], 'visible': [arr]}

    while True:
        audio = listen_for_voice(timeout=None)
        try:
            user_input = r.recognize_google(audio)
        except Exception as e:
            print(e) 
            continue
        print(user_input + "\n")
        asyncio.run(print_response_stream(user_input, history))
        #generated_text = print_response_stream(user_input, history)
        #print(generated_text)
        #generate_voice(generated_text)

        





