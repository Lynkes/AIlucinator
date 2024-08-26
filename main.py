import os
from colorama import init as colorama_init
from dotenv import load_dotenv
from utils.env_loader import load_env
from utils.env_checker import check_env
from resources.kokoro_init import init_kokoro
from resources import _queues_

colorama_init(autoreset=True)

if __name__ == "__main__":
    load_dotenv()
    check_env()

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    FOLDERNAME = os.environ['foldername']
    PERSONALITY = os.environ['personality']
    YOUR_NAME = os.environ['YOUR_NAME']
    LLMMODEL = os.environ['LLMMODEL']
    MODEL_SIZE = os.environ['MODEL_SIZE']
    MODEL_DEVICE = "cuda" # if torch.cuda.is_available() else "cpu"
    MODEL_COMPUTE_TYPE = "float16" if MODEL_DEVICE == "cuda" else "int8"
    EMBEDDING_SERVICE = os.environ['EMBEDDING_SERVICE']
    CHROMA_PATH = os.environ['CHROMA_PATH']
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    model_params = {
        "LLMMODEL": LLMMODEL,
        "MODEL_SIZE": MODEL_SIZE,
        "MODEL_DEVICE": MODEL_DEVICE,
        "MODEL_COMPUTE_TYPE": MODEL_COMPUTE_TYPE
    }

    _kokoro, foldername_dir, personality_dir = init_kokoro(
        SCRIPT_DIR, FOLDERNAME, PERSONALITY, model_params, CHROMA_PATH
    )

    youtube = ""  # Placeholder for future youtube API integration
    assistant = _queues_.IA_Queues(
        _kokoro, youtube, foldername_dir, 
        assistant_name=FOLDERNAME, 
        your_name=YOUR_NAME, 
        personality=personality_dir
    )

    assistant.run()
