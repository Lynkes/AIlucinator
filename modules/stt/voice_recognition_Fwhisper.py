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
from modules.utils.conversation_utils import filter_paragraph, load_keyword_map, load_filtered_words 
from .vad import VAD

# Usando pathlib para caminhos independentes de sistema operacional
ASR_MODEL_PATH = "ggml-distil-large-v3.bin"
VAD_MODEL_PATH = "silero_vad.onnx"
SAMPLE_RATE = 16000  # Taxa de amostragem para o stream de entrada
VAD_SIZE = 100  # Milissegundos de amostra para Detecção de Atividade de Voz (VAD)
VAD_THRESHOLD = 0.9  # Limite para detecção VAD
BUFFER_SIZE = 400  # Milissegundos de buffer antes da detecção VAD, padrão 600
PAUSE_LIMIT = 2300  # Milissegundos de pausa permitida antes de processar, padrão 400
PAUSE_TIME = 0.05
WAKE_WORD = "computer"  # Palavra de ativação
SIMILARITY_THRESHOLD = 2  # Limite para a similaridade da palavra de ativação


class VoiceRecognition:
    def __init__(self, model_size_or_path="large-v3", device="cuda", compute_type="float16", wake_word: str | None = None):
        self.model = WhisperModel(model_size_or_path=model_size_or_path, device=device, compute_type=compute_type, download_root="models")
        
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

    def audio_callback(self, indata: np.ndarray, frames: int, time: Any, status: CallbackFlags):
        """
        Callback function for the audio stream, processing incoming data.
        """
        data = indata.copy().squeeze()  # Reduz para um único canal
        vad_confidence = self.vad_model.process_chunk(data)  # O VAD retorna uma probabilidade
        is_voice = vad_confidence > VAD_THRESHOLD

        # Adiciona uma sobreposição no chunk de áudio processado para evitar cortes
        if not self.buffer.full():
            self.buffer.put(data)
        else:
            # Mantém parte do áudio anterior para sobreposição
            old_data = self.buffer.get()
            overlap_data = np.concatenate((old_data[-int(len(old_data) * 0.25):], data))
            self.buffer.put(overlap_data)
        
        self.sample_queue.put((data, is_voice))

    def wakeword_detected(self, text: str) -> bool:
        assert self.wake_word is not None, "Wake word should not be None"
        words = text.split()
        closest_distance = min(
            [distance(word.lower(), self.wake_word,) for word in words]
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
        # Inicia o stream de entrada de áudio
        self.input_stream.start()
        try:
            while True:
                # Obtém um chunk de áudio da fila de samples
                sample, vad_confidence = self.sample_queue.get(timeout=timeout)

                # Verifica se há amostra válida e se a gravação não terminou
                if sample is not None:
                    recognized_text = self._handle_audio_sample(sample, vad_confidence)

                    # Se houver texto reconhecido, retorna
                    if recognized_text:
                        return recognized_text
                else:
                    logger.warning("Timeout while waiting for audio samples")
                    break
        except queue.Empty:
            logger.warning("No voice detected in the given timeout period")
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
        finally:
            # Encerra o stream e sinaliza o shutdown
            self.shutdown_event.set()
            self.input_stream.stop()

    def _handle_audio_sample(self, sample: np.ndarray, vad_confidence: bool):
        if not globals.recording_started:
            self._manage_pre_activation_buffer(sample, vad_confidence)
        else:
            return self._process_activated_audio(sample, vad_confidence)

    def _manage_pre_activation_buffer(self, sample: np.ndarray, vad_confidence: bool):
        """
        Manages the buffer of audio samples before activation (i.e., before the voice is detected).
        """
        # Ajusta o buffer com sobreposição
        if self.buffer.full():
            self.buffer.get()  # Descarta a amostra mais antiga
        self.buffer.put(sample)

        # Ativa a gravação se houver atividade de voz
        if vad_confidence:
            globals.processing = False
            # Inclui o buffer prévio na gravação, usando um pequeno contexto de sobreposição
            self.samples = list(self.buffer.queue)
            globals.recording_started = True
            self.samples.append(sample)

            if not vad_confidence:
                self.gap_counter += 1
                if self.gap_counter >= PAUSE_LIMIT // VAD_SIZE:
                    return self._process_detected_audio()  # Processa o texto após uma pausa
            else:
                self.gap_counter = 0

    def _process_activated_audio(self, sample: np.ndarray, vad_confidence: bool):
        self.samples.append(sample)

        if not vad_confidence:
            self.gap_counter += 1
            if self.gap_counter >= PAUSE_LIMIT // VAD_SIZE:
                return self._process_detected_audio()  # Retorna o texto reconhecido
        else:
            self.gap_counter = 0

    def _process_detected_audio(self):
        """
        Processes the detected audio and returns the recognized text.
        """
        logger.info("Detected pause after speech. Processing...")

        # Combina o áudio capturado com sobreposição
        detected_text = self.asr(self.samples)
        if detected_text:
            logger.success(f"ASR text: '{detected_text}'")
            #filtered=filter_paragraph(paragraph=detected_text,keyword_map=load_keyword_map("conversations\GLaDOS\keyword_map.json"),filtered_words=load_filtered_words("conversations\GLaDOS\\filtered_words.txt"))

            if self.wake_word and not self.wakeword_detected(detected_text):
                logger.info(f"Required wake word {self.wake_word=} not detected.")
            else:
                self.reset()
                globals.processing = True
                globals.currently_speaking = True
                return detected_text

        # Aguarda se o sistema não for interrompível
        if not globals.interruptible:
            while globals.currently_speaking:
                time.sleep(PAUSE_TIME)

        self.reset()

    def asr(self, samples: List[np.ndarray]) -> str:
        audio = np.concatenate(samples)
        detected_text = self.recognize_speech(audio)
        return detected_text
    
    def recognize_speech(self, audio):
        response = []
        segments, info = self.model.transcribe(audio, vad_filter=False, beam_size=5, language=None)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        for segment in segments:
            response.append(segment.text)
            # Retornar conforme o texto é reconhecido
            if len(response) > 0:
                #print(Style.BRIGHT + Fore.YELLOW + "\nYou said: " + Fore.WHITE, response[-1])
                return response[-1]
        return None

    def reset(self):
        logger.info("Resetting recorder...")
        globals.recording_started = False
        self.samples.clear()
        self.gap_counter = 0
        with self.buffer.mutex:
            self.buffer.queue.clear()
