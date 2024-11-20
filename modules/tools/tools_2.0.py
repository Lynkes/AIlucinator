import asyncio
import json
import os
import requests
import threading
import time
from ollama import AsyncClient
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import sqlite3
import subprocess
import tkinter as tk
from tkinter import filedialog

from langchain.prompts import ChatPromptTemplate

# Defina suas chaves de API
GOOGLE_API_KEY = "AIzaSyCTor3nBYT8XOiDWP50QvO-Wg97kJMvWeE"
YOUR_SEARCH_ENGINE_ID = "55b89c7350afa4dde"
OPENWEATHERMAP_API_KEY = "30e7a1aeb70171f1714b7892b779bc67"

# Defina os prompts iniciais para cada agente
CHAT_AGENT_PROMPT = """You are Ryan, a highly intelligent AI assistant with a touch of subtle humor. 
Your responses are always precise and efficient, but you enjoy light-hearted interactions, 
keeping the conversation friendly and approachable.

Your expansive memory allows you to recall all previous interactions, 
files, and relevant details from the current session, ensuring your responses are contextually informed and intelligent.
you also have some tools at your disposal."""
TOOLS_AGENT_PROMPT = "You are an assistant with access to specific tools. Respond with 'tool_calls' if a tool is needed."
PLANNER_AGENT_PROMPT = "You are responsible for coordinating tasks and activating other agents as needed."

# Funções para carregar e salvar o histórico de mensagens
def load_messages_from_json(filepath='messages_history.json'):
    """Load messages from a JSON file to initialize the messages list."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                messages = json.load(file)
            print("Messages loaded from", filepath)
        except Exception as e:
            print(f"Error loading messages: {e}")
            messages = []
    else:
        # If the file does not exist, create it with the default system message
        messages = [{'role': 'system', 'content': CHAT_AGENT_PROMPT}]
        save_messages_to_json(messages, filepath)
        print("No previous message history found. Created a new file.")
    return messages

def save_messages_to_json(messages, filepath='messages_history.json'):
    """Overwrite the JSON file with the current messages list."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(messages, file, indent=2, ensure_ascii=False)
        print(f"Messages saved to {filepath}")
    except Exception as e:
        print(f"Error saving messages: {e}")

# Classe LLMTOOLS para uso das ferramentas
class LLMTOOLS:
    def __init__(self):
        self.tools_mapping = {
            'set_volume': self.set_volume,
            'get_folder_structure': self.get_folder_structure,
            'get_weather_forecast': self.get_weather_forecast,
            'currency_converter': self.currency_converter,
            'set_volume': self.set_volume,
            'increase_volume': self.increase_volume,
            'decrease_volume': self.decrease_volume,
            'open_folder': self.open_folder,
            'open_program': self.open_program,
            'google_search': self.google_search,
            'get_joke': self.get_joke,
        }
        with open('modules/tools/tools.json', 'r') as f:
            self.instruct_tools = json.load(f)
            print("Loaded tools:",self.instruct_tools)
        
            
    def set_volume(self, level: int):
        level = int(level)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%"

    def increase_volume(self, amount: int):
        amount = int(amount)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = min(1.0, current_volume + amount / 100)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return f"Volume increased by {amount}%"

    def decrease_volume(self, amount: int):
        amount = int(amount)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = max(0.0, current_volume - amount / 100)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return f"Volume decreased by {amount}%"

    def open_program(self, program_path: str):
        try:
            subprocess.Popen([program_path])
            return f"Program {program_path} opened."
        except Exception as e:
            return f"Error opening program: {e}"

    def open_folder(self, path: str):
        try:
            subprocess.run(['explorer', path])
            return f"Folder {path} opened in Explorer."
        except Exception as e:
            return f"Error opening folder: {e}"

    def select_folder(self, ):
        folder_path = filedialog.askdirectory(title="Select Folder")
        return folder_path if folder_path else "No folder selected."

    def get_folder_structure(self, path: str, level: int = 0) -> str:
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

    def get_weather_forecast(city: str, api_key: str) -> str:
        try:
            url = f"http://api.openweathermap.org/data/2.5/forecast"
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

    def google_search(query: str, api_key: str, search_engine_id: str) -> str:
        try:
            url = f"https://www.googleapis.com/customsearch/v1"
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

    def currency_converter(amount: float, from_currency: str, to_currency: str) -> str:
        conversion_rate = 1.2  # Exemplo de taxa de conversão
        converted_amount = amount * conversion_rate
        conversion = {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount,
            'converted_amount': converted_amount
        }
        return json.dumps(conversion)

    def set_reminder(message: str, duration_seconds: int):
        def reminder():
            time.sleep(duration_seconds)
            print(f"Reminder: {message}")
        threading.Thread(target=reminder).start()

    def get_joke() -> str:
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
    def __init__(self, host, tools):
        self.client = AsyncClient(host=host)
        self.tools = tools
        self.messages = load_messages_from_json()

    async def get_response(self, prompt, model):
        self.messages.append({'role': 'user', 'content': prompt})
        response = await self.client.chat(model=model, messages=self.messages)
        self.messages.append(response['message'])
        save_messages_to_json(self.messages)  # Salva o histórico atualizado
        return response['message']['content']
    
    # Função para rodar o LLMTOOLS com as ferramentas
    async def run_tools(self, prompt, model):
        toolsmessages=[{'role': 'user', 'content': prompt}]

        response = await self.client.chat(model=model, messages=toolsmessages, tools=self.tools.instruct_tools)
        self.messages.append(response['message'])

        if response['message'].get('tool_calls'):
            for tool in response['message']['tool_calls']:
                tool_name = tool['function']['name']
                args = tool['function']['arguments']

                if tool_name == 'google_search':
                    args['api_key'] = GOOGLE_API_KEY
                    args['search_engine_id'] = YOUR_SEARCH_ENGINE_ID
                if tool_name == 'get_weather_forecast':
                    args['api_key'] = OPENWEATHERMAP_API_KEY

                tool_result = self.tools.tools_mapping.get(tool_name)
                if tool_result:
                    function_response = tool_result(**args)
                    self.messages.append({'role': 'tool', 'content': function_response})

                final_response = await self.client.chat(model='llama3.2', messages=self.messages)
                self.messages.append(final_response['message'])
                save_messages_to_json(self.messages)  # Salva o histórico atualizado
                return final_response['message']['content']
        return response['message']['content']
    

