from modules.llm.llm_base import LLMBase
from modules.tts.tts_base import TTSBase
from modules.stt.stt_base import STTBase
from modules.utils.db_utils import initialize_db, update_db
from modules.utils.conversation_utils import load_filtered_words, load_keyword_map, save_inprogress, filter_paragraph
from langchain.prompts import ChatPromptTemplate
from colorama import *
import tiktoken

class Kokoro:
    """
    Classe que implementa funcionalidades para manipulação de conversas com modelos de linguagem, 
    reconhecimento de fala e síntese de voz. Integra provedores de LLM, TTS, e STT.

    Atributos:
        save_folderpath (str): Caminho da pasta onde as conversas são salvas.
        device_index (int): Índice do dispositivo de áudio (opcional).
        llm (str): Provedor de modelo de linguagem (LLM) utilizado.
        tts (str): Provedor de síntese de fala (TTS) utilizado.
        stt (str): Provedor de reconhecimento de fala (STT) utilizado.
        model_params (dict): Parâmetros opcionais para o modelo LLM.
        LLMMODEL (str): Nome do modelo LLM a ser usado.
        model_size (str): Tamanho do modelo STT.
        model_device (str): Dispositivo no qual o modelo STT será executado.
        compute_type (str): Tipo de computação utilizado para o STT.
    """
    
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
        """
        Inicializa a classe Kokoro com os parâmetros fornecidos.

        Args:
            save_folderpath (str): Caminho da pasta onde as conversas são salvas.
            device_index (int, opcional): Índice do dispositivo de áudio.
            llm (str): Nome do provedor LLM.
            tts (str): Nome do provedor TTS.
            stt (str): Nome do provedor STT.
            model_params (dict): Parâmetros opcionais do modelo.
            LLMMODEL (str): Nome do modelo de linguagem.
            model_size (str): Tamanho do modelo STT.
            model_device (str): Dispositivo utilizado para o modelo STT.
            compute_type (str): Tipo de computação utilizada no STT.
        """
        self.save_folderpath = save_folderpath
        self.model = LLMMODEL
        self.llm_provider = LLMBase.get_llm_provider(llm)
        self.tts_provider = TTSBase.get_tts_provider(tts)
        self.stt_provider = STTBase.get_stt_provider(stt, model_size, model_device, compute_type)
        self.stt = stt

        # Inicializa o banco de dados
        self.db = initialize_db(self.save_folderpath)
        # Carrega filtros
        self.filtered_words = load_filtered_words(self.save_folderpath + "/filtered_words.txt")
        self.keyword_map = load_keyword_map(self.save_folderpath + "/keyword_map.json")
        self.messages = [{}]

    def save_conversation(self):
        """
        Salva o progresso da conversa atual no diretório especificado.
        """
        save_inprogress(self.messages, self.save_folderpath)

    def query_rag(self, template, userprompt):
        """
        Realiza uma consulta RAG (Retrieval-Augmented Generation) usando um prompt fornecido.

        Args:
            template (str): Template do prompt.
            userprompt (str): Entrada do usuário para a consulta.

        Returns:
            str: Resposta gerada pelo modelo LLM.
        """
        results = self.db.similarity_search_with_score(userprompt, k=2)
        memoryDB = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        template = ChatPromptTemplate.from_template(template)
        prompt = template.format(memoryDB=memoryDB, messages=self.messages, userprompt=userprompt)
        self.memory_sise(prompt)
        response = self.llm_provider.generate(prompt, self.model)
        return response

    def generate_voice(self, sentence, temp_filename):
        """
        Gera o áudio da fala a partir de uma sentença usando o provedor TTS.

        Args:
            sentence (str): Texto a ser convertido em fala.
            temp_filename (str): Nome temporário do arquivo para salvar o áudio.

        Returns:
            str: Caminho do arquivo de áudio gerado.
        """
        self.tts_provider.generate_speech(sentence, temp_filename)
        return temp_filename

    def listen_for_voice(self, timeout):
        """
        Escuta e detecta comandos de voz por um tempo limite usando o provedor STT.

        Args:
            timeout (int): Tempo limite em segundos para escutar a fala.

        Returns:
            str: Texto reconhecido da fala.
        """
        return self.stt_provider.listen_for_voice(timeout)
    
    def speech_recognition(self, audio):
        """
        Realiza o reconhecimento de fala a partir de um arquivo de áudio.

        Args:
            audio: Arquivo de áudio a ser processado.

        Returns:
            str: Texto reconhecido do áudio.
        """
        return self.stt_provider.recognize_speech(audio)

    def memory_sise(self, prompt):
        """
        Verifica o número de tokens do prompt e reseta a memória se exceder o limite.

        Args:
            prompt (str): O prompt gerado.
        """
        encoding = tiktoken.encoding_for_model("gpt-4")
        total_tokens = len(encoding.encode(prompt))
        if total_tokens >= 7500:
            print(Style.BRIGHT + Fore.YELLOW, f'\nTotal number of tokens: {total_tokens} of 8000. Resetting.')
            self.save_conversation()
            self.db = initialize_db(self.save_folderpath)
            self.messages = [{}]
            
    def filter(self, response):
        """
        Filtra as respostas usando palavras filtradas e mapa de palavras-chave.

        Args:
            response (str): Resposta a ser filtrada.

        Returns:
            str: Resposta filtrada.
        """
        filtered = filter_paragraph(paragraph=response, filtered_words=self.filtered_words, keyword_map=self.keyword_map)
        return filtered
