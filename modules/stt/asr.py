import ctypes
import numpy as np
from loguru import logger
from . import whisper_cpp_wrapper

WORD_LEVEL_TIMINGS = False
BEAM_SEARCH = True

# Mapeamento manual de IDs de linguagem para strings
LANG_ID_TO_STRING = {
    0: "English",
    1: "Chinese",
    2: "German",
    3: "Spanish",
    4: "Russian",
    5: "Korean",
    6: "French",
    7: "Japanese",
    8: "Portuguese",
    9: "Turkish",
    10: "Polish",
    11: "Catalan",
    12: "Dutch",
    13: "Arabic",
    14: "Swedish",
    15: "Italian",
    16: "Indonesian",
    17: "Hindi",
    18: "Finnish",
    19: "Vietnamese",
    20: "Hebrew",
    21: "Ukrainian",
    22: "Greek",
    23: "Malay",
    24: "Czech",
    25: "Romanian",
    26: "Danish",
    27: "Hungarian",
    28: "Tamil",
    29: "Norwegian",
    30: "Thai",
    31: "Bengali",
    32: "Persian",
    33: "Telugu",
    34: "Filipino",
    35: "Malayalam",
    36: "Sinhala",
    37: "Slovak",
    38: "Croatian",
    39: "Serbian",
    40: "Bulgarian",
    41: "Lithuanian",
    42: "Latvian",
    43: "Estonian",
    44: "Slovenian",
    45: "Kannada",
    46: "Azerbaijani",
    47: "Urd",
    48: "Amharic",
    49: "Yoruba",
    50: "Swahili",
}

# Translate ggml log levels to loguru levels
_log_at_level = {2: logger.error, 3: logger.warning, 4: logger.info, 5: logger.debug}

def _unlog(level: ctypes.c_int, text: ctypes.c_char_p, user_data: ctypes.c_void_p) -> None:
    _log_at_level[level](text.rstrip())

_unlog_func = whisper_cpp_wrapper.ggml_log_callback(_unlog)

class ASR:
    def __init__(self, model: str) -> None:
        whisper_cpp_wrapper.whisper_log_set(_unlog_func, ctypes.c_void_p(0))
        self.ctx = whisper_cpp_wrapper.whisper_init_from_file(model.encode("utf-8"))
        self.params = self._whisper_cpp_params(
            word_level_timings=WORD_LEVEL_TIMINGS,
            beam_search=BEAM_SEARCH,
            detect_language=True,  # Ativar detecção automática de linguagem
        )

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio using the given parameters.

        Any is whisper_cpp.WhisperParams, but we can't import that here
        because it's a C++ class.
        """
        global last_detected_language
        
        # Resetar a linguagem detectada antes de cada transcrição
        last_detected_language = None

        # Verifique o comprimento do áudio
        audio_length = len(audio)
        logger.info(f"Comprimento do áudio: {audio_length} amostras")

        # Detectar linguagem automaticamente
        whisper_cpp_audio = audio.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        lang_id = whisper_cpp_wrapper.whisper_lang_auto_detect(self.ctx, audio_length, 0, whisper_cpp_audio)

        if lang_id >= 0:
            # Usar mapeamento manual para converter lang_id em string
            last_detected_language = LANG_ID_TO_STRING.get(lang_id, "Unknown")
            logger.info(f"Linguagem detectada: {last_detected_language}")
        else:
            logger.warning("Falha na detecção automática de linguagem.")
        
        # Transcrição do áudio
        result = whisper_cpp_wrapper.whisper_full(self.ctx, self.params, whisper_cpp_audio, audio_length)
        if result != 0:
            raise Exception(f"Error from whisper.cpp: {result}")

        n_segments = whisper_cpp_wrapper.whisper_full_n_segments(self.ctx)
        text = [
            whisper_cpp_wrapper.whisper_full_get_segment_text(self.ctx, i)
            for i in range(n_segments)
        ]

        return text[0].decode("utf-8")[1:] if text else ""

    def __del__(self):
        whisper_cpp_wrapper.whisper_free(self.ctx)

    def _whisper_cpp_params(
        self,
        word_level_timings: bool,
        beam_search: bool = True,
        print_realtime=False,
        print_progress=False,
        detect_language=False,  # Parâmetro para detecção automática de linguagem
    ):
        if beam_search:
            params = whisper_cpp_wrapper.whisper_full_default_params(
                whisper_cpp_wrapper.WHISPER_SAMPLING_BEAM_SEARCH
            )
        else:
            params = whisper_cpp_wrapper.whisper_full_default_params(
                whisper_cpp_wrapper.WHISPER_SAMPLING_GREEDY
            )

        params.print_realtime = print_realtime
        params.print_progress = print_progress
        params.detect_language = detect_language  # Habilita a detecção automática da linguagem
        params.token_timestamps = word_level_timings
        params.no_timestamps = True
        return params
