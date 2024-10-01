import threading
import time
from colorama import *
from queue import Queue, Empty
import logging
import keyboard 
from modules.kokoro import Kokoro
#from modules.stream.LIVE_youtube_api import YoutubeAPI
from modules.utils.audio_utils import beep, play_audio, percentage_played_audio, clip_interrupted_sentence
from modules.utils.db_utils import update_db
from modules.utils.conversation_utils import process_line, clean_raw_bytes, process_sentence
from modules.stt import vad
import globals
import copy
import json
import queue
import re
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

import numpy as np
import requests
import sounddevice as sd
import yaml
from Levenshtein import distance
from loguru import logger
from sounddevice import CallbackFlags

OPENAI_API_KEY= ""
HOST = "127.0.0.1"
WAKE = "glados"
VOICE_MODEL ="conversations\GLaDOS\pipermodel\glados.onnx"
ASR_MODEL = "ggml-large-32-2.en.bin"
VAD_MODEL = "silero_vad.onnx"
LLM_STOP_SEQUENCE = "<|eot_id|>"  
# End of sentence token for Meta-Llama-3
PAUSE_TIME = 0.05  
# Time to wait between processing loops
SAMPLE_RATE = 16000  
# Sample rate for input stream
VAD_SIZE = 50  
# Milliseconds of sample for Voice Activity Detection (VAD)
VAD_THRESHOLD = 0.9  
# Threshold for VAD detection
BUFFER_SIZE = 600  
# Milliseconds of buffer before VAD detection
PAUSE_LIMIT = 400  
# Milliseconds of pause allowed before processing
SIMILARITY_THRESHOLD = 2  
# Threshold for wake word similarity

