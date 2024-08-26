import speech_recognition as sr
#import openai
import pyttsx3
from colorama import *
from faster_whisper import WhisperModel
from resources._OS_Utils import *
#from transformers import AutoModelForCausalLM, AutoTokenizer
import ollama
import tiktoken
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from resources.populate_database import get
from langchain_community.vectorstores import Chroma
import io
from resources import populate_database
from resources.populate_database import get
embedding_service = "ollama"
    
class Kokoro:
    def __init__(self, 
                save_folderpath:str = '', 
                device_index = None, 
                keyword:str = 'hey',
                LLMMODEL:str = "gpt-3.5-turbo",
                assistant_name:str = "Exemple",
                model_size:str ="large-v2",
                model_device:str ="cuda",
                model_compute_type:str ="float16",
                chroma_path:str ="chroma",
                db=None,
                ):
        self.keyword = keyword
        self.LLMMODEL = LLMMODEL
        self.assistant_name= assistant_name
        self.model_size = model_size
        self.model_device = model_device
        self.model_compute_type = model_compute_type
        self.save_folderpath = save_folderpath
        self.suffix = get_suffix(save_folderpath)
        self.Whisper = WhisperModel(self.model_size, device=self.model_device, compute_type=self.model_compute_type)
        self.db = db if db else self.initialize_db()
        # Mic Set-up
        self.r = sr.Recognizer()
        self.r.dynamic_energy_threshold=False
        self.r.energy_threshold = 150 # 300 is the default value of the SR library
        self.mic = sr.Microphone(device_index=device_index)
        self.messages=[]
        # pyttsx3 engine Start
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)

    def initialize_db(self):
        embedding_function = get(embedding_service)
        chromaDB = self.save_folderpath+"/chroma"
        db = Chroma(persist_directory=chromaDB, embedding_function=embedding_function)
        return db


    def memory_sise(self):
        encoding = tiktoken.encoding_for_model("gpt-4")
        total_tokens = sum(len(encoding.encode(self.messages)) + len(encoding.encode(self.prompt_template)))
        if total_tokens >= 7500:
            self.save_conversation()
            populate_database.update_DB(self.save_folderpath)
            print(Style.BRIGHT + Fore.YELLOW,f'\nTotal number of tokens:{total_tokens} of 8000 Resetig')
        


    def query_rag(self, PROMPT_TEMPLATE, userprompt:str):
        # Prepare the DB.
        embedding_function = get(embedding_service)
        db = Chroma(persist_directory=self.save_folderpath, embedding_function=embedding_function)

        # Search the DB.
        results = db.similarity_search_with_score(userprompt, k=3)
        memoryDB = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

        # Format the prompt with the retrieved context and user question.
        self.prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        #self.memory_sise()
        print("query_rag")
        prompt = self.prompt_template.format(memoryDB=memoryDB, currentsesion=self.messages, userprompt=userprompt)
        print("query_rag2")
        sources = [doc.metadata.get("id", None) for doc, _score in results]
        print("query_rag3")
        response = self.generate(prompt)
        print("query_rag4")
        formatted_response = f"Response: {response}\nSources: {sources}"

        # Print the formatted response
        print(formatted_response)
        return response

    def generate(self, prompt):
            message=''
            stream = ollama.generate(model=self.LLMMODEL, prompt=prompt, stream=True,)
            for chunk in stream:
                message += chunk['response']
                print(chunk['response'], end='', flush=True)
            print("\n")
            return message

    # def chat(self):
    #     message=''
    #     stream = ollama.chat(model=self.LLMMODEL, messages=self.messages, stream=True,)
    #     print(Style.BRIGHT + Fore.LIGHTYELLOW_EX,"\n",self.assistant_name,":",Style.BRIGHT + Fore.WHITE)
    #     for chunk in stream:
    #         message += chunk['message']['content']
    #         print(chunk['message']['content'], end='', flush=True)
    #     print(Style.BRIGHT + Fore.LIGHTCYAN_EX,"\n")
    #     return message

    def generate_voice(self, sentence, clean_queue=True):
        if clean_queue:
            self.engine.stop()  # Limpa a fila de reprodução
        self.engine.say(sentence)
        self.engine.runAndWait()

    def listen_for_voice(self, timeout: int | None = 5):
        with self.mic as source:
            print("\nListening...")
            self.r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.r.listen(source, timeout)
                print("No longer listening")
                return audio
            except sr.WaitTimeoutError:
                print(Style.BRIGHT + Fore.RED + "Listening timed out")
            except Exception as e:
                print(Style.BRIGHT + Fore.RED + f"An error occurred while listening: {e}")
            return None
    
    def speech_recognition(self, audio):
        try:
            if audio:
                language= "" 
                language_probability= ""
                user_input, language, language_probability = self.fasterwhisper(audio, self.Whisper, language, language_probability)
                print(Style.BRIGHT + Fore.YELLOW + "You said: "+ Fore.WHITE, user_input) # Checking
                if "en" in language or "pt" in language and language_probability >= 0.4:
                    print(Style.BRIGHT + Fore.YELLOW + "You said: "+ Fore.WHITE, user_input) # Checking
                    return user_input
                else:
                    print(Style.BRIGHT + Fore.RED +"False input?")
            else:
                raise ValueError(Style.BRIGHT + Fore.RED + "Empty audio input")
        except:
            user_input = self.r.recognize_google_cloud(audio)
            print(Style.BRIGHT + Fore.YELLOW + "recognizing with google:"+ Fore.WHITE, user_input)
            return user_input
        
    def fasterwhisper(self, audio, model, language, language_probability):
        response = ""
        audio_data = io.BytesIO(audio.get_wav_data())  # Use in-memory bytes buffer
        segments, info = model.transcribe(audio_data, vad_filter=True, beam_size=5)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        for segment in segments:
            response += segment.text
        return response, info.language, info.language_probability
    
    def save_conversation(self):
        save_inprogress(self.messages, self.suffix, self.save_folderpath)


