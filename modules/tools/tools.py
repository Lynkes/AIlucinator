import asyncio
import json
import os
import sqlite3
import subprocess
import tkinter as tk
from tkinter import filedialog
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import requests
import time
import threading
from ollama import AsyncClient
# Defina suas chaves de API
GOOGLE_API_KEY = ""
YOUR_SEARCH_ENGINE_ID = ""
OPENWEATHERMAP_API_KEY = ""




class LLMTOOLS():
    def __init__(self, host):
        # Prompt inicial do sistema para IA
        systemprompt = "You are an intelligent virtual assistant designed to assist users with a variety of tasks. You have access to several tools that can help you execute specific functions and provide valuable information. You must respond to the user or use a tool if necessary say' 'tool_calls': 'if the user wants somethin of a tool. How can I assist you today?"
        self.messages = []
        self.messages.append({'role': 'system', 'content': systemprompt,})
        self.client = AsyncClient(host=host)
        with open('E:\\DEV\\AIlucinator\\modules\\tools\\tools.json', 'r') as f:
            self.instruct_tools =json.load(f)
        
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

# Função principal assíncrona
async def run(model: str):
    tools=LLMTOOLS(host="127.0.0.1")
    tools_mapping = {
        'get_folder_structure': tools.get_folder_structure,
        'get_weather_forecast': tools.get_weather_forecast,
        'currency_converter': tools.currency_converter,
        'set_volume': tools.set_volume,
        'increase_volume': tools.increase_volume,
        'decrease_volume': tools.decrease_volume,
        'open_folder': tools.open_folder,
        'open_program': tools.open_program,
        'google_search': tools.google_search,
        'get_joke': tools.get_joke,
        }
    #tools.messages.append({'role': 'user', 'content': 'What is the flight time from New York (NYC) to Los Angeles (LAX)?'})
    while True:
        prompt = input("ASK a tool: ")
        tools.messages.append({'role': 'user', 'content': prompt,})

        response = await tools.client.chat(model=model, messages=tools.messages)
        tools.messages.append(response['message'])

        # Verifica se o modelo usou uma função de ferramenta
        try:
            if response['message'].get('tool_calls'):
                response = await tools.client.chat(model=model, messages=tools.messages, tools=tools.instruct_tools)
                print("TOOL:",response['message'])
                for tool in response['message']['tool_calls']:
                    tool_name = tool['function']['name']
                    args = tool['function']['arguments']

                    if tool_name == 'google_search':
                        args['api_key'] = GOOGLE_API_KEY
                        args['search_engine_id'] = YOUR_SEARCH_ENGINE_ID

                    if tool_name == 'get_weather_forecast':
                        args['api_key'] = OPENWEATHERMAP_API_KEY
                    
                    tool_result = tools_mapping.get(tool_name)
                    if tool_result:
                        function_response = tool_result(**args)
                    #function_response = tools.tools_mapping.get([tool_name](**args))
                    tools.messages.append({'role': 'tool', 'content': function_response,})
                    # Segunda chamada de API: Obter a resposta final do modelo
                    final_response = await tools.client.chat(model=model, messages=tools.messages)
                if final_response['message']['content']:
                    print("TOOL RESPONSE:",final_response['message'])
                    tools.messages.append(final_response['message'])
            else:
                print("IA:",response['message'])
        except Exception as e:
            print(f"Error handling tool call: {e}")

if __name__ == '__main__':
    asyncio.run(run('llama3.2'))
