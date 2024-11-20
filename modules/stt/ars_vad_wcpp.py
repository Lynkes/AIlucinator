import queue
import numpy as np
import sounddevice as sd
from loguru import logger
import threading
from pathlib import Path
from typing import Any, List
from sounddevice import CallbackFlags
import time
from collections import deque

from .asr import ASR
from .vad import VAD
import globals

# Constantes
VAD_MODEL_PATH = "silero_vad.onnx"
SAMPLE_RATE = 16000
VAD_SIZE = 50  # ms
VAD_THRESHOLD = 0.5  # Valor inicial
PAUSE_LIMIT = 1300  # ms
SIMILARITY_THRESHOLD = 2  # Limiar de distância de Levenshtein
ALPHA = 0.1  # Taxa de suavização exponencial
MEDIAN_FILTER_SIZE = 5  # Tamanho do filtro de mediana
THRESHOLD_MULTIPLIER = 0.7  # Multiplicador para ajustar o limiar
PRE_RECORD_BUFFER_MS = 500  # Tamanho do buffer de pré-gravação em ms

class VoiceRecognition:
    """
    Classe para reconhecimento de voz utilizando VAD (Voice Activity Detection) e ASR (Automatic Speech Recognition).
    """

    def __init__(self, model_size_or_path="large-v3", device="cuda", compute_type="float16", wake_word: str | None = None):
        """
        Inicializa a classe VoiceRecognition com os parâmetros fornecidos.

        Args:
            model_size_or_path (str): Caminho ou nome do modelo ASR a ser utilizado.
            device (str): Dispositivo para executar o modelo (ex.: 'cuda').
            compute_type (str): Tipo de cálculo a ser utilizado no modelo.
            wake_word (str | None): Palavra-chave para ativação do sistema de reconhecimento.
        """
        self.wake_word = wake_word
        self.samples: List[np.ndarray] = []
        globals.recording_started = False
        self.gap_counter = 0
        self.shutdown_event = threading.Event()

        # Variáveis para VAD_THRESHOLD e confiança
        self.dynamic_threshold = VAD_THRESHOLD
        self.confidence_deque = deque(maxlen=MEDIAN_FILTER_SIZE)
        self.smoothed_confidence = None  # Para a média móvel exponencial

        # Buffer de pré-gravação
        self.buffer = deque(maxlen=int(PRE_RECORD_BUFFER_MS / VAD_SIZE))

        # Fila para comunicação entre o callback e a função de processamento
        self.sample_queue = queue.Queue()

        # Configuração de entrada de áudio
        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000),
        )

        # Inicialização dos modelos
        self.vad_model = VAD(model_path=str(Path.cwd() / "models" / VAD_MODEL_PATH))
        self.asr_model = ASR(model=str(Path.cwd() / "models" / model_size_or_path))

    def audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: CallbackFlags):
        """
        Callback de áudio utilizado para processar áudio em tempo real.

        Args:
            indata (np.ndarray): Dados de entrada do áudio.
            frames (int): Número de frames de áudio.
            time_info (Any): Tempo de áudio.
            status (CallbackFlags): Status da entrada de áudio.
        """
        if status:
            logger.warning(f"Audio callback status: {status}")

        data = indata.copy().squeeze()
        vad_confidence = self.vad_model.process_chunk(data)

        # Atualiza o valor suavizado exponencialmente
        if self.smoothed_confidence is None:
            self.smoothed_confidence = vad_confidence
        else:
            self.smoothed_confidence = (ALPHA * vad_confidence) + ((1 - ALPHA) * self.smoothed_confidence)

        # Adiciona ao filtro de mediana
        self.confidence_deque.append(self.smoothed_confidence)
        if len(self.confidence_deque) == MEDIAN_FILTER_SIZE:
            median_confidence = np.median(self.confidence_deque)
            self.dynamic_threshold = median_confidence * THRESHOLD_MULTIPLIER

        # Armazena o áudio no buffer de pré-gravação
        self.buffer.append(data)

        # Envia os dados para a fila
        self.sample_queue.put((data, vad_confidence))

    def wakeword_detected(self, text: str) -> bool:
        """
        Verifica se a palavra-chave (wake word) está presente no texto reconhecido.

        Args:
            text (str): Texto reconhecido pelo ASR.

        Returns:
            bool: True se a palavra-chave for detectada, False caso contrário.
        """
        if not self.wake_word:
            return False

        # Converta a string das wakewords em uma lista, se necessário
        if isinstance(self.wake_word, str):
            self.wake_word = self.wake_word.split(',')  # Separa a string em uma lista de palavras

        # Encontre a menor distância entre as palavras no texto e qualquer uma das wake words
        closest_distance = min(
            self.distance(word.lower(), wake_word.lower())
            for word in text.split()
            for wake_word in self.wake_word
        )

        logger.info(f"closest_distance: {closest_distance}")
        return closest_distance <= SIMILARITY_THRESHOLD

    def listen_for_voice(self, timeout=None):
        """
        Inicia a captura de áudio e processa em tempo real para reconhecimento de fala.

        Returns:
            str: Texto reconhecido, caso a palavra-chave seja detectada.
        """
        self.input_stream.start()
        try:
            while True:
                if not self.sample_queue.empty():
                    data, vad_confidence = self.sample_queue.get()

                    # Verifica se a gravação deve começar
                    if not globals.recording_started and vad_confidence > self.dynamic_threshold:
                        globals.recording_started = True
                        self.gap_counter = 0  # Reseta o contador de pausas

                        # Armazena o áudio prévio do buffer
                        pre_record_audio = list(self.buffer)
                        self.samples.extend(pre_record_audio)
                        self.samples.append(data)
                    elif globals.recording_started:
                        self.samples.append(data)

                        if vad_confidence <= self.dynamic_threshold:
                            self.gap_counter += VAD_SIZE
                        else:
                            self.gap_counter = 0  # Reseta o contador de gaps se a confiança subir

                        # Processa o áudio se o contador de gaps exceder o limite de pausa
                        if self.gap_counter > PAUSE_LIMIT:
                            detected_text = self._process_detected_audio()
                            if detected_text:
                                return detected_text
                            else:
                                # Reseta para próxima captura
                                self.reset()
                    else:
                        # Continua monitorando sem gravar
                        pass
                else:
                    # Adiciona um pequeno delay para evitar uso excessivo de CPU
                    time.sleep(0.01)

                # Continua capturando áudio mesmo se estiver esperando
                if globals.recording_started and self.gap_counter <= PAUSE_LIMIT:
                    continue  # Continua capturando áudio
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
            return None
        finally:
            self.shutdown_event.set()
            self.input_stream.stop()
            self.reset()

    def _process_detected_audio(self) -> str | None:
        """
        Processa o áudio detectado e realiza a transcrição do texto.

        Returns:
            str | None: Texto reconhecido ou None se o áudio não for processável.
        """
        logger.info("Processing detected audio...")

        if not self.samples:
            logger.warning("No samples available, skipping processing.")
            return None

        final_audio = np.concatenate(self.samples)
        detected_text = self.asr_model.transcribe(final_audio)

        if detected_text:
            logger.info(f"Detected: '{detected_text}'")
            if self.wake_word and not self.wakeword_detected(detected_text):
                logger.info(f"Wake word '{self.wake_word}' not detected.")
                return None
            else:
                return detected_text
        else:
            logger.info("No text detected.")
            return None

    def reset(self):
        """
        Reseta o estado completo do sistema de reconhecimento de voz.
        """
        globals.recording_started = False
        self.samples.clear()
        self.gap_counter = 0
        self.dynamic_threshold = VAD_THRESHOLD  # Reinicia o threshold dinâmico para o padrão
        self.confidence_deque.clear()
        self.buffer.clear()
        # Limpa a fila de samples
        try:
            while True:
                self.sample_queue.get_nowait()
        except queue.Empty:
            pass


    # Função auxiliar para calcular a distância de Levenshtein
    @staticmethod
    def distance(a: str, b: str) -> int:
        """
        Calcula a distância de Levenshtein entre duas strings.

        Args:
            a (str): Primeira string.
            b (str): Segunda string.

        Returns:
            int: Distância de Levenshtein.
        """
        if len(a) < len(b):
            return VoiceRecognition.distance(b, a)

        if len(b) == 0:
            return len(a)

        previous_row = range(len(b) + 1)
        for i, c1 in enumerate(a):
            current_row = [i + 1]
            for j, c2 in enumerate(b):
                insertions = previous_row[j + 1] + 1  # Inserção
                deletions = current_row[j] + 1       # Deleção
                substitutions = previous_row[j] + (c1 != c2)  # Substituição
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

# Exemplo de uso
if __name__ == "__main__":
    vr = VoiceRecognition(wake_word="assistente")
    transcribed_text = vr.listen_for_voice()  # Ignorando o timeout
    if transcribed_text:
        logger.info(f"Texto transcrito: {transcribed_text}")
    else:
        logger.info("Nenhum texto foi transcrito.")
