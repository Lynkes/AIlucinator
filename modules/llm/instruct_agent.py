import asyncio
import json
import os
import requests
import threading
import time
from ollama import AsyncClient, Client
import colorama
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import sqlite3
import subprocess
import tkinter as tk
from tkinter import filedialog
from modules.utils.conversation_utils import process_line, clean_raw_bytes, process_sentence
import globals

from modules.llm.llm_base import LLMBase

from langchain.prompts import ChatPromptTemplate

# Definição dos prompts iniciais para cada agente
CHAT_AGENT_PROMPT = """You are Ryan, a highly intelligent AI assistant with a touch of subtle humor. 
Your responses are always precise and efficient, but you enjoy light-hearted interactions, 
keeping the conversation friendly and approachable.

Your expansive memory allows you to recall all previous interactions, 
files, and relevant details from the current session, ensuring your responses are contextually informed and intelligent.
you also have some tools at your disposal like:
{
'set_volume',          
'get_folder_structure',
'get_weather_forecast',
'currency_converter',  
'increase_volume',     
'decrease_volume',     
'open_folder',         
'open_program',        
'google_search',       
'get_joke'
}          
"""

# Funções para carregar e salvar o histórico de mensagens
def load_messages_from_json(save_folderpath:str):
    """
    Carrega as mensagens de um arquivo JSON para inicializar a lista de mensagens.

    Args:
        filepath (str): Caminho para o arquivo JSON de histórico de mensagens.

    Returns:
        list: Lista de mensagens carregadas.
    """
    filepath= save_folderpath + "\\messages_history.json"
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                messages = json.load(file)
            print("Messages loaded from", filepath)
        except Exception as e:
            print(f"Error loading messages: {e}")
            messages = []
    else:
        try:
            with open(f"{save_folderpath}.txt", "r", encoding="utf-8") as file:
                prompt = file.read()
                print("Personality template loaded.")
        except Exception as e:
            print(f"Error loading personality prompt: {e}")
            prompt = CHAT_AGENT_PROMPT
        # Se o arquivo não existir, cria um novo com a mensagem de sistema padrão
        messages = [{'role': 'system', 'content': prompt}]
        save_messages_to_json(messages, save_folderpath)
        print("No previous message history found. Created a new file.")
    return messages

def save_messages_to_json(messages, save_folderpath:str):
    """
    Sobrescreve o arquivo JSON com a lista atual de mensagens.

    Args:
        messages (list): Lista de mensagens a serem salvas.
        filepath (str): Caminho para o arquivo JSON de histórico de mensagens.
    """
    filepath = save_folderpath + "/messages_history.json"
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(messages, file, indent=2, ensure_ascii=False)
        print(f"Messages saved to {filepath}")
    except Exception as e:
        print(f"Error saving messages: {e}")

