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

# Configuração de logging com nível de INFO
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# End of sentence token for Meta-Llama-3
PAUSE_TIME = 0.05  

class Queues:
    def __init__(self, kokoro: Kokoro, your_name, personality, character, debug=False):
        """
        Inicializa a classe Queues com múltiplas filas para processamento de voz, texto e outros eventos.
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

        if self.kokoro.messages:
            self.kokoro.messages = [{}]
            logging.info("Self.kokoro.messages cleared.")

        # Carrega o prompt da personalidade
        try:
            with open(f"{self.personality}.txt", "r", encoding="utf-8") as file:
                self.prompt = file.read()
                logging.info("Personality template loaded.")
        except Exception as e:
            logging.error(f"Error loading personality prompt: {e}")
            self.prompt = ""

    def run(self):
        """Inicia todas as threads necessárias para o processamento em paralelo."""
        self._log_info("Starting up!")
        threads = []
        for func in [self.gpt_generation, self.tts_generation, self.stt_recognition, self.handle_personal_input]:
            t = threading.Thread(target=self.thread_wrapper, args=(func,))
            t.start()
            threads.append(t)
        return threads

    def thread_wrapper(self, func):
        """Função que encapsula a execução das threads para tratamento de exceções."""
        while not self.end_received.is_set():
            try:
                func()
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")

    def _log_info(self, message):
        """Loga informações respeitando a flag de depuração."""
        if self.debug:
            logging.info(message)

    def handle_personal_input(self):
        """Lida com o input textual do usuário e comandos especiais ('save', 'exit')."""
        while not self.end_received.is_set():
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

    def stt_recognition(self):
        """Processa a fala em texto e insere na fila de geração de GPT."""
        while not self.end_received.is_set():
            try:
                recognized_text = self.kokoro.listen_for_voice(timeout=5)
                if recognized_text:
                    logger.info(f"Recognized Text: {recognized_text}")
                    self.gpt_generation_queue.put(recognized_text)
            except Exception as e:
                logging.error(f"Error in stt_recognition: {e}")

    def gpt_generation(self):
        """Processa o texto reconhecido usando o modelo GPT."""
        while not self.end_received.is_set():
            try:
                detected_text = self.gpt_generation_queue.get(timeout=0.1)
                response = self.kokoro.query_rag(template=self.prompt, username=self.your_name, userprompt=detected_text)
                if response:
                    self.kokoro.messages.append({'role': self.your_name, 'content': detected_text})
                    self.tts_generation_queue.put(response)
            except queue.Empty:
                time.sleep(PAUSE_TIME)

    def tts_generation(self):
        """Gera áudio a partir do texto e executa a reprodução."""
        assistant_text = []
        while not self.end_received.is_set():
            try:
                generated_text = self.tts_generation_queue.get(timeout=PAUSE_TIME)
                if generated_text == "<EOS>":
                    finished = True
                elif generated_text:
                    audio, rate = self.kokoro.generate_voice(generated_text)
                    if audio and rate:
                        sd.play(audio, rate)
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
