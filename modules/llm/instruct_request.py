import asyncio
import json
import os
import requests
from modules.llm.llm_base import LLMBase
from colorama import *
from modules.utils.conversation_utils import process_line, clean_raw_bytes, process_sentence
from jinja2 import Template
import globals
from ollama import AsyncClient, Client

LLAMA3_TEMPLATE = """{% set loop_messages = messages %}{% for message in loop_messages %}{% set content = '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'+ message['content'] | trim + '<|eot_id|>' %}{% if loop.index0 == 0 %}{% set content = bos_token + content %}{% endif %}{{ content }}{% endfor %}{% if add_generation_prompt %}{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}{% endif %}"""
OPENAI_API_KEY = ""

class INSTRUCT(LLMBase):
    """
    Classe INSTRUCT que herda da LLMBase para implementar a funcionalidade de geração de respostas utilizando um modelo LLM.

    Atributos:
        client (Client): Cliente para comunicação com o servidor LLM.
        template (Template): Template Jinja2 utilizado para formatar mensagens.
    """
    def __init__(self, host):
        """
        Inicializa a classe INSTRUCT.

        Args:
            host (str): Host do servidor LLM.
        """
        self.client = Client(host=host)
        self.template = Template(LLAMA3_TEMPLATE)

    def generate(self, prompt, model):
        """
        Gera uma resposta do modelo baseado no prompt fornecido.

        Args:
            prompt (str): Texto de entrada do usuário.
            model (str): Nome do modelo a ser utilizado.

        Returns:
            str: Resposta gerada pelo modelo.
        """
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
        
        # Use self.client.generate instead of requests.post for streaming
        message = ''
        stream = self.client.generate(model=model, prompt=prompt, stream=True, keep_alive=1600)
        for chunk in stream:
            if globals.processing is False:
                print("Break globals.processing is False")
                break  # Se a flag de parada estiver definida, interrompa o processamento

            message += chunk['response']  # Adiciona o trecho da resposta gerada
            next_token = chunk['response']

            if next_token:
                # Se houver um token de pausa, processa a sentença
                if next_token in [".", "!", "?", ":", ";", "?!", "\n", "\n\n"]:
                    process_sentence([next_token])

        # Verifica se o processamento ainda está habilitado e processa qualquer sentença restante
        if globals.processing and message:
            process_sentence([message])
            
        return message if message else "<EOS>"  # Retorna a mensagem ou o token <EOS> se nada for gerado
