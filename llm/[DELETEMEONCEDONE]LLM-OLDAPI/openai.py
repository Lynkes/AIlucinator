import modules.LLM.openai as openai

# API endpoints
API_BASE_URL = "http://localhost:11434/v1/"

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

# Initialize OpenAI with custom base URL and dummy API key
openai.api_base = API_BASE_URL
openai.api_key = 'ollama'  # Required but ignored

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
    response = openai.Completion.create(**payload)
    return response

def generate_chat_completion(model, messages, format="json", options=None, stream=False, keep_alive="5m"):
    payload = {
        "model": model,
        "messages": messages,
        "format": format,
        "options": options if options is not None else DEFAULT_COMPLETION_OPTIONS,
        "stream": stream if format == "json" else "True",
        "keep_alive": keep_alive
    }
    response = openai.ChatCompletion.create(**payload)
    return response

def create_model(name, modelfile=None, stream=False, path=None):
    payload = {
        "name": name,
        "modelfile": modelfile,
        "path": path
    }
    response = openai.Model.create(**payload)
    return response

def get_available_models():
    response = openai.Model.list()
    return response

def list_local_models():
    response = openai.Tag.list()
    return response

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
