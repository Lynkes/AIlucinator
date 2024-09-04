import os , torch, sys
from colorama import init as colorama_init
from dotenv import load_dotenv


# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils.env_checker import check_env
from modules.kokoro import Kokoro
from modules import queues

colorama_init(autoreset=True)

if __name__ == "__main__":
    check_env()
    load_dotenv()

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    PERSONALITY = os.environ['personality']
    YOUR_NAME = os.environ['YOUR_NAME']
    LLMMODEL = os.environ['LLMMODEL']
    LLM = os.environ['LLM']
    STT = os.environ['STT']
    TTS = os.environ['TTS']

    #FASTERWISPER VARIABLES

    MODEL_SIZE = os.environ['MODEL_SIZE']
    MODEL_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    MODEL_COMPUTE_TYPE = "float16" if MODEL_DEVICE == "cuda" else "int8"

    #DATABASE VARIABLES
    
    EMBEDDING_SERVICE = os.environ['EMBEDDING_SERVICE']
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PERSONALITY = SCRIPT_DIR+'/'+'conversations/'+PERSONALITY
    print("PERSONALITY=",PERSONALITY)
    model_params = {
        "MODEL_SIZE": MODEL_SIZE,
        "MODEL_DEVICE": MODEL_DEVICE,
        "MODEL_COMPUTE_TYPE": MODEL_COMPUTE_TYPE
    }

    kokoro = Kokoro(
        save_folderpath=PERSONALITY, 
        device_index=None, 
        llm=LLM, 
        tts=TTS, 
        stt=STT, 
        model_params=model_params, 
        LLMMODEL=LLMMODEL, 
        model_size=MODEL_SIZE, 
        model_device=MODEL_DEVICE,
        compute_type=MODEL_COMPUTE_TYPE,
    )

    youtube = ""  # Placeholder for future youtube API integration
    GLaDOS = queues.Queues(
        kokoro, 
        youtube, 
        personality=PERSONALITY, 
        your_name=YOUR_NAME, 
    )

    GLaDOS.run()
