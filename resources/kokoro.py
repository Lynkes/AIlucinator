from resources.llm.llm_base import LLMBase
from resources.tts.tts_base import TTSBase
from resources.stt.stt_base import STTBase
from utils.db_utils import initialize_db
from utils import conversation_utils

class Kokoro:
    def __init__(self, save_folderpath='', device_index=None, LLM='', TTS='', STT='', model_params={}, LLMMODEL="gpt-3.5-turbo", model_size="large-v2", model_device="cuda"):
        #LLM, 
        #TTS, 
        #STT, 
        model_params
        self.LLMMODEL = LLMMODEL
        self.save_folderpath = save_folderpath
        self.llm_provider = LLMBase.get_llm_provider()
        self.tts_provider = TTSBase.get_tts_provider()
        self.stt_provider = STTBase.get_stt_provider()
        # Initialize the database
        self.db = initialize_db(save_folderpath)

    def save_conversation(self):
        conversation_utils.save_conversation(messages=self.messages,save_folderpath=self.save_folderpath)

    def query_rag(self, template, userprompt):
        self.memory_sise()
        results = self.db.similarity_search_with_score(userprompt, k=3)
        memoryDB = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt = template.format(memoryDB=memoryDB, userprompt=userprompt)
        response = self.llm_provider.generate(prompt)
        return response

    def generate_voice(self, sentence):
        self.tts_provider.generate_voice(sentence)

    def listen_for_voice(self):
        return self.stt_provider.recognize_speech()
    ############################
    def memory_sise(self):
        encoding = tiktoken.encoding_for_model("gpt-4")
        total_tokens = sum(len(encoding.encode(self.messages)) + len(encoding.encode(self.prompt_template)))
        if total_tokens >= 7500:
            self.save_conversation()
            populate_database.update_DB(self.save_folderpath)
            print(Style.BRIGHT + Fore.YELLOW, f'\nTotal number of tokens: {total_tokens} of 8000. Resetting.')
