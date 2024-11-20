import threading
import time
import logging
import queue
from queue import Queue
import copy
import sounddevice as sd
from loguru import logger
from colorama import Style, Fore
from modules.kokoro import Kokoro
from modules.utils.audio_utils import percentage_played_audio, clip_interrupted_sentence
import globals
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PAUSE_TIME = 0.05

class Queues:
    def __init__(self, kokoro: Kokoro, your_name, personality, character, debug=False, debug_time_logs=False):
        """
        Inicializa a classe Queues, responsável por gerenciar filas e coordenar a execução
        de diferentes tarefas em threads paralelas.

        Args:
            kokoro (Kokoro): Instância da classe Kokoro para processamento de linguagem.
            your_name (str): Nome do usuário.
            personality (str): Caminho para o arquivo de personalidade do chatbot.
            character (str): Nome do personagem do chatbot.
            debug (bool): Indicador para ativar ou desativar o modo de depuração.
            debug_time_logs (bool): Indicador para ativar ou desativar os logs de tempo.
        """
        self.retrieve_comments_queue = Queue()
        self.gpt_generation_queue = Queue()
        self.tts_generation_queue = Queue()

        self.gpt_generated = threading.Event()
        self.tts_generated = threading.Event()
        self.end_received = threading.Event()

        self.kokoro = kokoro
        self.your_name = your_name
        self.personality = personality
        self.character = character
        self.debug = debug
        self.debug_time_logs = debug_time_logs

        if self.kokoro.messages:
            self.kokoro.messages = [{}]
            logging.info("Self.kokoro.messages cleared.")

        try:
            with open(f"{self.personality}.txt", "r", encoding="utf-8") as file:
                self.prompt = file.read()
                logging.info("Personality template loaded.")
        except Exception as e:
            logging.error(f"Error loading personality prompt: {e}")
            self.prompt = ""

    def run(self):
        """
        Inicia todas as threads necessárias para o processamento em paralelo.

        Returns:
            list: Lista de threads que foram iniciadas.
        """
        self._log_info("Starting up!")
        threads = []
        for func in [self.gpt_generation_wrapper, self.tts_generation, self.stt_recognition, self.handle_personal_input]:
            t = threading.Thread(target=self.thread_wrapper, args=(func,))
            t.start()
            threads.append(t)
        return threads

    def thread_wrapper(self, func):
        """
        Função que encapsula a execução das threads para tratamento de exceções.

        Args:
            func (function): Função a ser executada na thread.
        """
        while not self.end_received.is_set():
            try:
                func()
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")

    def _log_info(self, message):
        """
        Loga informações respeitando a flag de depuração.

        Args:
            message (str): Mensagem a ser registrada.
        """
        if self.debug:
            logging.info(message)

    def gpt_generation_wrapper(self):
        """
        Wrapper para executar gpt_generation com asyncio.run.
        """
        asyncio.run(self.gpt_generation())

    async def gpt_generation(self):
        """
        Processa o texto reconhecido usando o modelo GPT e insere a resposta na fila de TTS.
        """
        while not self.end_received.is_set():
            start_time = time.time()
            try:
                detected_text = self.gpt_generation_queue.get(timeout=0.1)
                response = await self.kokoro.chat(userprompt=detected_text)
                if response:
                    self.tts_generation_queue.put(response)
            except queue.Empty:
                await asyncio.sleep(PAUSE_TIME)
            end_time = time.time()
            if self.debug_time_logs:
                logging.info(f"gpt_generation - Tempo de ciclo: {end_time - start_time:.4f} segundos")

    def handle_personal_input(self):
        """
        Lida com o input textual do usuário e comandos especiais ('save', 'exit').
        """
        while not self.end_received.is_set():
            start_time = time.time()
            try:
                personal_sentence = input(Style.BRIGHT + Fore.MAGENTA + "\nEnter your question (or 'exit' to save and stop): " + Style.BRIGHT + Fore.WHITE)
                if personal_sentence.lower() == "save":
                    self.kokoro.save_conversation()
                    self._log_info("Conversation saved.")
                elif personal_sentence.lower() == "exit":
                    self.kokoro.save_conversation()
                    self._log_info("Conversation saved. Quitting.")
                    self.end_received.set()
                    break
                else:
                    self.gpt_generation_queue.put(personal_sentence)
            except Exception as e:
                logging.error(f"Error in handle_personal_input: {e}")
            end_time = time.time()
            if self.debug_time_logs:
                logging.info(f"handle_personal_input - Tempo de ciclo: {end_time - start_time:.4f} segundos")

    def stt_recognition(self):
        """
        Processa a fala em texto e insere na fila de geração de GPT.
        """
        while not self.end_received.is_set():
            start_time = time.time()
            try:
                recognized_text = self.kokoro.listen_for_voice(timeout=5)
                if recognized_text:
                    logger.info(f"Recognized Text: {recognized_text}")
                    self.gpt_generation_queue.put(recognized_text)
            except Exception as e:
                logging.error(f"Error in stt_recognition: {e}")
            end_time = time.time()
            if self.debug_time_logs:
                logging.info(f"stt_recognition - Tempo de ciclo: {end_time - start_time:.4f} segundos")

    def tts_generation(self):
        """
        Gera áudio a partir do texto e executa a reprodução.
        """
        assistant_text = []
        while not self.end_received.is_set():
            start_time = time.time()
            try:
                generated_text = self.tts_generation_queue.get(timeout=PAUSE_TIME)
                finished = False
                if generated_text == "<EOS>":
                    finished = True
                elif generated_text:
                    logging.info(f"Sent to tts_generation: {generated_text}")
                    audio, rate = self.kokoro.generate_voice(generated_text)
                    if audio.any() and rate:
                        if globals.interrupted:
                            clipped_text = clip_interrupted_sentence(generated_text, percentage_played_audio(len(audio), rate))
                            assistant_text.append(clipped_text)
                        assistant_text.append(generated_text)
                if globals.interrupted or finished:
                    self.kokoro.messages.append({"role": self.character, "content": " ".join(assistant_text)})
                    assistant_text.clear()
                    globals.interrupted = False
            except queue.Empty:
                pass
            end_time = time.time()
            if self.debug_time_logs:
                logging.info(f"tts_generation - Tempo de ciclo: {end_time - start_time:.4f} segundos")
