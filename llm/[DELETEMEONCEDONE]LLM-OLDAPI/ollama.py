import json
import requests

#API endpoints
OLLAMA_API ="http://localhost:11434/api/"
#base_url='http://localhost:11434/v1/',
#api_key='ollama',
'''
OPEN AI COMPATIBLE
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1/',

    # required but ignored
    api_key='ollama',
)
'''

# Define default values for API parameters
DEFAULT_COMPLETION_OPTIONS = {
    "num_keep": 5,
    "seed": 42,
    "num_predict": 100,
    "top_k": 20,
    "top_p": 0.9,
    "tfs_z": 0.5,
    "typical_p": 0.7,
    "repeat_last_n": 33,
    "temperature": 0.8,
    "repeat_penalty": 1.2,
    "presence_penalty": 1.5,
    "frequency_penalty": 1.0,
    "mirostat": 1,
    "mirostat_tau": 0.8,
    "mirostat_eta": 0.6,
    "penalize_newline": True,
    "stop": ["\n", "user:"],
    "numa": False,
    "num_ctx": 1024,
    "num_batch": 2,
    "num_gpu": 1,
    "main_gpu": 0,
    "low_vram": False,
    "f16_kv": True,
    "vocab_only": False,
    "use_mmap": True,
    "use_mlock": False,
    "num_thread": 8
}

def make_request(url, payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.reason}")
        return None

def generate_completion(model, prompt, images=None, format="json", options=None, system=None, template=None, context=None, stream=False, raw=False, keep_alive="5m"):
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images,
        "format": format,
        "options": options if options is not None else DEFAULT_COMPLETION_OPTIONS,
        "system": system,
        "template": template,
        "context": context,
        "stream": stream if format == "json" else "True",
        "raw": raw,
        "keep_alive": keep_alive
    }
    return make_request(OLLAMA_API + "generate", payload)

def generate_chat_completion(model, messages, format="json", options=None, stream=False, keep_alive="5m"):
    payload = {
        "model": model,
        "messages": messages,
        "format": format,
        "options": options if options is not None else DEFAULT_COMPLETION_OPTIONS,
        "stream": stream if format == "json" else "True",
        "keep_alive": keep_alive
    }
    return make_request(OLLAMA_API + "chat", payload)

def create_model(name, modelfile=None, stream=False, path=None):
    payload = {
        "name": name,
        "modelfile": modelfile,
        "path": path
    }
    return make_request(OLLAMA_API + "create", payload)

def get_available_models():
    return make_request(OLLAMA_API + "models", payload=None)

def list_local_models():
    return make_request(OLLAMA_API + "tags", payload=None)

# Example usage
if __name__ == "__main__":
    available_models = get_available_models()
    print("Available Models:", available_models)

    local_models = list_local_models()
    print("Local Models:", local_models)

    completion_options = {
        "num_keep": 10,
        "top_k": 30,
        "top_p": 0.8
    }

    completion_response = generate_completion(
        model="llama3",
        prompt="Why is the sky blue?",
        options=completion_options
    )
    print("Completion Response:", completion_response)

    # Example usage for other functions...
