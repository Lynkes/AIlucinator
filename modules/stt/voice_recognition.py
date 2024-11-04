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
VAD_THRESHOLD = 0.9
BUFFER_SIZE = 400  # ms
PAUSE_LIMIT = 2300  # ms
PAUSE_TIME = 0.05
WAKE_WORD = "computer"
SIMILARITY_THRESHOLD = 2  # Levenshtein distance threshold

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

        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000),
        )
        self.vad_model = VAD(model_path=str(Path.cwd() / "models" / VAD_MODEL_PATH))
        self.asr_model = asr.ASR(model=str(Path.cwd() / "models" / ASR_MODEL_PATH))

    def audio_callback(self, indata: np.ndarray, frames: int, time: Any, status: CallbackFlags):
        data = indata.copy().squeeze()
        vad_confidence = self.vad_model.process_chunk(data)

        if not self.buffer.full():
            self.buffer.put(data)
        else:
            old_data = self.buffer.get()
            overlap_data = np.concatenate((old_data[-int(len(old_data) * 0.25):], data))
            self.buffer.put(overlap_data)

        self.sample_queue.put((data, vad_confidence > VAD_THRESHOLD))

    def wakeword_detected(self, text: str) -> bool:
        assert self.wake_word is not None, "Wake word should not be None"
        closest_distance = min(distance(word.lower(), self.wake_word) for word in text.split())
        return closest_distance < SIMILARITY_THRESHOLD

    def listen_for_voice(self, timeout=None) -> str:
        self.input_stream.start()
        try:
            while True:
                sample, vad_confidence = self.sample_queue.get(timeout=timeout)
                if sample is not None:
                    recognized_text = self._handle_audio_sample(sample, vad_confidence)
                    if recognized_text:
                        return recognized_text
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
        logger.info("Detected pause after speech. Processing...")
        detected_text = self.asr_model.transcribe(np.concatenate(self.samples))
        if detected_text:
            logger.success(f"ASR text: '{detected_text}'")
            if self.wake_word and not self.wakeword_detected(detected_text):
                logger.info(f"Required wake word {self.wake_word=} not detected.")
            else:
                self.reset()
                globals.processing = True
                globals.currently_speaking = True
                return detected_text

        if not globals.interruptible:
            while globals.currently_speaking:
                time.sleep(PAUSE_TIME)

        self.reset()

    def reset(self):
        logger.info("Resetting recorder...")
        globals.recording_started = False
        self.samples.clear()
        self.gap_counter = 0
        with self.buffer.mutex:
            self.buffer.queue.clear()
