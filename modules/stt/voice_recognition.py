import numpy as np
import queue
import sounddevice as sd
import threading
from typing import Any, List, Tuple
import io
from loguru import logger
from sounddevice import CallbackFlags
from faster_whisper import WhisperModel
from colorama import *
from modules.stt.stt_base import STTBase
from .vad import VAD 
import sys

# Logging setup
logger.remove(0)
logger.add(sys.stderr, level="INFO")

# Constants
SAMPLE_RATE = 16000
VAD_SIZE = 50
VAD_THRESHOLD = 0.9
BUFFER_SIZE = 600
PAUSE_LIMIT = 400
SIMILARITY_THRESHOLD = 2

class VoiceReC(STTBase):
    def __init__(self, model_size_or_path="large-v2", device="cuda", compute_type="float16", wake_word: str | None = None, interruptible: bool = True):
        self.model = WhisperModel(model_size_or_path=model_size_or_path, device=device, compute_type=compute_type)
        self.wake_word = wake_word
        self._vad_model = VAD(model_path="conversations\GLaDOS\pipermodel\silero_vad.onnx")

        # Initialize sample queues and state flags
        self._samples: List[np.ndarray] = []
        self._sample_queue: queue.Queue[Tuple[np.ndarray, np.ndarray]] = queue.Queue()
        self._buffer: queue.Queue[np.ndarray] = queue.Queue(maxsize=BUFFER_SIZE // VAD_SIZE)
        self._recording_started = False
        self._gap_counter = 0

        self.processing = False
        self.currently_speaking = False
        self.interruptible = interruptible
        self.shutdown_event = threading.Event()

        # Initialize audio input stream with callback
        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000),
        )

    def audio_callback(self, indata: np.ndarray, frames: int, time: Any, status: CallbackFlags):
        """
        Callback function for handling real-time audio input.
        """
        data = indata.copy().squeeze()  # Reduce to single channel if necessary
        vad_confidence = self._vad_model.process_chunk(data) > VAD_THRESHOLD
        self._sample_queue.put((data, vad_confidence))

    def listen_for_voice(self, timeout: int | None = 5):
        """
        Continuously listens for voice input, streaming audio for processing.
        """
        self.input_stream.start()
        logger.info("Listening for voice...")

        try:
            while not self.shutdown_event.is_set():
                try:
                    sample, vad_confidence = self._sample_queue.get(timeout=timeout)
                    if sample is not None:
                        return self._handle_audio_sample(sample, vad_confidence)
                except queue.Empty:
                    logger.warning("Timeout while waiting for audio samples")
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
        finally:
            self.shutdown_event.set()
            self.input_stream.stop()

    def _handle_audio_sample(self, sample: np.ndarray, vad_confidence: bool):
        """
        Processes each audio sample as it is received from the callback.
        """
        if not self._recording_started:
            self._manage_pre_activation_buffer(sample, vad_confidence)
        else:
            return self._process_activated_audio(sample, vad_confidence)

    def _manage_pre_activation_buffer(self, sample: np.ndarray, vad_confidence: bool):
        """
        Manages the circular buffer for audio samples before activation.
        """
        if self._buffer.full():
            self._buffer.get()
        self._buffer.put(sample)

        if vad_confidence:
            sd.stop()
            self.processing = False
            self._samples = list(self._buffer.queue)
            self._recording_started = True

    def _process_activated_audio(self, sample: np.ndarray, vad_confidence: bool):
        """
        Processes audio samples after the wake word or activation is detected.
        """
        self._samples.append(sample)
        if not vad_confidence:
            self._gap_counter += 1
            if self._gap_counter >= PAUSE_LIMIT // VAD_SIZE:
                return self._process_detected_audio()
        else:
            self._gap_counter = 0

    def _process_detected_audio(self):
        """
        Finalizes audio processing after speech is detected.
        """
        logger.info("Processing detected audio...")
        self.input_stream.stop()

        audio = np.concatenate(self._samples)
        transcription = self.recognize_speech(audio)
        self.reset()
        self.input_stream.start()
        return transcription

    def recognize_speech(self, audio):
        """
        Uses a model to recognize and transcribe speech from audio.
        """
        response = ""
        audio_data = io.BytesIO(audio.tobytes())
        segments, info = self.model.transcribe(audio_data, vad_filter=True, beam_size=5)

        logger.info(f"Detected language: '{info.language}' with probability {info.language_probability}")

        for segment in segments:
            response += segment.text

        if info.language in ["en", "pt"] and info.language_probability >= 0.6:
            print(f"\nYou said: {response}")
            return response
        else:
            print("\nUnrecognized or false input.")
        return response

    def reset(self):
        """
        Resets state for new recording sessions.
        """
        logger.info("Resetting state for new session...")
        self._recording_started = False
        self._samples.clear()
        self._gap_counter = 0
        with self._buffer.mutex:
            self._buffer.queue.clear()
