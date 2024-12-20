import os, sys, globals
from dotenv import load_dotenv
from modules.utils.env_checker import check_env
from modules.kokoro import Kokoro
from modules import queues

globals.processing = True
globals.currently_speaking = False
globals.interrupted = False
globals.interruptible = True
globals.recording_started = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

if __name__ == "__main__":
    """
    Ponto de entrada principal do programa que inicializa o ambiente, carrega
    as variáveis de ambiente e configura os componentes principais da aplicação.

    Variáveis de Ambiente:
        PERSONALITY (str): Personalidade do chatbot.
        YOUR_NAME (str): Nome do usuário do sistema.
        LLMMODEL (str): Modelo de LLM utilizado.
        LLM (str): Provedor do modelo de linguagem.
        STT (str): Provedor de reconhecimento de fala.
        TTS (str): Provedor de síntese de fala.
        MODEL_SIZE (str): Tamanho do modelo STT.
        MODEL_DEVICE (str): Dispositivo utilizado pelo modelo (CPU ou GPU).
        MODEL_COMPUTE_TYPE (str): Tipo de computação do modelo STT (float16 ou int8).
        EMBEDDING_SERVICE (str): Serviço de embeddings utilizado para o RAG.
        DEBUG (str): Indicador de modo de depuração.

    Objetos Iniciados:
        kokoro (Kokoro): Instância da classe Kokoro que lida com processamento de linguagem natural, STT, TTS.
        GLaDOS (Queues): Instância da classe Queues que coordena a execução do chatbot com a personalidade GLaDOS.

    Funções:
        check_env(): Verifica se as variáveis de ambiente estão corretamente configuradas.
        load_dotenv(): Carrega as variáveis de ambiente do arquivo .env.
    """
    check_env()
    load_dotenv()

    PERSONALITY = os.environ['PERSONALITY']
    YOUR_NAME = os.getlogin()
    LLMMODEL = os.environ['LLMMODEL']
    HOST = os.environ['HOST']
    LLM = os.environ['LLM']
    STT = os.environ['STT']
    TTS = os.environ['TTS']
    # FASTERWISPER VARIABLES
    MODEL_SIZE = os.environ['MODEL_SIZE']
    MODEL_DEVICE = "cuda"
    MODEL_COMPUTE_TYPE = "float16" if MODEL_DEVICE == "cuda" else "int8"
    CHARACTER = PERSONALITY
    # DATABASE VARIABLES
    EMBEDDING_SERVICE = os.environ['EMBEDDING_SERVICE']
    DEBUG = os.environ['DEBUG']
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PERSONALITY = SCRIPT_DIR + '/' + 'conversations/' + PERSONALITY
    TTS_MODEL = 'models\\'+os.environ['TTS_MODEL']
    WAKE_WORD = os.environ['WAKE_WORD']
    # print("PERSONALITY=",PERSONALITY)
    model_params = {
        "MODEL_SIZE": MODEL_SIZE,
        "MODEL_DEVICE": MODEL_DEVICE,
        "MODEL_COMPUTE_TYPE": MODEL_COMPUTE_TYPE
    }
    kokoro = Kokoro(
        save_folderpath=PERSONALITY, 
        device_index=None, \
        host=HOST,
        llm=LLM, 
        tts=TTS, 
        stt=STT, 
        tts_model=TTS_MODEL,
        LLMMODEL=LLMMODEL, 
        model_size=MODEL_SIZE, 
        model_device=MODEL_DEVICE,
        compute_type=MODEL_COMPUTE_TYPE,
        wake_word=WAKE_WORD,
    )

    #youtube = ""  # Placeholder para futura integração com API do YouTube
    Ryan = queues.Queues(
        kokoro, 
        #youtube, 
        personality=PERSONALITY, 
        your_name=YOUR_NAME, 
        character=CHARACTER,
        debug=DEBUG,
    )

    Ryan.run()
