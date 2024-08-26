import os
from resources.kokoro import Kokoro
from resources._OS_Utils import get_file_paths

def init_kokoro(script_dir, foldername, personality, model_params, chroma_path):
    foldername_dir, personality_dir = get_file_paths(script_dir, foldername, personality)

    _kokoro = Kokoro(
        save_folderpath=foldername_dir,
        LLMMODEL=model_params['LLMMODEL'],
        assistant_name=foldername,
        model_size=model_params['MODEL_SIZE'],
        model_device=model_params['MODEL_DEVICE'],
        model_compute_type=model_params['MODEL_COMPUTE_TYPE'],
        chroma_path=chroma_path
    )

    return _kokoro, foldername_dir, personality_dir
