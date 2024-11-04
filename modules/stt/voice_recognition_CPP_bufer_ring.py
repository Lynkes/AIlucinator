import queue
import numpy as np
import sounddevice as sd
from Levenshtein import distance
from loguru import logger
import threading
from pathlib import Path
from typing import Any, List, Tuple
from sounddevice import CallbackFlags
from . import asr
from .vad import VAD
import globals
import time

# Constantes
VAD_MODEL_PATH = "silero_vad.onnx"
SAMPLE_RATE = 16000
VAD_SIZE = 50  # ms
VAD_THRESHOLD = 0.4
BUFFER_SIZE = 40000  # ms
PAUSE_LIMIT = 1300  # ms
SIMILARITY_THRESHOLD = 2 # Levenshtein distance threshold
SMOOTHING_FACTOR = 0.3  # Fator de suavização (0 a 1), menor é mais suave

class VoiceRecognition:
    def __init__(self, model_size_or_path="large-v3", device="cuda", compute_type="float16", wake_word: str | None = None):
        self.wake_word = wake_word
        self.samples: List[np.ndarray] = []
        self.sample_queue: queue.Queue[Tuple[np.ndarray, np.ndarray]] = queue.Queue()
        self.buffer: queue.Queue[np.ndarray] = queue.Queue(maxsize=BUFFER_SIZE // VAD_SIZE)
        globals.recording_started = False
        self.gap_counter = 0
        self.shutdown_event = threading.Event()

        # Variável para VAD_THRESHOLD
        self.dynamic_threshold = VAD_THRESHOLD
        self.confidence_history: List[float] = []

        # Configuração de entrada de áudio
        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000),
        )

        # Inicialização dos modelos
        self.vad_model = VAD(model_path=str(Path.cwd() / "models" / VAD_MODEL_PATH))
        self.asr_model = asr.ASR(model=str(Path.cwd() / "models" / model_size_or_path))

    def audio_callback(self, indata: np.ndarray, frames: int, time: Any, status: CallbackFlags):
        if status:
            logger.warning(f"Audio callback status: {status}")

        data = indata.copy().squeeze()
        vad_confidence = self.vad_model.process_chunk(data)

        # Adiciona a confiança ao histórico
        self.confidence_history.append(vad_confidence)
        if len(self.confidence_history) > 10:
            self.confidence_history.pop(0)

        # Atualiza o limiar dinâmico com base na confiança
        if len(self.confidence_history) > 1:
            if vad_confidence > max(self.confidence_history[-2:]):
                new_threshold = max(vad_confidence - 0.1, 0)
                self.dynamic_threshold = (1 - SMOOTHING_FACTOR) * self.dynamic_threshold + SMOOTHING_FACTOR * new_threshold

        # Adiciona ao buffer
        if not self.buffer.full():
            self.buffer.put(data)
        else:
            self.buffer.get()
            self.buffer.put(data)

        # Captura áudio continuamente
        if vad_confidence > self.dynamic_threshold:
            self.samples.append(data)
            logger.success(f"VAD Confidence: {vad_confidence} (Threshold: {self.dynamic_threshold})")
            self.gap_counter = 0  # Reseta o contador de pausa quando áudio é capturado
        else:
            self.gap_counter += VAD_SIZE  # Aumenta o contador se não houver voz detectada

        self.sample_queue.put((data, vad_confidence))

    def wakeword_detected(self, text: str) -> bool:
        if not self.wake_word:
            return False

        # Converta a string das wakewords em uma lista, se necessário
        if isinstance(self.wake_word, str):
            self.wake_word = self.wake_word.split(',')  # Separa a string em uma lista de palavras

        # Encontre a menor distância entre as palavras no texto e qualquer uma das wake words
        closest_distance = min(
            distance(word.lower(), wake_word.lower())
            for word in text.split()
            for wake_word in self.wake_word
        )

        logger.warning(f"closest_distance: {closest_distance}")
        return closest_distance <= SIMILARITY_THRESHOLD

    def listen_for_voice(self, timeout=None):
        self.input_stream.start()
        try:
            while True:
                if not self.sample_queue.empty():
                    _, vad_confidence = self.sample_queue.get()

                    # Verifica se a gravação deve começar
                    if not globals.recording_started and vad_confidence > self.dynamic_threshold:
                        globals.recording_started = True
                        self.gap_counter = 0  # Reseta o contador de pausas

                    # Se a gravação já começou
                    if globals.recording_started:
                        if vad_confidence <= self.dynamic_threshold:
                            self.gap_counter += VAD_SIZE
                        else:
                            self.gap_counter = 0  # Se a confiança do VAD subir novamente, reseta o contador de gaps

                        # Processa o áudio se o contador de gaps exceder o limite de pausa
                        if self.gap_counter > PAUSE_LIMIT:
                            detected_text = self._process_detected_audio()
                            if detected_text:
                                return detected_text
                else:
                    # Adiciona um pequeno delay para evitar uso excessivo de CPU
                    time.sleep(0.01)

                # Captura áudio continuamente mesmo se estiver esperando
                if globals.recording_started and self.gap_counter <= PAUSE_LIMIT:
                    continue  # Continua capturando áudio
        except queue.Empty:
            logger.warning("No voice detected.")
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
        finally:
            self.shutdown_event.set()
            self.input_stream.stop()
            
    def _process_detected_audio(self) -> str | None:
        logger.info("Processing detected audio...")

        if not self.samples:
            logger.warning("No samples available, skipping processing.")
            return None

        final_audio = np.concatenate(self.samples)
        detected_text = self.asr_model.transcribe(final_audio)

        if detected_text:
            logger.info(f"Detected:'{detected_text}'")
            if self.wake_word and not self.wakeword_detected(detected_text):
                logger.info(f"Wake word '{self.wake_word}' not detected.")
            else:
                self.reset()
                return detected_text

        # Se o áudio foi completamente processado, resetar o estado
        self.reset()

    def reset(self):
        globals.recording_started = False
        self.samples.clear()
        self.gap_counter = 0
        self.dynamic_threshold = VAD_THRESHOLD  # Reinicia o threshold dinâmico para o padrão
        self.confidence_history.clear()
        with self.buffer.mutex:
            self.buffer.queue.clear()
