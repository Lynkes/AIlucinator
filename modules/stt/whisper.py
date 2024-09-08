from modules.stt.stt_base import STTBase
from faster_whisper import WhisperModel
from colorama import *
import speech_recognition as sr
import io

class WhisperSTT(STTBase):
    def __init__(self, model_size_or_path="large-v2", device="cuda", compute_type="float16"):
        self.r = sr.Recognizer()
        self.r.dynamic_energy_threshold = False
        self.r.energy_threshold = 150  # 300 is the default value of the SR library
        self.mic = sr.Microphone(device_index=0)
        self.model = WhisperModel(model_size_or_path=model_size_or_path, device=device, compute_type=compute_type, download_root="whisper-model")

    def recognize_speech(self, audio):
        response = ""
        audio_data = io.BytesIO(audio.get_wav_data())
        segments, info = self.model.transcribe(audio_data, vad_filter=True, beam_size=5)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        for segment in segments:
            response += segment.text
        if "en" in info.language or "pt" in info.language and info.language_probability >= 0.75:
            print(Style.BRIGHT + Fore.YELLOW + "\nYou said: " + Fore.WHITE, response)  # Checking
            return response
        else:
            print(Style.BRIGHT + Fore.RED + "\nFalse input?")
        return response, info.language, info.language_probability

    def listen_for_voice(self, timeout: int | None = 5):
        with self.mic as source:
            self.r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.r.listen(source, timeout)
                return audio
            except sr.WaitTimeoutError:
                print("Listening timed out")
            except Exception as e:
                print(f"An error occurred while listening: {e}")
            return None