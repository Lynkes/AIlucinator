from llm.llm_base import LLMBase
import ollama

class OllamaLLM(LLMBase):
    def __init__(self, model="llama3.1"):
        self.model = model

    def generate(self, prompt):
        message = ''
        stream = ollama.generate(model=self.model, prompt=prompt, stream=True)
        for chunk in stream:
            message += chunk['response']
            print(chunk['response'], end='', flush=True)
        print("\n")
        return message
