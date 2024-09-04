class LLMBase:

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

    def generate_response(self, prompt, model):
        return self.provider.generate_response(prompt, model)
