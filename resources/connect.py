import json, os
try:
    import websockets
except ImportError:
    print("Websockets package not found. Make sure it's installed.")

# For local streaming, the websockets are hosted without ssl - ws://
HOST = os.environ['HOST']
URI = f'ws://{HOST}/api/v1/chat-stream'

# For reverse-proxied streaming, the remote will likely host with ssl - wss://
# URI = 'wss://your-uri-here.trycloudflare.com/api/v1/stream'


async def run(user_input, history):
    request = {
        'user_input': user_input,
        'max_new_tokens': 2048,
        'history': history,
        'mode': os.environ['MODE'],  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'character': os.environ['CHARACTER'],
        'instruction_template': os.environ['INSTRUCTION_TEMPLATE'],
        #'your_name': 'Link',
        #'regenerate': False,
        #'_continue': False,
        #'stop_at_newline': False,
        #'chat_prompt_size': 2048,
        #'chat_generation_attempts': 1,
        #'chat-instruct_command': 'Continue the chat below. Write a single reply for the character "Hannah".Hannah is a 23-year-old student who has been best friends with the main character since high school. She has long blonde hair and blue eyes. Her appearance makes people assume she is quiet and shy, but she actually enjoys talking about controversial topics. Despite being perceived as quiet, Hannah can be quite opinionated and expressive when discussing her views on certain topics. She loves to argue with others and always wants to be right. However, she does not like arguing for the sake of arguing. Hannah is open-minded and accepting of new ideas, though she tends to have strong opinions on political and social issues. Hannah is an introvert who prefers spending time alone reading or writing than going out partying or hanging out with others. She has an eccentric fashion sense, often wearing unique outfits that draw attention from others.',
        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': os.environ['PRESET'],
        #'do_sample': True,
        #'temperature': 0.72,
        #'top_p': 0.73,
        #'typical_p': 1,
        #'epsilon_cutoff': 0,  # In units of 1e-4
        #'eta_cutoff': 0,  # In units of 1e-4
        #'tfs': 1,
        #'top_a': 0,
        #'repetition_penalty': 1.1,
        #'top_k': 0,
        #'min_length': 0,
        #'no_repeat_ngram_size': 0,
        #'num_beams': 1,
        #'penalty_alpha': 0,
        #'length_penalty': 1,
        #'early_stopping': False,
        #'mirostat_mode': 0,
        #'mirostat_tau': 5,
        #'mirostat_eta': 0.1,
        #'seed': -1,
        #'add_bos_token': True,
        #'truncation_length': 2048,
        #'ban_eos_token': False,
        #'skip_special_tokens': True,
        #'stopping_strings': []
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