# Classe LLMTOOLS para uso das ferramentas
class LLMTOOLS:
    """
    Classe que define as ferramentas que o agente pode utilizar para executar ações específicas.
    """
    def __init__(self):
        """
        Inicializa o mapeamento de ferramentas e carrega as instruções das ferramentas.
        """
        self.tools_mapping = {
            'set_volume'            : self.set_volume,
            'get_folder_structure'  : self.get_folder_structure,
            'get_weather_forecast'  : self.get_weather_forecast,
            'currency_converter'    : self.currency_converter,
            'increase_volume'       : self.increase_volume,
            'decrease_volume'       : self.decrease_volume,
            'open_folder'           : self.open_folder,
            'open_program'          : self.open_program,
            'google_search'         : self.google_search,
            'get_joke'              : self.get_joke,
        }
        with open('modules/tools/tools.json', 'r') as f:
            self.instruct_tools = json.load(f)
            print("Loaded tools instructions:\n", self.instruct_tools, "\n")
            print("Loaded tools mapping:\n", self.tools_mapping, "\n")

    def set_volume(self, level: int):
        """
        Define o volume do sistema para um nível específico.

        Args:
            level (int): Nível de volume desejado (0 a 100).

        Returns:
            str: Confirmação da ação realizada.
        """
        level = int(level)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%"

    def increase_volume(self, amount: int):
        """
        Aumenta o volume do sistema em uma certa porcentagem.

        Args:
            amount (int): Quantidade a aumentar (0 a 100).

        Returns:
            str: Confirmação da ação realizada.
        """
        amount = int(amount)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = min(1.0, current_volume + amount / 100)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return f"Volume increased by {amount}%"

    def decrease_volume(self, amount: int):
        """
        Diminui o volume do sistema em uma certa porcentagem.

        Args:
            amount (int): Quantidade a diminuir (0 a 100).

        Returns:
            str: Confirmação da ação realizada.
        """
        amount = int(amount)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = max(0.0, current_volume - amount / 100)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return f"Volume decreased by {amount}%"

    def open_program(self, program_path: str):
        """
        Abre um programa específico usando o caminho fornecido.

        Args:
            program_path (str): Caminho para o executável do programa.

        Returns:
            str: Confirmação da ação realizada ou mensagem de erro.
        """
        try:
            subprocess.Popen([program_path])
            return f"Program {program_path} opened."
        except Exception as e:
            return f"Error opening program: {e}"

    def open_folder(self, path: str):
        """
        Abre uma pasta no Explorador de Arquivos.

        Args:
            path (str): Caminho para a pasta.

        Returns:
            str: Confirmação da ação realizada ou mensagem de erro.
        """
        try:
            subprocess.run(['explorer', path])
            return f"Folder {path} opened in Explorer."
        except Exception as e:
            return f"Error opening folder: {e}"

    def select_folder(self):
        """
        Abre uma caixa de diálogo para o usuário selecionar uma pasta.

        Returns:
            str: Caminho da pasta selecionada ou mensagem de cancelamento.
        """
        folder_path = filedialog.askdirectory(title="Select Folder")
        return folder_path if folder_path else "No folder selected."

    def get_folder_structure(self, path: str, level: int = 0) -> str:
        """
        Retorna uma representação em string da estrutura de pastas a partir de um caminho dado.

        Args:
            path (str): Caminho para a pasta.
            level (int): Nível de profundidade atual (para recuo).

        Returns:
            str: Representação da estrutura da pasta.
        """
        folder_structure = []
        indent = ' ' * 4 * level
        folder_structure.append(f'{indent}{os.path.basename(path)}/')

        try:
            entries = os.listdir(path)
        except PermissionError:
            return f'{indent}{os.path.basename(path)}/ (access denied)'

        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                folder_structure.append(f'{indent}├── {entry}/')
                folder_structure.append(self.get_folder_structure(full_path, level + 1))
            else:
                folder_structure.append(f'{indent}├── {entry}')
        return '\n'.join(folder_structure)

    def get_weather_forecast(self, city: str, api_key: str) -> str:
        """
        Obtém a previsão do tempo para uma cidade usando a API OpenWeatherMap.

        Args:
            city (str): Nome da cidade.
            api_key (str): Chave de API do OpenWeatherMap.

        Returns:
            str: Previsão do tempo ou mensagem de erro.
        """
        try:
            url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {'q': city, 'appid': api_key, 'units': 'metric'}
            response = requests.get(url, params=params)
            data = response.json()

            if "list" in data:
                forecast = data["list"][0]
                temp = forecast["main"]["temp"]
                weather_desc = forecast["weather"][0]["description"]
                return f"The weather in {city} will be {weather_desc} with a temperature of {temp}°C."
            return "Weather data not available."
        except Exception as e:
            return f"Error fetching weather data: {e}"

    def google_search(self, query: str, api_key: str, search_engine_id: str) -> str:
        """
        Realiza uma pesquisa no Google usando a API Custom Search.

        Args:
            query (str): Termo de pesquisa.
            api_key (str): Chave de API do Google.
            search_engine_id (str): ID do mecanismo de pesquisa personalizado.

        Returns:
            str: Resultados formatados ou mensagem de erro.
        """
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {'key': api_key, 'cx': search_engine_id, 'q': query}
            response = requests.get(url, params=params)
            results = response.json()

            if 'items' in results:
                formatted_results = [
                    f"Title: {item['title']}\nLink: {item['link']}\n" for item in results['items']
                ]
                return "\n".join(formatted_results)
            return "No results found."
        except Exception as e:
            return f"Error performing Google search: {e}"

    def currency_converter(self, amount: float, from_currency: str, to_currency: str) -> str:
        """
        Converte um valor entre duas moedas (usa uma taxa fixa de exemplo).

        Args:
            amount (float): Quantidade a ser convertida.
            from_currency (str): Moeda de origem.
            to_currency (str): Moeda de destino.

        Returns:
            str: Resultado da conversão em formato JSON.
        """
        conversion_rate = 1.2  # Exemplo de taxa de conversão
        converted_amount = amount * conversion_rate
        conversion = {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount,
            'converted_amount': converted_amount
        }
        return json.dumps(conversion)

    def set_reminder(self, message: str, duration_seconds: int):
        """
        Define um lembrete que será mostrado após um certo tempo.

        Args:
            message (str): Mensagem do lembrete.
            duration_seconds (int): Duração em segundos até o lembrete ser exibido.
        """
        def reminder():
            time.sleep(duration_seconds)
            print(f"Reminder: {message}")
        threading.Thread(target=reminder).start()

    def get_joke(self) -> str:
        """
        Obtém uma piada usando a API JokeAPI.

        Returns:
            str: Piada obtida ou mensagem de erro.
        """
        try:
            url = "https://v2.jokeapi.dev/joke/Any"
            response = requests.get(url)
            data = response.json()

            if data["type"] == "single":
                return data["joke"]
            return f"{data['setup']} - {data['delivery']}"
        except Exception as e:
            return f"Error fetching joke: {e}"

