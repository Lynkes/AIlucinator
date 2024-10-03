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
from colorama import *
import io

from .vad import VAD

# Using pathlib for OS-independent paths models
ASR_MODEL_PATH = "ggml-distil-large-v3.bin"
VAD_MODEL_PATH = "silero_vad.onnx"
SAMPLE_RATE = 32000  # Sample rate for input stream
VAD_SIZE = 200  # Milliseconds of sample for Voice Activity Detection (VAD)
VAD_THRESHOLD = 0.7  # Threshold for VAD detection
BUFFER_SIZE = 600  # Milliseconds of buffer before VAD detection default 600
PAUSE_LIMIT = 1000  # Milliseconds of pause allowed before processing default 400
PAUSE_TIME = 0.10
WAKE_WORD = "computer"  # Wake word for activation
SIMILARITY_THRESHOLD = 2  # Threshold for wake word similarity


class VoiceRecognition:
    def __init__(self, model_size_or_path="large-v2", device="cuda", compute_type="float16", wake_word: str | None = None):
        """
        Initializes the VoiceRecognition class, setting up necessary models, streams, and queues.
        """
        self.model = WhisperModel(model_size_or_path=model_size_or_path, device=device, compute_type=compute_type, download_root="models")


        self.wake_word = wake_word
        # Initialize sample queues and state flags
        # Initialize sample queues and state flags
        self.samples: List[np.ndarray] = []
        self.sample_queue: queue.Queue[Tuple[np.ndarray, np.ndarray]] = queue.Queue()
        self.buffer: queue.Queue[np.ndarray] = queue.Queue(maxsize=BUFFER_SIZE // VAD_SIZE)
        globals.recording_started = False
        self.gap_counter = 0

        processing = False
        currently_speaking = False

        self.shutdown_event = threading.Event()

        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000),
        )
        self.vad_model = VAD(model_path=str(Path.cwd() / "models" / VAD_MODEL_PATH))
        

    def audio_callback(self, indata: np.ndarray, frames: int, time: Any, status: CallbackFlags):
        """
        Callback function for the audio stream, processing incoming data.
        """
        data = indata.copy()
        data = data.squeeze()  # Reduce to single channel if necessary
        vad_confidence = self.vad_model.process_chunk(data) > VAD_THRESHOLD
        self.sample_queue.put((data, vad_confidence))

    def wakeword_detected(self, text: str) -> bool:
        """
        Calculates the nearest Levenshtein distance from the detected text to the wake word.

        This is used as 'Glados' is not a common word, and Whisper can sometimes mishear it.
        """
        assert self.wake_word is not None, "Wake word should not be None"

        words = text.split()
        closest_distance = min(
            [distance(word.lower(), self.wake_word) for word in words]
        )
        return closest_distance < SIMILARITY_THRESHOLD

    def listen_for_voice(self, timeout=None):
        """
        Starts listening for voice input and returns the recognized text.
        
        Args:
            timeout (int, optional): Time in seconds to wait for voice input. If None, listens indefinitely.

        Returns:
            str: Recognized speech text.
        """
        
        self.input_stream.start()
        try:
            sample, vad_confidence = self.sample_queue.get()
            if sample is not None:
                return self._handle_audio_sample(sample, vad_confidence)
            logger.warning("Timeout while waiting for audio samples")
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
        finally:
            self.shutdown_event.set()
            self.input_stream.stop()

    def _handle_audio_sample(self, sample: np.ndarray, vad_confidence: bool):
        """
        Handles the processing of each audio sample and returns recognized text if available.
        """
        if not globals.recording_started:
            self._manage_pre_activation_buffer(sample, vad_confidence)
        else:
            return self._process_activated_audio(sample, vad_confidence)

    def _manage_pre_activation_buffer(self, sample: np.ndarray, vad_confidence: bool):
        """
        Manages the buffer of audio samples before activation (i.e., before the voice is detected).
        """
        if self.buffer.full():
            self.buffer.get()  # Discard the oldest sample to make room for new ones
        self.buffer.put(sample)

        if vad_confidence:  # Voice activity detected
            globals.processing = False
            self.samples = list(self.buffer.queue)
            globals.recording_started = True

    def _process_activated_audio(self, sample: np.ndarray, vad_confidence: bool):
        """
        Processes audio samples after activation and returns recognized text.
        """
        self.samples.append(sample)

        if not vad_confidence:
            self.gap_counter += 1
            if self.gap_counter >= PAUSE_LIMIT // VAD_SIZE:
                return self._process_detected_audio()  # Return the recognized text
        else:
            self.gap_counter = 0

    def _process_detected_audio(self):
        """
        Processes the detected audio and returns the recognized text.
        """
        logger.info("Detected pause after speech. Processing...")
        self.input_stream.stop()

        detected_text = self.asr(self.samples)
        if detected_text:
            logger.success(f"ASR text: '{detected_text}'")

            if self.wake_word and not self.wakeword_detected(detected_text):
                logger.info(f"Required wake word {self.wake_word=} not detected.")
            else:
                self.reset()
                self.input_stream.start()
                globals.processing = True
                globals.currently_speaking = True
                return detected_text

        if not globals.interruptible:
            while globals.currently_speaking:
                time.sleep(PAUSE_TIME)

        self.reset()

    def asr(self, samples: List[np.ndarray]) -> str:
        """
        Performs automatic speech recognition on the collected samples.
        
        Args:
            samples (List[np.ndarray]): List of audio samples.

        Returns:
            str: Recognized speech text.
        """
        audio = np.concatenate(samples)
        detected_text = self.recognize_speech(audio)
        return detected_text
    
    def recognize_speech(self, audio):
        response = ""
        #audio_data = io.BytesIO(audio.get_wav_data())
        segments, info = self.model.transcribe(audio, vad_filter=False, beam_size=5, language=None)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        for segment in segments:
            response += segment.text
        if "en" in info.language or "pt" in info.language:
            if info.language_probability >= 0.7:
                print(Style.BRIGHT + Fore.YELLOW + "\nYou said: " + Fore.WHITE, response)  # Checking
                return response
        else:
            print(Style.BRIGHT + Fore.RED + "\nFalse input?")
            print(Style.BRIGHT + Fore.YELLOW + "\nYou said?: " + Fore.WHITE, response)
        return None

    def reset(self):
        """
        Resets the recording state and clears buffers.
        """
        logger.info("Resetting recorder...")
        globals.recording_started = False
        self.samples.clear()
        self.gap_counter = 0
        with self.buffer.mutex:
            self.buffer.queue.clear()


if __name__ == "__main__":
    demo = VoiceRecognition(wake_word=WAKE_WORD)
    demo.start()
