import ctypes
import numpy as np
from loguru import logger
from . import whisper_cpp_wrapper

WORD_LEVEL_TIMINGS = False
BEAM_SEARCH = True
SILENCE_DURATION_MS = 500  # Duração do silêncio em milissegundos
SAMPLE_RATE = 16000  # Taxa de amostragem do áudio, ajuste conforme necessário

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

    def _add_silence(self, audio: np.ndarray) -> np.ndarray:
        """Adiciona silêncio ao início e ao final do áudio."""
        silence_samples = int((SILENCE_DURATION_MS / 1000) * SAMPLE_RATE)  # Converte ms para amostras
        silence = np.zeros(silence_samples, dtype=audio.dtype)  # Cria o array de silêncio

        # Adiciona silêncio ao início e ao final
        padded_audio = np.concatenate((silence, audio, silence))
        return padded_audio

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio using the given parameters."""
        global last_detected_language
        
        # Resetar a linguagem detectada antes de cada transcrição
        last_detected_language = None

        # Verifique o comprimento do áudio
        audio_length = len(audio)
        logger.info(f"Comprimento do áudio: {audio_length} amostras")

        # Adiciona silêncio ao áudio
        audio = self._add_silence(audio)

        # Verifique o novo comprimento do áudio
        audio_length = len(audio)
        logger.info(f"Comprimento do áudio após adicionar silêncio: {audio_length} amostras")

        # Detectar linguagem automaticamente
        whisper_cpp_audio = audio.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        
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