# Classe para o agente de chat
class ChatAgent:
    """
    Classe que interage com o LLM para gerar respostas baseadas nas mensagens do usuário.
    """
    def __init__(self, host, tools, save_folderpath, GOOGLE_API_KEY, YOUR_SEARCH_ENGINE_ID, OPENWEATHERMAP_API_KEY):
        """
        Inicializa o agente de chat com as credenciais e instâncias necessárias.

        Args:
            host (str): Endereço do host do LLM.
            tools (LLMTOOLS): Instância das ferramentas disponíveis.
            GOOGLE_API_KEY (str): Chave de API do Google.
            YOUR_SEARCH_ENGINE_ID (str): ID do mecanismo de pesquisa personalizado.
            OPENWEATHERMAP_API_KEY (str): Chave de API do OpenWeatherMap.
        """
        self.save_folderpath=save_folderpath
        self.GOOGLE_API_KEY = GOOGLE_API_KEY
        self.YOUR_SEARCH_ENGINE_ID = YOUR_SEARCH_ENGINE_ID
        self.OPENWEATHERMAP_API_KEY = OPENWEATHERMAP_API_KEY
        self.client = AsyncClient(host=host)
        self.clientsync = Client(host=host)
        self.tools = tools
        self.messages = load_messages_from_json(self.save_folderpath)

    async def get_response(self, prompt, model):
        """
        Envia uma mensagem ao LLM e obtém a resposta.

        Args:
            prompt (str): Mensagem do usuário.
            model (str): Modelo do LLM a ser utilizado.

        Returns:
            dict: Resposta do LLM.
        """
        self.messages.append({'role': 'user', 'content': prompt})
        response = await self.client.chat(model=model, messages=self.messages)
        self.messages.append(response['message'])
        save_messages_to_json(self.messages, self.save_folderpath)  # Salva o histórico atualizado
        return response['message']['content']

    async def run_tools(self, prompt, model):
        """
        Envia um prompt ao LLM indicando que ferramentas podem ser necessárias.

        Args:
            prompt (str): Prompt modificado indicando necessidade de ferramentas.
            model (str): Modelo do LLM a ser utilizado.

        Returns:
            str: Resposta final após executar as ferramentas.
        """
        toolsmessages = [{'role': 'user', 'content': prompt}]

        response = await self.client.chat(model=model, messages=toolsmessages, tools=self.tools.instruct_tools)
        self.messages.append(response['message'])

        if response['message'].get('tool_calls'):
            for tool in response['message']['tool_calls']:
                tool_name = tool['function']['name']
                args = tool['function']['arguments']

                # Ajusta argumentos para ferramentas que exigem chaves de API
                if tool_name == 'google_search':
                    args['api_key'] = self.GOOGLE_API_KEY
                    args['search_engine_id'] = self.YOUR_SEARCH_ENGINE_ID
                if tool_name == 'get_weather_forecast':
                    args['api_key'] = self.OPENWEATHERMAP_API_KEY

                # Executa a ferramenta correspondente
                tool_function = self.tools.tools_mapping.get(tool_name)
                if tool_function:
                    function_response = tool_function(**args)
                    self.messages.append({'role': 'tool', 'content': function_response})

                # Obtém a resposta final do LLM
                final_response = await self.client.chat(model='llama3.2', messages=self.messages)
                self.messages.append(final_response['message'])
                save_messages_to_json(self.messages, self.save_folderpath)  # Salva o histórico atualizado
                return final_response['message']['content']
        return response['message']['content']

