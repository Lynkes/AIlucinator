import queue 
from pathlib import Path
from typing import Any, List, Tuple
from sounddevice import CallbackFlags
import numpy as np
import sounddevice as sd
from Levenshtein import distance
from loguru import logger
import time
import globals
import threading
from faster_whisper import WhisperModel
from modules.utils.conversation_utils import filter_paragraph, load_keyword_map, load_filtered_words
from . import asr
from .vad import VAD

# Constantes
VAD_MODEL_PATH = "silero_vad.onnx"
SAMPLE_RATE = 16000
VAD_SIZE = 50  # ms
VAD_THRESHOLD = 0.2
BUFFER_SIZE = 40000  # ms
PAUSE_LIMIT = 2300  # ms
MIN_SAMPLES = 500  # ms
SIMILARITY_THRESHOLD = 2  # Levenshtein distance threshold
SMOOTHING_FACTOR = 0.3  # Fator de suavização (0 a 1), menor é mais suave

class VoiceRecognition:
    def __init__(self, model_size_or_path="ggml-large-v3-turbo.bin", device="cuda", compute_type="float16", wake_word: str | None = None):
        ASR_MODEL_PATH = model_size_or_path

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
        self.smoothed_threshold = self.dynamic_threshold  # Adicione esta linha

        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000),
        )
        self.vad_model = VAD(model_path=str(Path.cwd() / "models" / VAD_MODEL_PATH))
        self.asr_model = asr.ASR(model=str(Path.cwd() / "models" / ASR_MODEL_PATH))

    def audio_callback(self, indata: np.ndarray, frames: int, time: Any, status: CallbackFlags):
        if status:
            logger.warning(f"Audio callback status: {status}")

        data = indata.copy().squeeze()
        vad_confidence = self.vad_model.process_chunk(data)

        # Adiciona a confiança ao histórico
        self.confidence_history.append(vad_confidence)
        if len(self.confidence_history) > 10:
            self.confidence_history.pop(0)

        # Ajuste dinâmico do VAD_THRESHOLD
        if len(self.confidence_history) > 1 and vad_confidence > max(self.confidence_history[-2:]):
            new_threshold = vad_confidence - 0.1
            # Suavização do limiar dinâmico
            self.smoothed_threshold = (1 - SMOOTHING_FACTOR) * self.smoothed_threshold + SMOOTHING_FACTOR * new_threshold
            self.dynamic_threshold = max(self.dynamic_threshold, self.smoothed_threshold)  # Atualize apenas se necessário

        # Ajuste o áudio ao buffer sem sobreposição
        if not self.buffer.full():
            self.buffer.put(data)
        else:
            self.buffer.get()
            self.buffer.put(data)

        # Processamento dinâmico da confiança do VAD
        if vad_confidence > self.dynamic_threshold:
            self.samples.append(data)
            logger.success(f"VAD Confidence: '{vad_confidence}' (Threshold: {self.dynamic_threshold})")

        # Coloca o dado e a confiança no queue
        self.sample_queue.put((data, vad_confidence))

    def wakeword_detected(self, text: str) -> bool:
        assert self.wake_word is not None, "Wake word should not be None"
        closest_distance = min(distance(word.lower(), self.wake_word) for word in text.split())
        return closest_distance < SIMILARITY_THRESHOLD

    def listen_for_voice(self, timeout=None) -> str:
        self.input_stream.start()
        try:
            while True:
                sample, vad_confidence = self.sample_queue.get()

                if sample is not None:
                    if vad_confidence > self.dynamic_threshold:
                        self.samples.append(sample)
                        logger.success(f"VAD Confidence: '{vad_confidence}'")
                    else:
                        if self.samples:
                            detected_text = self._process_detected_audio()
                            if detected_text:
                                return detected_text
        except queue.Empty:
            logger.warning("No voice detected in the given timeout period")
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
        finally:
            self.shutdown_event.set()
            self.input_stream.stop()

    def _handle_audio_sample(self, sample: np.ndarray, vad_confidence: bool) -> str | None:
        self.samples.append(sample)
        if not globals.recording_started:
            self._manage_pre_activation_buffer(sample, vad_confidence)
        else:
            return self._process_activated_audio(vad_confidence)

    def _manage_pre_activation_buffer(self, sample: np.ndarray, vad_confidence: bool):
        if self.buffer.full():
            self.buffer.get()
        self.buffer.put(sample)

        if vad_confidence:
            globals.processing = False
            self.samples.extend(self.buffer.queue)
            globals.recording_started = True
            self.samples.append(sample)

    def _process_activated_audio(self, vad_confidence: bool) -> str | None:
        if not vad_confidence:
            self.gap_counter += 1
            if self.gap_counter >= PAUSE_LIMIT // VAD_SIZE:
                return self._process_detected_audio()
        else:
            self.gap_counter = 0

    def _process_detected_audio(self) -> str | None:
        logger.info("Processing detected audio...")

        total_samples = len(np.concatenate(self.samples))

        if total_samples < MIN_SAMPLES:
            logger.warning("Input is too short, skipping processing.")
            self.reset()
            return None

        # Não realizar sobreposição no processamento de áudio
        final_audio = np.concatenate(self.samples)

        detected_text = self.asr_model.transcribe(final_audio)

        if detected_text:
            logger.success(f"ASR text: '{detected_text}'")
            if self.wake_word and not self.wakeword_detected(detected_text):
                logger.info(f"Required wake word {self.wake_word=} not detected.")
            else:
                # Apenas reseta se o comprimento total do áudio for maior que PAUSE_LIMIT
                if total_samples >= PAUSE_LIMIT // VAD_SIZE:
                    self.reset()
                globals.processing = True
                globals.currently_speaking = True
                return detected_text

        # Reset será chamado somente se o áudio for suficientemente longo
        if total_samples >= PAUSE_LIMIT // VAD_SIZE:
            self.reset()

    def reset(self):
        logger.info("Resetting recorder...")
        globals.recording_started = False
        self.samples.clear()
        self.gap_counter = 0
        self.dynamic_threshold = VAD_THRESHOLD  # Reset dynamic threshold
        self.confidence_history.clear()
        with self.buffer.mutex:
            self.buffer.queue.clear()
