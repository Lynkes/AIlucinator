from modules.llm.llm_base import LLMBase
from dotenv import load_dotenv
import openai
import os

class OpenAILLM(LLMBase):
    """
    Classe OpenAILLM que herda da LLMBase para implementar a funcionalidade de geração de respostas utilizando a API da OpenAI.

    Atributos:
        api_key (str): Chave da API da OpenAI obtida das variáveis de ambiente.
        model (str): Nome do modelo a ser utilizado.
    """
    def __init__(self):
        """
        Inicializa a classe OpenAILLM, carregando a chave da API e o modelo a ser utilizado.

        Raises:
            ValueError: Se a chave da API não for encontrada nas variáveis de ambiente.
        """
        load_dotenv()
        # Define a chave da API OpenAI a partir da variável de ambiente
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLMMODEL")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set the 'OPENAI_API_KEY' environment variable.")
        
        openai.api_key = self.api_key

    def generate(self, prompt):
        """
        Gera uma resposta do modelo LLM utilizando a API da OpenAI.

        Args:
            prompt (str): O prompt para o modelo LLM.

        Returns:
            str: Resposta gerada pelo modelo ou None em caso de erro.
        """
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