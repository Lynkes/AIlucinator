from modules.llm.llm_base import LLMBase
import ollama
from colorama import *
from ollama import AsyncClient, Client

class OllamaLLM(LLMBase):
    """
    Classe OllamaLLM que herda da LLMBase para implementar a funcionalidade de geração de respostas utilizando o cliente Ollama.

    Atributos:
        client (Client): Cliente para comunicação síncrona com o servidor LLM.
        asyncclient (AsyncClient): Cliente para comunicação assíncrona com o servidor LLM.
    """
    def __init__(self, host):
        """
        Inicializa a classe OllamaLLM.

        Args:
            host (str): Host do servidor LLM.
        """
        self.client = Client(host=host)
        self.asyncclient = AsyncClient(host=host)

    def generate(self, prompt, model):
        """
        Gera uma resposta do modelo LLM de forma síncrona.

        Args:
            prompt (str): O prompt para o modelo LLM.
            model (str): O nome do modelo a ser usado.

        Returns:
            str: Resposta do modelo.
        """
        message = ''
        stream = self.client.generate(model=model, prompt=prompt, stream=True, keep_alive=600)
        for chunk in stream:
            message += chunk['response']
        return message
    
    async def asyncgenerate(self, prompt, model):
        """
        Gera uma resposta do modelo LLM usando AsyncClient de forma assíncrona.

        Args:
            prompt (str): O prompt para o modelo LLM.
            model (str): O nome do modelo a ser usado.

        Returns:
            str: Resposta do modelo.
        """
        message = ''
        try:
            # Gera uma solicitação assíncrona para o modelo
            stream = await self.asyncclient.generate(model=model, prompt=prompt, stream=True)
            async for chunk in stream:
                message += chunk['response']
        except Exception as e:
            print(f"Erro durante a geração da resposta: {e}")
            return None
        return message
