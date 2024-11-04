from modules.llm.llm_base import LLMBase
from colorama import *
import requests
from modules.utils.conversation_utils import process_line, clean_raw_bytes, process_sentence
from jinja2 import Template
import globals
from ollama import AsyncClient, Client
from modules.tools import tools_mapping  # Assumindo que você tenha um mapeamento de tools aqui
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
import pyautogui
from ollama import AsyncClient
import requests
import time
import threading

class INSTRUCT(LLMBase):
    def __init__(self, host, system):
        self.client = AsyncClient(host=host)
        with open('E:\\DEV\\AIlucinator\\modules\\tools\\tools.json', 'r') as f:
            self.tools = json.load(f)

    async def generate(self, prompt, model):
        response = await self.client.chat(model=model, messages=messages, tools=tools)
        print(response['message'])
        messages.append(response['message'])

        # Verifica se o modelo usou uma função de ferramenta
        if response['message'].get('tool_calls'):
            for tool in response['message']['tool_calls']:
                tool_name = tool['function']['name']
                args = tool['function']['arguments']

                if tool_name == 'google_search':
                    args['api_key'] = GOOGLE_API_KEY
                    args['search_engine_id'] = YOUR_SEARCH_ENGINE_ID

                if tool_name == 'get_weather_forecast':
                    args['api_key'] = OPENWEATHERMAP_API_KEY

                tool_result = tools_mapping[tool_name](**args)
                print(tool_result)
                messages.append({'role': tool_name, 'content': tool_result})

    def _check_tools(self, message, model):
        """
        Checks if any tool should be invoked based on the message content.
        """
        # Assuming tool calls are returned in the message
        if 'tool_calls' in message:
            for tool in message['tool_calls']:
                tool_name = tool['function']['name']
                args = tool['function']['arguments']

                # Call the tool from the tool mapping
                function = tools_mapping.get(tool_name)
                if function:
                    tool_result = function(**args)  # Execute the tool function
                    tool_response = {'role': 'tool', 'content': tool_result}
                    self.messages.append(tool_response)
                    
                    # Re-run the model generation with the updated tool response
                    return self.generate(prompt=self.template.render(messages=self.messages, bos_token="<|begin_of_text|>", add_generation_prompt=True), model=model)
        
        # If no tools are used, return the generated message
        return message if message else "<EOS>"
