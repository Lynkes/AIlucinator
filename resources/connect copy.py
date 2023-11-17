import json
try:
    import websockets
except ImportError:
    print("Websockets package not found. Make sure it's installed.")
    
HOST = '127.0.0.1:5005'
URI = f'ws://{HOST}/api/v1/chat-stream'

async def run(user_input, history, mode, character, instruction_template, your_name, instruct_command, preset):
    #history = "internal"
    # Note: the selected defaults change from time to time.
    request = {
        'user_input': user_input,
        'max_new_tokens': 2048,
        'history': history,
        'mode': mode,  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'character': character,
        'instruction_template': instruction_template,
        'your_name': your_name,
        'regenerate': False,
        '_continue': False,
        'stop_at_newline': False,
        'chat_prompt_size': 2048,
        'chat_generation_attempts': 1,
        'chat-instruct_command': instruct_command,
        'preset': preset,
        'do_sample': True,
        'temperature': 0.72,
        'top_p': 0.73,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.1,
        'top_k': 0,
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
        'ban_eos_token': True,
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