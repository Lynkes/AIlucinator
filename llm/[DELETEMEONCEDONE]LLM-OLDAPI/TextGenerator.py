import json
import requests

# Define base URL for API endpoints
API_BASE_URL = "http://localhost:5005/v1/"

# Define default parameters for requests
DEFAULT_PARAMS = {
    "api_key": "ollama"
}

def make_request(url, payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.reason}")
        return None

# Chat Completions
def chat_completions_create(messages, model, options=None, stream=False, keep_alive="5m"):
    payload = {
        "messages": messages,
        "model": model,
        "options": options if options else DEFAULT_PARAMS,
        "stream": stream,
        "keep_alive": keep_alive
    }
    return make_request(API_BASE_URL + "chat/completions", payload)

# Embeddings
def embeddings_create(texts, model=None, stream=False):
    payload = {
        "texts": texts,
        "model": model,
        "stream": stream
    }
    return make_request(API_BASE_URL + "embeddings", payload)

# Image Generations
def image_generations_create(images, response_format="b64_json"):
    payload = {
        "images": images,
        "response_format": response_format
    }
    return make_request(API_BASE_URL + "images/generations", payload)

# Moderations
def moderations_create(texts, model=None):
    payload = {
        "texts": texts,
        "model": model
    }
    return make_request(API_BASE_URL + "moderations", payload)

# Models
def models_list():
    return make_request(API_BASE_URL + "models", payload=None)

def models_get(model_id):
    return make_request(API_BASE_URL + f"models/{model_id}", payload=None)

# Edits - Deprecated
def edits_create(prompt, model, options=None, stream=False, keep_alive="5m"):
    payload = {
        "prompt": prompt,
        "model": model,
        "options": options if options else DEFAULT_PARAMS,
        "stream": stream,
        "keep_alive": keep_alive
    }
    return make_request(API_BASE_URL + "edits", payload)

# Text Completion - Deprecated
def text_completion_create(prompt, model, options=None, stream=False, keep_alive="5m"):
    payload = {
        "prompt": prompt,
        "model": model,
        "options": options if options else DEFAULT_PARAMS,
        "stream": stream,
        "keep_alive": keep_alive
    }
    return make_request(API_BASE_URL + "text_completion", payload)

# Completions - Deprecated
def completions_create(prompt, model, options=None, stream=False, keep_alive="5m"):
    payload = {
        "prompt": prompt,
        "model": model,
        "options": options if options else DEFAULT_PARAMS,
        "stream": stream,
        "keep_alive": keep_alive
    }
    return make_request(API_BASE_URL + "completions", payload)

# Engines - Deprecated
def engines_list():
    return make_request(API_BASE_URL + "engines", payload=None)

def engines_get(model_name):
    return make_request(API_BASE_URL + f"engines/{model_name}", payload=None)

# Images Edits - Not Yet Supported
def images_edits_create():
    return "This endpoint is not yet supported"

# Images Variations - Not Yet Supported
def images_variations_create():
    return "This endpoint is not yet supported"

# Audio - Supported
def audio_transcribe(data, model=None):
    payload = {
        "data": data,
        "model": model
    }
    return make_request(API_BASE_URL + "audio/transcribe", payload)

# Files - Not Yet Supported
def files_create():
    return "This endpoint is not yet supported"

# Fine-tunes - Not Yet Supported
def fine_tunes_create():
    return "This endpoint is not yet supported"

# Search - Not Yet Supported
def search_query():
    return "This endpoint is not yet supported"
