import ctypes
import numpy as np
from loguru import logger
from typing import Optional, List
from contextlib import AbstractContextManager

# Importe seu módulo whisper_cpp_wrapper conforme necessário
from . import whisper_cpp_wrapper

# Constantes
WORD_LEVEL_TIMINGS = False
BEAM_SEARCH = True
SILENCE_DURATION_MS = 500  # Duração do silêncio em milissegundos
SAMPLE_RATE = 16000  # Taxa de amostragem do áudio

# Mapeamento de níveis de log do ggml para loguru
_log_at_level = {
    2: logger.error,
    3: logger.warning,
    4: logger.info,
    5: logger.debug
}

def _unlog(level: ctypes.c_int, text: whisper_cpp_wrapper.String, user_data: ctypes.c_void_p) -> None:
    """Callback para redirecionar logs do ggml para o loguru."""
    message = str(text).rstrip()
    _log_at_level.get(level, logger.info)(message)

_unlog_func = whisper_cpp_wrapper.ggml_log_callback(_unlog)

class ASR(AbstractContextManager):
    """
    Classe para reconhecimento automático de fala (ASR) usando o modelo whisper.cpp.

    Atributos:
        ctx (ctypes.c_void_p): Contexto do modelo whisper.cpp.
        params: Parâmetros configurados para a transcrição.
        last_detected_language (Optional[str]): Último idioma detectado.
    """

    def __init__(self, model: str) -> None:
        """
        Inicializa o modelo whisper.cpp e configura os parâmetros.

        Args:
            model (str): Caminho para o arquivo de modelo a ser utilizado.
        """
        # Configura a função de callback para logs do ggml
        whisper_cpp_wrapper.whisper_log_set(_unlog_func, ctypes.c_void_p(0))

        # Inicializa o contexto do modelo a partir do arquivo
        self.ctx = whisper_cpp_wrapper.whisper_init_from_file(model.encode("utf-8"))
        if not self.ctx:
            raise RuntimeError("Falha ao inicializar o modelo whisper.cpp.")

        # Configura os parâmetros de transcrição
        self.params = self._whisper_cpp_params(
            word_level_timings=WORD_LEVEL_TIMINGS,
            beam_search=BEAM_SEARCH,
            detect_language=True  # Ativar detecção automática de linguagem
        )

        # Atributo para armazenar o último idioma detectado
        self.last_detected_language: Optional[str] = None

    def __enter__(self):
        """Suporte ao contexto com 'with'."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Libera recursos ao sair do contexto."""
        self.close()

    def close(self):
        """Libera os recursos alocados pelo whisper.cpp."""
        if hasattr(self, 'ctx') and self.ctx:
            whisper_cpp_wrapper.whisper_free(self.ctx)
            self.ctx = None

    def __del__(self):
        """Destrutor para garantir que os recursos sejam liberados."""
        self.close()

    def _add_silence(self, audio: np.ndarray) -> np.ndarray:
        """
        Adiciona silêncio ao início e ao final do áudio.

        Args:
            audio (np.ndarray): Array NumPy contendo o áudio original.

        Returns:
            np.ndarray: Áudio com silêncio adicionado no início e no fim.
        """
        silence_samples = int((SILENCE_DURATION_MS / 1000) * SAMPLE_RATE)
        silence = np.zeros(silence_samples, dtype=audio.dtype)
        padded_audio = np.concatenate((silence, audio, silence))
        return padded_audio

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcreve o áudio fornecido usando o modelo whisper.cpp.

        Args:
            audio (np.ndarray): Array NumPy contendo o áudio a ser transcrito.

        Returns:
            str: Texto transcrito do áudio.

        Raises:
            RuntimeError: Se ocorrer um erro durante a transcrição.
        """
        if not isinstance(audio, np.ndarray):
            raise TypeError("O áudio deve ser um np.ndarray.")

        # Resetar a linguagem detectada antes de cada transcrição
        self.last_detected_language = None

        # Verifique o comprimento do áudio
        audio_length = len(audio)
        logger.info(f"Comprimento do áudio: {audio_length} amostras")

        # Adiciona silêncio ao áudio
        audio = self._add_silence(audio)

        # Verifique o novo comprimento do áudio
        audio_length = len(audio)
        logger.info(f"Comprimento do áudio após adicionar silêncio: {audio_length} amostras")

        # Prepara o áudio para a transcrição
        audio_float32 = audio.astype(np.float32)  # Certifique-se de que o áudio está em float32
        whisper_cpp_audio = audio_float32.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

        # Chama a função de transcrição do whisper.cpp
        result = whisper_cpp_wrapper.whisper_full(self.ctx, self.params, whisper_cpp_audio, audio_length)
        if result != 0:
            raise RuntimeError(f"Erro do whisper.cpp: código de erro {result}")

        # Obtém o idioma detectado, se a detecção estiver ativada
        if self.params.detect_language:
            lang_id = whisper_cpp_wrapper.whisper_full_lang_id(self.ctx)
            if lang_id >= 0:
                lang_str_ptr = whisper_cpp_wrapper.whisper_lang_str(lang_id)
                if lang_str_ptr:
                    self.last_detected_language = lang_str_ptr.decode('utf-8')
                    logger.info(f"Idioma detectado: {self.last_detected_language}")
            else:
                logger.warning("Não foi possível detectar o idioma.")

        # Obtém o número de segmentos transcritos
        n_segments = whisper_cpp_wrapper.whisper_full_n_segments(self.ctx)
        logger.debug(f"Número de segmentos transcritos: {n_segments}")

        # Extrai o texto de cada segmento
        text_segments: List[str] = []
        for i in range(n_segments):
            segment_ptr = whisper_cpp_wrapper.whisper_full_get_segment_text(self.ctx, i)
            if segment_ptr:
                segment_text = segment_ptr.decode("utf-8")
                text_segments.append(segment_text)
            else:
                logger.warning(f"Segmento {i} retornou None.")

        # Concatena os segmentos para formar o texto completo
        full_text = ''.join(text_segments).strip()
        logger.info(f"Texto transcrito: {full_text}")

        return full_text

    def _whisper_cpp_params(
        self,
        word_level_timings: bool,
        beam_search: bool = True,
        print_realtime: bool = False,
        print_progress: bool = False,
        detect_language: bool = False
    ):
        """
        Configura os parâmetros para a transcrição usando o whisper.cpp.

        Args:
            word_level_timings (bool): Se True, retorna timestamps em nível de palavra.
            beam_search (bool): Se True, usa busca em feixe; caso contrário, busca gananciosa.
            print_realtime (bool): Se True, imprime informações em tempo real.
            print_progress (bool): Se True, imprime o progresso da transcrição.
            detect_language (bool): Se True, ativa a detecção automática de linguagem.

        Returns:
            Parâmetros configurados para uso com o whisper.cpp.
        """
        if beam_search:
            sampling_strategy = whisper_cpp_wrapper.WHISPER_SAMPLING_BEAM_SEARCH
        else:
            sampling_strategy = whisper_cpp_wrapper.WHISPER_SAMPLING_GREEDY

        params = whisper_cpp_wrapper.whisper_full_default_params(sampling_strategy)
        params.print_realtime = print_realtime
        params.print_progress = print_progress
        params.detect_language = detect_language
        params.token_timestamps = word_level_timings
        params.no_timestamps = True
        return params

# Exemplo de uso
if __name__ == "__main__":
    # Carregue seu áudio aqui como um np.ndarray
    # Para fins de exemplo, criaremos um array de zeros
    audio_data = np.zeros(int(SAMPLE_RATE * 5), dtype=np.float32)  # Áudio de 5 segundos de silêncio

    # Caminho para o modelo (ajuste conforme necessário)
    model_path = "path/to/your/whisper/model.bin"

    try:
        with ASR(model=model_path) as asr:
            transcribed_text = asr.transcribe(audio_data)
            print(f"Texto transcrito: {transcribed_text}")
    except Exception as e:
        logger.error(f"Ocorreu um erro durante a transcrição: {e}")