# Classe para o agente de planejamento
class PlannerAgent:
    """
    Classe responsável por analisar a intenção do usuário e decidir se deve chamar uma ferramenta ou outro agente.
    """
    def __init__(self, chat_agent, tools_mapping):
        """
        Inicializa o agente de planejamento com o agente de chat e o mapeamento de ferramentas.

        Args:
            chat_agent (ChatAgent): Instância do agente de chat.
            tools_mapping (dict): Mapeamento de nomes de ferramentas para funções.
        """
        self.chat_agent = chat_agent
        self.tools_mapping = tools_mapping

    async def chat(self, prompt, model):
        """
        Método para enviar uma mensagem diretamente ao LLM via ChatAgent.

        Args:
            prompt (str): Mensagem do usuário.
            model (str): Modelo do LLM a ser utilizado.

        Returns:
            str: Resposta do LLM.
        """
        return await self.chat_agent.get_response(prompt, model)

    async def plan_task(self, prompt, model):
        """
        Usa um template para criar um prompt que ajuda a decidir a ação apropriada.

        Args:
            prompt (str): Mensagem do usuário.
            model (str): Modelo do LLM a ser utilizado.

        Returns:
            str: Resposta após decidir a ação.
        """
        template_text = """Objective: Review the user's message and analyze the intention.

Interaction with another agent:
If the user's message indicates that they want to interact with another agent, respond with 'agent_call'.

Action based on tool:
If the user is requesting an action that involves using tools (such as accessing information, setting reminders, or performing calculations), respond with 'tool_call', including the necessary context to ensure the tool performs the action correctly.

No direct response:
If none of the above options are relevant, no response is necessary.

Tool Mapping:
{tools_mapping}

Message History:
{messages}

Additional Notes:

If the user's message suggests they want to try again or perform a similar task, refer to the Message History to decide whether to perform a 'tool_call', based on previous context.
User Input:
{userprompt}"""
        template = ChatPromptTemplate.from_template(template_text)
        Planer_prompt = template.format(tools_mapping=self.tools_mapping, messages=self.chat_agent.messages, userprompt=prompt)
        response = await self.chat_agent.client.generate(model=model, prompt=Planer_prompt)
        decision = response['response']
        self.chat_agent.messages.append({'role': 'plannerAgent', 'content': decision})

        # Decide a ação com base na decisão do LLM
        if "tool_call" in decision.lower():
            print("Calling tool:")
            return await self.chat_agent.run_tools(decision, model)

        elif "agent_call" in decision.lower():
            print("Calling Agent:")
            return await self.chat_agent.get_response(prompt, model)
        else:
            print("Calling Agent:")
            return await self.chat_agent.get_response(prompt, model)

