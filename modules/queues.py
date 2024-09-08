import threading
import time
from colorama import *
from queue import Queue, Empty
import logging
import keyboard 
from modules.kokoro import Kokoro
from modules.stream.LIVE_youtube_api import YoutubeAPI
from modules.utils.audio_utils import beep, play_audio
from modules.utils.db_utils import update_db

# Configuração de logging com nível de DEBUG para rastreamento detalhado
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Queues:
    def __init__(self, kokoro: Kokoro, 
                 youtube: YoutubeAPI,
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
        # Atributos principais
        self.kokoro = kokoro
        self.youtube = youtube
        self.your_name = your_name
        self.personality = personality
        self.character = character
        self.debug = debug  # Variável de controle de depuração

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

        # Inicializa todas as filas para diferentes propósitos
        self.retrieve_comments_queue = Queue()
        self.gpt_generation_queue = Queue()
        self.separate_sentence_queue = Queue()
        self.stt_recognition_queue = Queue()
        self.tts_generation_queue = Queue()
        self.read_audio_queue = Queue()
        self.PrintResponse_queue = Queue()

        # Inicializa eventos e travas para controle de fluxo
        self.gpt_generated = threading.Event()
        self.sentences_separated = threading.Event()
        self.stt_recognized = threading.Event()
        self.tts_generated = threading.Event()
        self.audio_read = threading.Event()
        self.playing_audio = threading.Event()
        self.audio_lock = threading.Lock()
        self.end_received = threading.Event()

    def run(self):
        """Inicia todas as threads necessárias para o processamento em paralelo."""
        self._log_info("Starting up!")  # Utiliza o método de log que respeita o modo de depuração
        threads = []
        # Lista de funções para executar em threads separadas
        for func in [
            self.gpt_generation, 
            self.separate_sentence, 
            self.stt_recognition,
            self.tts_generation, 
            self.handle_personal_input,
            self.handle_personal_audio,
            self.PrintResponse,
            self.read_audio,
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

    def handle_personal_audio(self, timeout=10):
        """Lida com o input de áudio do usuário quando a tecla 'espaço' é pressionada."""
        while not self.end_received.is_set():
            try:
                # Verifica se a tecla 'espaço' está pressionada
                while keyboard.is_pressed('space'):
                    beep()  # Reproduz um som de feedback
                    self._log_info("Listening for voice input...")
                    audio = self.kokoro.listen_for_voice(timeout)  # Escuta o input de voz
                    if audio:
                        self._log_info("Audio detected")
                        self.stt_recognition_queue.put(audio)  # Coloca o áudio na fila para processamento
                    else:
                        logging.warning("No audio detected or timeout occurred")
                    time.sleep(0.3)  # Pequeno atraso para evitar alto uso de CPU
            except Exception as e:
                logging.error(f"Error in handle_personal_audio: {e}")
            time.sleep(0.3)  # Atraso adicional para evitar alto uso de CPU

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

    def retrieve_comments(self):
        """Recupera comentários do YouTube e os envia para processamento de GPT."""
        while not self.end_received.is_set():
            try:
                msg = self.youtube.msg_queue.get(timeout=5)
                self._log_info("YouTube queue message received")
                complete_message = f"{msg.author.name} said: {msg.message}"
                self.gpt_generation_queue.put(complete_message)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in retrieve_comments: {e}")

    def stt_recognition(self):
        """Realiza o reconhecimento de voz para texto e envia o texto para o processamento de GPT."""
        while not self.end_received.is_set():
            try:
                audio = self.stt_recognition_queue.get(timeout=5)
                self._log_info("STT queue message received")
                stt = self.kokoro.speech_recognition(audio)
                self._log_info(f"STT result: {stt}")
                self.gpt_generation_queue.put(stt)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in stt_recognition: {e}")

    def gpt_generation(self):
        """Gera a resposta de GPT para uma mensagem do usuário."""
        while not self.end_received.is_set():
            if not self.gpt_generation_queue.empty():
                self._log_info("LLM queue received")
                userprompt = self.gpt_generation_queue.get()
                response = self.kokoro.query_rag(template=self.prompt, userprompt=userprompt)
                self.kokoro.messages.append({'role': 'user', 'content': userprompt})
                self.kokoro.messages.append({'role': 'assistant', 'content': response})
                self.separate_sentence_queue.put(response)

    def separate_sentence(self):
        """Separa a resposta gerada pelo GPT em sentenças e as envia para geração de TTS."""
        while not self.end_received.is_set():
            try:
                gpt_response = self.separate_sentence_queue.get(timeout=1)
                self._log_info("Filter sentence queue message received")
                sentences = self.kokoro.filter(gpt_response)
                
                # Inicializa o contador para reiniciá-lo a cada nova resposta
                counter = 0
                
                for sentence in sentences:
                    counter += 1  # Incrementa o contador para cada sentença
                    temp_filename = f"temp_audio_{counter}.wav"  # Nomeia o arquivo temporário usando o contador
                    self.tts_generation_queue.put((sentence, temp_filename))  # Envia para a fila de TTS
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in separate_sentence: {e}")

    def tts_generation(self):
        """Gera o áudio para cada sentença e o salva com um nome de arquivo temporário."""
        while not self.end_received.is_set():
            try:
                sentence, temp_filename = self.tts_generation_queue.get(timeout=1)
                self._log_info("TTS generation queue message received")
                
                # Gera o áudio usando o TTS
                tts_path = self.kokoro.generate_voice(sentence, temp_filename)
                # Adiciona na fila de leitura de áudio
                self.PrintResponse_queue.put(sentence)
                self.read_audio_queue.put(tts_path)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in tts_generation: {e}")


    def PrintResponse(self):
        """Imprime a resposta na tela a partir da fila de respostas."""
        while not self.end_received.is_set():
            try:
                printresponse = self.PrintResponse_queue.get(timeout=1)
                self._log_info("Print response queue message received")  # Usa o método auxiliar de logging
                print(Style.BRIGHT + Fore.LIGHTCYAN_EX, "\n", self.personality, ":", printresponse)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in PrintResponse: {e}")


    def read_audio(self):
        """Lê e reproduz o áudio a partir da fila de leitura de áudio."""
        while not self.end_received.is_set():
            try:
                tts_path = self.read_audio_queue.get(timeout=1)
                self._log_info("Read audio queue message received")  # Usa o método auxiliar de logging
                with self.audio_lock:  # Bloqueia o áudio
                    play_audio(tts_path)
                self.audio_read.set()  # Libera o evento de áudio
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in read_audio: {e}")