# Classe para o agente de planejamento
class PlannerAgent:
    def __init__(self, chat_agent, tools_mapping):
        self.chat_agent = chat_agent
        self.tools_mapping = tools_mapping
        #self.messages = load_messages_from_json()

    async def plan_task(self, prompt, model):
        
        template ="""Review the user's message and analyze their intent.

If the user’s message implies they want to interact with another agent, respond with 'agent_call'.
If the user is requesting a tool-based action (such as accessing information, setting reminders, or performing calculations), respond with 'tool_call'.
If neither is relevant, no response is needed.
Tool Mapping: {tools_mapping}

Message History: {messages}

Additionally:

If the prompt suggests the user wants to retry or perform a similar task, refer to Message History to determine if you should make a tool_call based on previous context.
User Input: {userprompt}"""
        template = ChatPromptTemplate.from_template(template)
        Planer_prompt = template.format(tools_mapping=self.tools_mapping ,messages=self.chat_agent.messages, userprompt=prompt)
        response = await self.chat_agent.client.generate(model=model, prompt=Planer_prompt)
        decision = response['response']
        self.chat_agent.messages.append({'role': 'plannerAgent', 'content': decision})
        #print("Decision Text:", decision)  # Inspect the actual text from the LLM

        if "tool_call" in decision.lower():
            print(f"Calling tool:")
            return await self.chat_agent.run_tools(decision, model)
        
        elif "agent_call" in decision.lower():
            print(f"Calling Agent:")
            return await self.chat_agent.get_response(prompt, model)
        else:
            print(f"Calling Agent:")
            return await self.chat_agent.get_response(prompt, model)
        
class AgentINSTRUCT():
    def __init__(self, host):
        self.tools = LLMTOOLS()
        self.chat_agent = ChatAgent(host, self.tools)
        self.planner_agent = PlannerAgent(self.chat_agent, self.tools)

    async def generate(self, prompt, model):
        response = await self.planner_agent.plan_task(prompt, model)
        return response if response else "<EOS>"


# Função principal assíncrona que coordena os agentes
async def main(model):
    host = "127.0.0.1"
    tools = LLMTOOLS()
    chat_agent = ChatAgent(host, tools)
    planner_agent = PlannerAgent(chat_agent, tools)

    while True:
        prompt = input("Enter your question or command: ")
        response = await planner_agent.plan_task(prompt, model=model)
        print("Response:", response)

if __name__ == '__main__':
    asyncio.run(main(model="llama3.2"))