class AgentINSTRUCT(LLMBase):
    """
    Classe que coordena os agentes e integra as funcionalidades.
    """
    def __init__(self, host, save_folderpath:str, GOOGLE_API_KEY, YOUR_SEARCH_ENGINE_ID, OPENWEATHERMAP_API_KEY):
        """
        Inicializa os agentes e pré-carrega o LLM.

        Args:
            host (str): Endereço do host do LLM.
            GOOGLE_API_KEY (str): Chave de API do Google.
            YOUR_SEARCH_ENGINE_ID (str): ID do mecanismo de pesquisa personalizado.
            OPENWEATHERMAP_API_KEY (str): Chave de API do OpenWeatherMap.
        """
        self.tools = LLMTOOLS()
        self.chat_agent = ChatAgent(host, self.tools, save_folderpath, GOOGLE_API_KEY, YOUR_SEARCH_ENGINE_ID, OPENWEATHERMAP_API_KEY)
        self.planner_agent = PlannerAgent(self.chat_agent, self.tools)
        # Pré-carrega o LLM
        stream = self.chat_agent.clientsync.generate(prompt="Start", model="llama3.2", keep_alive=0)
        message = stream['response']
        print("Pre-LOADED Ollama", message)

    async def generate(self, prompt, model):
        """
        Gera uma resposta ao prompt fornecido usando o planner_agent.

        Args:
            prompt (str): Mensagem do usuário.
            model (str): Modelo do LLM a ser utilizado.

        Returns:
            str: Resposta gerada.
        """
        messages = [
            {
                "role": "system",
                "content": prompt
            },
        ]
        message = ''
        stream = await self.planner_agent.plan_task(prompt, model)

        # Processa o stream de resposta do LLM
        for chunk in stream:
            if globals.processing is False:
                print("Break globals.processing is False")
                break  # Se o sinal de parada for definido, interrompe o processamento

            message += chunk['response']  # Adiciona o chunk de resposta gerado
            next_token = chunk['response']

            if next_token:
                # Se houver um token de pausa, processa a sentença
                if next_token in [".", "!", "?", ":", ";", "?!", "\n", "\n\n"]:
                    process_sentence([next_token])

        # Verifica se o processamento ainda está habilitado e processa qualquer sentença restante
        if globals.processing and message:
            process_sentence([message])

        return message if message else "<EOS>"
    
    async def chat_rag(self, prompt, model):
        """
        Envia uma mensagem diretamente ao LLM via planner_agent.

        Args:
            prompt (str): Mensagem do usuário.
            model (str): Modelo do LLM a ser utilizado.

        Returns:
            str: Resposta do LLM.
        """
        response = await self.planner_agent.chat(prompt, model)
        return response if response else "<EOS>"

    async def chat(self, prompt, model):
        """
        Envia uma mensagem diretamente ao LLM via planner_agent.

        Args:
            prompt (str): Mensagem do usuário.
            model (str): Modelo do LLM a ser utilizado.

        Returns:
            str: Resposta do LLM.
        """
        response = await self.planner_agent.chat(prompt, model)
        return response if response else "<EOS>"

# Função principal assíncrona que coordena os agentes
async def main(model):
    """
    Função principal que inicializa os agentes e inicia o loop de interação com o usuário.

    Args:
        model (str): Modelo do LLM a ser utilizado.
    """
    host = "127.0.0.1"
    GOOGLE_API_KEY = "SUA_CHAVE_API_GOOGLE"
    YOUR_SEARCH_ENGINE_ID = "SEU_ID_DO_MECANISMO_DE_PESQUISA"
    OPENWEATHERMAP_API_KEY = "SUA_CHAVE_API_OPENWEATHERMAP"

    tools = LLMTOOLS()
    chat_agent = ChatAgent(host, tools, GOOGLE_API_KEY, YOUR_SEARCH_ENGINE_ID, OPENWEATHERMAP_API_KEY)
    planner_agent = PlannerAgent(chat_agent, tools.tools_mapping)

    while True:
        prompt = input("Enter your question or command: ")
        response = await planner_agent.plan_task(prompt, model=model)
        print("Response:", response)

if __name__ == '__main__':
    asyncio.run(main(model="llama3.2"))