# Configuração de logging com nível de DEBUG para rastreamento detalhado
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Queues:
    def __init__(self, kokoro: Kokoro, 
                 #youtube: YoutubeAPI,
                 your_name,
                 personality,
                 character,
                 debug=False):
        """
        Inicializa a classe Queues com múltiplas filas para processamento de voz, texto e outros eventos.

        Args:
            kokoro (Kokoro): Instância da classe Kokoro para manipulação de voz e texto.
            youtube (YoutubeAPI): Instância da API do YouTube para receber mensagens de chat.
            your_name (str): Nome do usuário.
            personality (str): Personalidade carregada a partir de um arquivo.
            character (str): Nome do personagem para interações.
            debug (bool): Flag para controle de mensagens de depuração (default: False).
        """

                # Inicializa todas as filas para diferentes propósitos
        self.retrieve_comments_queue = Queue()
        self.gpt_generation_queue = Queue()
        self.tts_generation_queue = Queue()
        self._vad_model = vad.VAD(model_path=str(Path.cwd() / "models" / VAD_MODEL))
        # Inicializa eventos e travas para controle de fluxo
        self.gpt_generated = threading.Event()
        self.tts_generated = threading.Event()
        self.end_received = threading.Event()

        # Atributos principais
        self.kokoro = kokoro
        #self.youtube = youtube
        self.your_name = your_name
        self.personality = personality
        self.character = character
        self.debug = debug  # Variável de controle de depuração
        #self.stt_recognition()

        # Limpa mensagens anteriores, se houver
        if self.kokoro.messages:
            self.kokoro.messages = [{}]
            print("\nSelf.kokoro.messages = VAZIO")

        # Inicializa a base de dados se não existir
        if not hasattr(self.kokoro, 'db'):
            self.kokoro.__init__

        # Carrega o prompt da personalidade a partir de um arquivo
        try:
            with open(self.personality+".txt", "r", encoding="utf-8") as file:
                self.prompt = file.read()
                print("TEMPLATE LOADED")
        except Exception as e:
            logging.error(f"Error loading personality prompt: {e}")
            self.prompt = ""

    def run(self):
        """Inicia todas as threads necessárias para o processamento em paralelo."""
        self._log_info("Starting up!")  # Utiliza o método de log que respeita o modo de depuração
        threads = []
        # Lista de funções para executar em threads separadas
        for func in [
            self.gpt_generation, 
            self.tts_generation,
            self.stt_recognition,
            self.handle_personal_input,
        ]:
            t = threading.Thread(target=self.thread_wrapper, args=(func,))
            t.start()
            threads.append(t)
        time.sleep(0.1)  # Pequeno atraso para garantir que todas as threads iniciem corretamente
        return threads

    def thread_wrapper(self, func):
        """Função que encapsula a execução das threads para tratamento de exceções."""
        while not self.end_received.is_set():
            try:
                func()
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")

    def _log_info(self, message):
        """
        Método auxiliar para logar informações, respeitando a flag de depuração.

        Args:
            message (str): Mensagem a ser logada.
        """
        if self.debug:
            logging.info(message)

    def handle_personal_input(self):
        """Lida com o input textual do usuário e comandos especiais ('save', 'exit')."""
        while not self.end_received.is_set():
            try:
                print(Style.BRIGHT + Fore.MAGENTA,)
                personal_sentence = input("\nEnter your question (or 'exit' to save and stop): ")
                print(Style.BRIGHT + Fore.WHITE)
                if personal_sentence.lower() == "save":
                    self.kokoro.save_conversation()
                    self._log_info("Conversation saved")
                elif personal_sentence.lower() == "exit":
                    self.kokoro.save_conversation()
                    self._log_info("Conversation saved. Quitting.")
                    self.end_received.set()
                    break
                else:
                    self.gpt_generation_queue.put(personal_sentence)
            except Exception as e:
                logging.error(f"Error in handle_personal_input: {e}")

    def stt_recognition(self):
        """
        Starts the Glados voice assistant, continuously listening for input and responding.
        """
        try:
                recognized_text = self.kokoro.listen_for_voice(timeout=5)
                if recognized_text:
                    logger.info(f"Recognized Text: {recognized_text}")
                    self.gpt_generation_queue.put(recognized_text)
        except Exception as e:
                logging.error(f"Error in stt_recognition: {e}")

    def gpt_generation(self):
        """
        Processes the detected text using the LLM model.

        """
        while not self.end_received.is_set():
            try:
                detected_text = self.gpt_generation_queue.get(timeout=0.1)
                response = self.kokoro.query_rag(template=self.prompt, userprompt=detected_text)
                globals.processing = True
                globals.currently_speaking = True
                self.kokoro.messages.append({'role': self.your_name, 'content': detected_text})
                if response != None:
                    self.tts_generation_queue.put(response)
            except queue.Empty:
                time.sleep(PAUSE_TIME)

    def tts_generation(self):
        """
        Processes the LLM generated text using the TTS model.

        Runs in a separate thread to allow for continuous processing of the LLM output.
        """
        assistant_text = (
            []
        )  # The text generated by the assistant, to be spoken by the TTS
        system_text = (
            []
        )  # The text logged to the system prompt when the TTS is interrupted
        finished = False  # a flag to indicate when the TTS has finished speaking
        globals.interrupted = (
            False  # a flag to indicate when the TTS was interrupted by new input
        )

        while not self.end_received.is_set():
            try:
                generated_text = self.tts_generation_queue.get(timeout=PAUSE_TIME)

                if (
                    generated_text == "<EOS>"
                ):  # End of stream token generated in process_LLM_thread
                    finished = True
                elif not generated_text:
                    self._log_info("Empty string sent to TTS")  # should not happen!
                else:
                    self._log_info(f"TTS text: {generated_text}")
                    audio, rate = self.kokoro.generate_voice(generated_text)
                    total_samples = len(audio)

                    if total_samples and rate:
                        sd.play(audio, rate)

                        percentage_played = percentage_played_audio(
                            total_samples,
                            rate
                        )
                        if globals.interrupted:
                            self.tts_generation_queue = queue.Queue()
                            clipped_text = clip_interrupted_sentence(
                                generated_text, percentage_played
                            )
                            self._log_info(
                                f"TTS interrupted at {percentage_played}%: {clipped_text}"
                            )
                            system_text = copy.deepcopy(assistant_text)
                            system_text.append(clipped_text)
                            finished = True
                        assistant_text.append(generated_text)
                if finished:
                    self.kokoro.messages.append({"role": self.character, "content": " ".join(assistant_text)})
                    if globals.interrupted:
                         self.kokoro.messages.append({
                                 "role": "system",
                                 "content": f"USER INTERRUPTED GLADOS, TEXT DELIVERED: {' '.join(system_text)}",})
                    assistant_text = []
                    finished = False
                    globals.interrupted = False
                    globals.currently_speaking = False

            except queue.Empty:
                pass