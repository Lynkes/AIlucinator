from modules.llm.llm_base import LLMBase
import ollama
from colorama import *
from ollama import AsyncClient, Client
        
class OllamaLLM(LLMBase):
    def __init__(self, host):
        self.client=Client(host=host)
        self.asyncclient=AsyncClient(host=host)

    def generate(self, prompt, model):
        message = ''
        stream = self.client.generate(model=model, prompt=prompt, stream=True,keep_alive=600,)
        for chunk in stream:
            message += chunk['response']
            #print(chunk['response'], end='', flush=True)
        #print("\n")
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
