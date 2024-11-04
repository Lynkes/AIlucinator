from modules.llm.llm_base import LLMBase
from colorama import *
import requests
from modules.utils.conversation_utils import process_line, clean_raw_bytes, process_sentence
from jinja2 import Template
import globals
from modules.llm.llm_base import LLMBase
import ollama
from colorama import *
from ollama import AsyncClient, Client
LLAMA3_TEMPLATE = "{% set loop_messages = messages %}{% for message in loop_messages %}{% set content = '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'+ message['content'] | trim + '<|eot_id|>' %}{% if loop.index0 == 0 %}{% set content = bos_token + content %}{% endif %}{{ content }}{% endfor %}{% if add_generation_prompt %}{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}{% endif %}"
OPENAI_API_KEY= ""

class INSTRUCT(LLMBase):
    def __init__(self, host):
        self.client=Client(host=host)
        self.template = Template(LLAMA3_TEMPLATE)

    def generate(self, prompt, model):
        self.messages = [
        {
            "role": "system",
            "content": prompt
        },
    ]
        prompt = self.template.render(
            messages=self.messages,
            bos_token="<|begin_of_text|>",
            add_generation_prompt=True,
        )
        
        # Use self.client.generate instead of requests.post for streaming,  options={"num_predict": 200}
        message = ''
        stream = self.client.generate(model=model, prompt=prompt, stream=True, keep_alive=1600)
        for chunk in stream:
            if globals.processing is False:
                print("Break globals.processing is False")
                break  # If the stop flag is set, halt processing

            #message += clean_raw_bytes(line=chunk['response'])  # Append the generated response chunk
            message += chunk['response'] # Append the generated response chunk
            next_token = chunk['response']

            if next_token:
                # If there's a pause token, process the sentence
                if next_token in [".", "!", "?", ":", ";", "?!", "\n", "\n\n"]:
                    process_sentence([next_token])

        # Check if processing is still enabled and process any remaining sentence
        if globals.processing and message:
            process_sentence([message])
            
        return message if message else "<EOS>"  # Return message or <EOS> token if nothing was generated
