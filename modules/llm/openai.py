from modules.llm.llm_base import LLMBase
import openai
import os

class OpenAILLM(LLMBase):
    def __init__(self, model="gpt-4"):
        # Set your OpenAI API key from the environment variable or directly
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set the 'OPENAI_API_KEY' environment variable.")
        
        openai.api_key = self.api_key
        self.model = model

    def generate(self, prompt):
        # Generate a response from the OpenAI API
        try:
            response = openai.Completion.create(
                model=self.model,
                prompt=prompt,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
                stream=True
            )
            message = ''
            for chunk in response:
                if 'choices' in chunk and chunk['choices']:
                    message += chunk['choices'][0]['text']
                    print(chunk['choices'][0]['text'], end='', flush=True)
            print("\n")
            return message
        except openai.error.OpenAIError as e:
            print(f"An error occurred: {e}")
            return None
