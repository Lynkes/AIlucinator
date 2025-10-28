import asyncio
import json
import os
import requests
from modules.llm.llm_base import LLMBase
from colorama import *
from modules.utils.conversation_utils import process_line, clean_raw_bytes, process_sentence
from jinja2 import Template
import globals

# Template de formatação similar ao LLAMA3, adaptado para o estilo instruct do KoboldCPP
KOBOLD_TEMPLATE = """{% for message in messages %}
{{ message['role'] }}: {{ message['content'] }}
{% endfor %}
assistant:"""

class KOBOLD_INSTRUCT(LLMBase):
    """
    Classe KOBOLD_INSTRUCT para comunicação direta com KoboldCPP.
    Compatível com o formato da classe INSTRUCT usada com Ollama.
    """

    def __init__(self, host: str = "http://127.0.0.1:5001"):
        """
        Inicializa a classe KOBOLD_INSTRUCT.

        Args:
            host (str): URL base do servidor KoboldCPP (ex: http://127.0.0.1:5001)
        """
        self.host = host.rstrip("/")
        self.template = Template(KOBOLD_TEMPLATE)
        self.api_url = f"{self.host}/api/v1/generate"

    def generate(self, prompt: str, model: str = None):
        """
        Gera uma resposta do modelo baseado no prompt fornecido, com suporte a streaming.

        Args:
            prompt (str): Texto de entrada do usuário.
            model (str): Nome do modelo (não usado diretamente no KoboldCPP, mas mantido por compatibilidade).

        Returns:
            str: Resposta gerada pelo modelo.
        """
        # Estrutura de mensagens para template (compatível com LLMBase)
        self.messages = [
            {"role": "user", "content": prompt},
        ]

        # Renderiza o prompt com o template
        rendered_prompt = self.template.render(messages=self.messages)

        payload = {
            "prompt": rendered_prompt,
            "temperature": 0.7,
            "max_length": 1024,
            "min_p": 0.05,
            "top_p": 0.9,
            "top_k": 60,
            "typical": 1,
            "stream": True,
        }

        message = ""
        try:
            with requests.post(self.api_url, json=payload, stream=True, timeout=120) as response:
                if response.status_code != 200:
                    print(Fore.RED + f"[KOBOLD] Erro HTTP {response.status_code}: {response.text}" + Style.RESET_ALL)
                    return "<ERROR>"

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    if globals.processing is False:
                        print("Break: globals.processing is False")
                        break

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = data.get("token", "")
                    if not token:
                        continue

                    message += token
                    process_line(token)

                    # Se o token for uma pausa natural, processa a sentença
                    if token.strip() in [".", "!", "?", ":", ";", "?!", "\n", "\n\n"]:
                        process_sentence([token])

        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"[KOBOLD] Erro de conexão: {e}" + Style.RESET_ALL)
            return "<CONNECTION_ERROR>"

        # Processa qualquer sentença restante
        if globals.processing and message:
            process_sentence([message])

        return message if message else "<EOS>"
