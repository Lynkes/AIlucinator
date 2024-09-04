from modules.llm.llm_base import LLMBase
from modules.tts.tts_base import TTSBase
from modules.stt.stt_base import STTBase
from modules.utils.db_utils import initialize_db, update_db
from modules.utils.conversation_utils import load_filtered_words, load_keyword_map, save_inprogress, filter_paragraph
from langchain.prompts import ChatPromptTemplate
from colorama import *
import tiktoken
class Kokoro:
    def __init__(self, 
                 save_folderpath='conversations/GLaDOS/', 
                 device_index=None, 
                 llm='ollama', 
                 tts='vits2', 
                 stt='whisper', 
                 model_params={}, 
                 LLMMODEL="gpt-3.5-turbo", 
                 model_size="large-v2", 
                 model_device="cuda",
                 compute_type="float16"
                 ):
        self.save_folderpath = save_folderpath
        self.llm_provider = LLMBase.get_llm_provider(llm)
        self.tts_provider = TTSBase.get_tts_provider(tts)
        self.stt_provider = STTBase.get_stt_provider(stt)
        self.model = LLMMODEL
        # Initialize the database
        self.db = initialize_db(self.save_folderpath)
        # Load filters
        self.filtered_words = load_filtered_words(self.save_folderpath + "/filtered_words.txt")
        self.keyword_map = load_keyword_map(self.save_folderpath + "/keyword_map.json")
        self.messages= [{}]

    def save_conversation(self):
        save_inprogress(self.messages, self.save_folderpath)

    def query_rag(self, template, userprompt):
        results = self.db.similarity_search_with_score(userprompt, k=3)
        memoryDB = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        template = ChatPromptTemplate.from_template(template)
        prompt = template.format(memoryDB=memoryDB, messages=self.messages,  userprompt=userprompt)
        #self.memory_sise(prompt)
        response = self.llm_provider.generate(prompt, self.model)
        return response

    def generate_voice(self, sentence):
        self.tts_provider.generate_speech(sentence)


    def listen_for_voice(self):
        return self.stt_provider.listen_for_voice()

    ############################
    def memory_sise(self, prompt):
        print("MEMORY SISE")
        encoding = tiktoken.encoding_for_model("gpt-4")
        print("MEMORY SISE2")
        total_tokens = sum(len(encoding.encode(self.messages)) + len(encoding.encode(prompt)))
        print("MEMORY SISE3")
        if total_tokens >= 7500:
            self.save_conversation()
            update_db(self.save_folderpath)
            print(Style.BRIGHT + Fore.YELLOW, f'\nTotal number of tokens: {total_tokens} of 8000. Resetting.')

    def filter(self, response):
        filtrerd=filter_paragraph(paragraph=response, filtered_words= self.filtered_words, keyword_map= self.keyword_map)
        return filtrerd
