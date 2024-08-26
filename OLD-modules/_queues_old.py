import threading
import time
from colorama import *
from queue import Queue
import tiktoken
from resources.kokoro import Kokoro
from resources._OS_Utils import *
from resources.LIVE_youtube_api import YoutubeAPI
from resources import populate_database
#from resources.RAG import populate_database

class IA_Queues:
    def __init__(self, kokoro: Kokoro, 
                 youtube: YoutubeAPI,
                 save_foldername,
                 assistant_name, 
                 your_name,
                 personality,
                 ):
        self.kokoro = kokoro
        self.youtube = youtube
        self.save_foldername = save_foldername
        self.assistant_name =assistant_name  
        self.your_name=your_name
        self.personality=personality
        

        with open(self.personality, "r", encoding="utf-8") as file:
            self.prompt = file.read()
        populate_database.update_DB(self.save_foldername)
        

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
        # Create an event to signal that the end command has been received
        self.end_received = threading.Event()

    def run(self):
        print(Style.BRIGHT + Fore.GREEN,"\nStarting up!")
        threads = []
        for func in [
            #self.retrieve_comments, 
            self.gpt_generation, 
            self.separate_sentence, 
            self.stt_recognition,
            self.tts_generation, 
            #self.read_audio, 
            self.handle_personal_input,
            self.PrintResponse,
            #self.handle_personal_audio
            ]:
            t = threading.Thread(target=self.thread_wrapper, args=(func,))
            t.start()
            threads.append(t)
        time.sleep(0.1)
        return threads

    def thread_wrapper(self, func):
        while not self.end_received.is_set():
            func()

    # Handle personal Audio input in a separate thread
    def handle_personal_audio(self, timeout=5):
        while not self.end_received.is_set():
            beep()
            #self.tts_generation_queue.put("I'm listening.")
            start_time = time.time()
            audio = self.kokoro.listen_for_voice()
            if audio:
                print(Style.BRIGHT + Fore.LIGHTBLUE_EX,"\nTheres Audio")
                self.stt_recognition_queue.put(audio)
            else:
                if time.time() - start_time > timeout:
                    print(Style.BRIGHT + Fore.LIGHTYELLOW_EX,"\nTimeout")
                continue

    # Handle personal sentence input in a separate thread
    def handle_personal_input(self):
        while not self.end_received.is_set():
            print(Style.BRIGHT + Fore.MAGENTA,)
            personal_sentence = input("\nEnter your question (or 'exit' to save and stop): ")
            print(Style.BRIGHT + Fore.WHITE)
            if personal_sentence.lower() == "save":
                self.kokoro.save_conversation()
                print(Style.BRIGHT + Fore.GREEN,"Saved Conversation") 
            if personal_sentence.lower() == "exit":
                self.kokoro.save_conversation()
                print(Style.BRIGHT + Fore.GREEN,"Saved Conversation") 
                print(Style.BRIGHT + Fore.GREEN,"Quiting") 
                self.end_received.set()
                break
            else:
                self.gpt_generation_queue.put(personal_sentence)

    def retrieve_comments(self):
        while not self.end_received.is_set():
            if not self.youtube.msg_queue.empty():
                print(Style.BRIGHT + Fore.RED,"YOUTUBE QUEUE GOT")
                msg = self.youtube.msg_queue.get()
                print(f"{msg.datetime} [{msg.author.name}]- {msg.message}")
                complete_message = (f"{msg.author.name} said: {msg.message}")
                self.gpt_generation_queue.put(f"{complete_message}")

    def stt_recognition(self):
        while not self.end_received.is_set():
            if not self.stt_recognition_queue.empty():
                print(Style.BRIGHT + Fore.RED,"STT QUEUE GOT")
                audio = self.stt_recognition_queue.get()
                stt = self.kokoro.speech_recognition(audio)
                print(stt)
                self.gpt_generation_queue.put(f"{stt}")
            
    def gpt_generation(self):
        while not self.end_received.is_set():
            encoding = tiktoken.encoding_for_model("gpt-4")
            if not self.gpt_generation_queue.empty():
                print(Style.BRIGHT + Fore.RED,"\nGeneration-GOT")
                userprompt = '{"'+self.gpt_generation_queue.get()+'"}'
                response = Kokoro.query_rag(PROMPT_TEMPLATE=self.prompt, userprompt=userprompt)
                self.kokoro.messages.append({
                'role': 'user',
                'content': userprompt
                    },)
                total_tokens = sum(len(encoding.encode(message['role'])) + len(encoding.encode(message['content'])) for message in self.kokoro.messages)
                print(Style.BRIGHT + Fore.GREEN,f'\nTotal number of tokens:{total_tokens}')
                #response = self.kokoro.chat()
                self.kokoro.messages.append({
                    'role': 'assistant',
                    'content': response
                    },)
                populate_database.update_DB(self.save_foldername)
                #self.PrintResponse_queue.put(response)
                #self.tts_generation_queue.put(f"{response}")
                self.separate_sentence_queue.put(f"{response}")
                
    def separate_sentence(self):
        while not self.end_received.is_set():
            if not self.separate_sentence_queue.empty():
                print(Style.BRIGHT + Fore.RED,"\nFILTER QUEUE GOT")
                gpt_response = self.separate_sentence_queue.get()
                sentences = filter_paragraph(gpt_response)
                for sentence in sentences:
                    self.tts_generation_queue.put(f"{sentence}")
                    #self.PrintResponse_queue(tts_audio)

    def tts_generation(self):
        while not self.end_received.is_set():
            if not self.tts_generation_queue.empty():
                print(Style.BRIGHT + Fore.RED,"\nTTS QUEUE GOT")
                sentence = self.tts_generation_queue.get()
                self.kokoro.generate_voice(f"{sentence}")
                #self.read_audio_queue.put(tts_audio)

    def PrintResponse(self):
        while not self.end_received.is_set():
            if not self.PrintResponse_queue.empty():
                print(Style.BRIGHT + Fore.RED,"\nPRINT QUEUE GOT")
                printresponse = self.PrintResponse_queue.get()
                print(Style.BRIGHT + Fore.LIGHTCYAN_EX,"\n",self.assistant_name,":",printresponse)

    def read_audio(self):
        while not self.end_received.is_set():
            if not self.read_audio_queue.empty():
                print(Style.BRIGHT + Fore.RED,"\nAUDIO QUEUE GOT")
                tts_audio = self.read_audio_queue.get()
                with self.audio_lock:
                    async_play_audio(tts_audio)
                self.audio_read.set()
