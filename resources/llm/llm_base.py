from dotenv import load_dotenv
import os

class LLMBase:
    def __init__(self):
        load_dotenv()
        provider_name = os.getenv('LLM')
        self.provider = self.get_llm_provider(provider_name)

    @staticmethod
    def get_llm_provider(provider_name):
        if provider_name == 'openai':
            from .openai import OpenAILLM
            return OpenAILLM()
        elif provider_name == 'ollama':
            from .ollama import OllamaLLM
            return OllamaLLM()
        # Add other LLM providers as needed
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    def generate_response(self, prompt):
        return self.provider.generate_response(prompt)
