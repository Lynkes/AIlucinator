from llm.ollama_provider import OllamaProvider
from tts.pyttsx3_provider import Pyttsx3Provider
from stt.faster_whisper_provider import FasterWhisperProvider
from utils.db_utils import initialize_db
from utils.conversation_utils import save_conversation

class Kokoro:
    def __init__(self, save_folderpath='', device_index=None, LLMMODEL="gpt-3.5-turbo", model_size="large-v2", model_device="cuda"):
        self.LLMMODEL = LLMMODEL
        self.save_folderpath = save_folderpath
        self.suffix = get_suffix(save_folderpath)
        self.llm_provider = OllamaProvider(model=LLMMODEL)
        self.tts_provider = Pyttsx3Provider()
        self.stt_provider = FasterWhisperProvider(model_size=model_size, device=model_device)
        self.db = initialize_db(save_folderpath)

    # Example methods using providers:
    def query_rag(self, template, userprompt):
        results = self.db.similarity_search_with_score(userprompt, k=3)
        memoryDB = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt = self.prompt_template.format(memoryDB=memoryDB, userprompt=userprompt)
        response = self.llm_provider.generate(prompt)
        return response

    def generate_voice(self, sentence):
        self.tts_provider.generate_voice(sentence)

    def listen_for_voice(self):
        # Implementation with self.stt_provider
        pass
