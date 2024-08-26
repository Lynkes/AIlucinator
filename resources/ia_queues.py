import threading
import time
from colorama import *
from queue import Queue, Empty
import logging
from resources.kokoro import Kokoro
from resources.LIVE_youtube_api import YoutubeAPI
from resources._OS_Utils import beep, async_play_audio
from resources import populate_database
from modules.TTS import testglados

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IA_Queues:
    def __init__(self, kokoro: Kokoro, 
                 youtube: YoutubeAPI,
                 save_foldername,
                 assistant_name, 
                 your_name,
                 personality):
        self.kokoro = kokoro
        self.youtube = youtube
        self.save_foldername = save_foldername
        self.assistant_name = assistant_name  
        self.your_name = your_name
        self.personality = personality

        # Initialize the database if Kokoro does not already have one
        if not hasattr(self.kokoro, 'db'):
            self.kokoro.initialize_db()

        # Load the personality prompt
        try:
            with open(self.personality, "r", encoding="utf-8") as file:
                self.prompt = file.read()
        except Exception as e:
            logging.error(f"Error loading personality prompt: {e}")
            self.prompt = ""

        # Initialize the database
        try:
            populate_database.update_DB(self.save_foldername)
        except Exception as e:
            logging.error(f"Error updating database: {e}")

        # Queues
        self.retrieve_comments_queue = Queue()
        self.gpt_generation_queue = Queue()
        self.separate_sentence_queue = Queue()
        self.stt_recognition_queue = Queue()
        self.tts_generation_queue = Queue()
        self.read_audio_queue = Queue()
        self.PrintResponse_queue = Queue()

        # Events
        self.gpt_generated = threading.Event()
        self.sentences_separated = threading.Event()
        self.stt_recognized = threading.Event()
        self.tts_generated = threading.Event()
        self.audio_read = threading.Event()
        self.playing_audio = threading.Event()
        self.audio_lock = threading.Lock()
        self.end_received = threading.Event()

    def run(self):
        logging.info("Starting up!")
        threads = []
        for func in [
            self.gpt_generation, 
            self.separate_sentence, 
            self.stt_recognition,
            self.tts_generation, 
            self.handle_personal_input,
            self.PrintResponse,
            ]:
            t = threading.Thread(target=self.thread_wrapper, args=(func,))
            t.start()
            threads.append(t)
        time.sleep(0.1)
        return threads

    def thread_wrapper(self, func):
        while not self.end_received.is_set():
            try:
                func()
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")

    def handle_personal_audio(self, timeout=5):
        while not self.end_received.is_set():
            try:
                beep()
                start_time = time.time()
                audio = self.kokoro.listen_for_voice()
                if audio:
                    logging.info("Audio detected")
                    self.stt_recognition_queue.put(audio)
                else:
                    if time.time() - start_time > timeout:
                        logging.warning("Audio detection timeout")
            except Exception as e:
                logging.error(f"Error in handle_personal_audio: {e}")

    def handle_personal_input(self):
        while not self.end_received.is_set():
            try:
                print(Style.BRIGHT + Fore.MAGENTA,)
                personal_sentence = input("\nEnter your question (or 'exit' to save and stop): ")
                print(Style.BRIGHT + Fore.WHITE)
                if personal_sentence.lower() == "save":
                    self.kokoro.save_conversation()
                    logging.info("Conversation saved")
                elif personal_sentence.lower() == "exit":
                    self.kokoro.save_conversation()
                    logging.info("Conversation saved. Quitting.")
                    self.end_received.set()
                    break
                else:
                    self.gpt_generation_queue.put(personal_sentence)
            except Exception as e:
                logging.error(f"Error in handle_personal_input: {e}")

    def retrieve_comments(self):
        while not self.end_received.is_set():
            try:
                msg = self.youtube.msg_queue.get(timeout=1)
                logging.info("YouTube queue message received")
                complete_message = f"{msg.author.name} said: {msg.message}"
                self.gpt_generation_queue.put(complete_message)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in retrieve_comments: {e}")

    def stt_recognition(self):
        while not self.end_received.is_set():
            try:
                audio = self.stt_recognition_queue.get(timeout=1)
                logging.info("STT queue message received")
                stt = self.kokoro.speech_recognition(audio)
                logging.info(f"STT result: {stt}")
                self.gpt_generation_queue.put(stt)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in stt_recognition: {e}")

    def gpt_generation(self):
        while not self.end_received.is_set():
            if not self.gpt_generation_queue.empty():
                print(Style.BRIGHT + Fore.GREEN, "\nGeneration-GOT")
                userprompt = self.gpt_generation_queue.get()
                print(Style.BRIGHT + Fore.RED, "\nTEST")
                response = self.kokoro.query_rag(template=self.prompt, userprompt=userprompt)
                print(Style.BRIGHT + Fore.RED, "\nTEST2")
                self.kokoro.messages.append({
                    'role': 'user',
                    'content': userprompt
                })
                self.kokoro.messages.append({
                    'role': 'assistant',
                    'content': response
                })
                self.separate_sentence_queue.put(response)

    def separate_sentence(self):
        while not self.end_received.is_set():
            try:
                gpt_response = self.separate_sentence_queue.get(timeout=1)
                logging.info("Separate sentence queue message received")
                sentences = filter_paragraph(gpt_response)
                for sentence in sentences:
                    self.tts_generation_queue.put(sentence)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in separate_sentence: {e}")

    def tts_generation(self):
        while not self.end_received.is_set():
            try:
                sentence = self.tts_generation_queue.get(timeout=1)
                logging.info("TTS generation queue message received")
                testglados.Generateaudio(sentence)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in tts_generation: {e}")

    def PrintResponse(self):
        while not self.end_received.is_set():
            try:
                printresponse = self.PrintResponse_queue.get(timeout=1)
                logging.info("Print response queue message received")
                print(Style.BRIGHT + Fore.LIGHTCYAN_EX, "\n", self.assistant_name, ":", printresponse)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in PrintResponse: {e}")

    def read_audio(self):
        while not self.end_received.is_set():
            try:
                tts_audio = self.read_audio_queue.get(timeout=1)
                logging.info("Read audio queue message received")
                with self.audio_lock:
                    async_play_audio(tts_audio)
                self.audio_read.set()
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in read_audio: {e}")
