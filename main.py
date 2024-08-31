import os , torch
from colorama import init as colorama_init
from dotenv import load_dotenv
from resources.utils.env_checker import check_env
from resources.kokoro import Kokoro
from resources import queues

colorama_init(autoreset=True)

if __name__ == "__main__":
    check_env()
    load_dotenv()

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    PERSONALITY = os.environ['personality']
    YOUR_NAME = os.environ['YOUR_NAME']
    LLM = os.environ['LLM']
    LLMMODEL = os.environ['LLMMODEL']
    STT = os.environ['STT']
    TTS = os.environ['TTS']
    #FASTERWISPER VARIABLES
    MODEL_SIZE = os.environ['MODEL_SIZE']
    MODEL_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    MODEL_COMPUTE_TYPE = "float16" if MODEL_DEVICE == "cuda" else "int8"

    #DATABASE VARIABLES
    EMBEDDING_SERVICE = os.environ['EMBEDDING_SERVICE']
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    model_params = {
        "MODEL_SIZE": MODEL_SIZE,
        "MODEL_DEVICE": MODEL_DEVICE,
        "MODEL_COMPUTE_TYPE": MODEL_COMPUTE_TYPE
    }

    kokoro = Kokoro(
        LLM, 
        TTS, 
        STT, 
        model_params,
        PERSONALITY, 
    )

    youtube = ""  # Placeholder for future youtube API integration
    GLaDOS = queues.Queues(
        kokoro, 
        youtube, 
        personality=PERSONALITY, 
        your_name=YOUR_NAME, 
    )

    GLaDOS.run()
