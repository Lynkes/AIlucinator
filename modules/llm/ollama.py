from modules.llm.llm_base import LLMBase
import ollama
from colorama import *

class OllamaLLM(LLMBase):

    def generate(self, prompt, model):
        message = ''
        stream = ollama.generate(model=model, prompt=prompt, stream=True,keep_alive=600,)
        for chunk in stream:
            message += chunk['response']
            #print(chunk['response'], end='', flush=True)
        #print("\n")
        return message
