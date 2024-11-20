import speech_recognition as sr
from modules.stt.stt_base import STTBase


class GoogleSTT(STTBase):
    def __init__(self,):
        self.r = sr.Recognizer()
        self.r.dynamic_energy_threshold = False
        self.r.energy_threshold = 150  # 300 is the default value of the SR library
        self.mic = sr.Microphone(device_index=0)
    
    def recognize_speech(self, audio):
        if audio:
            return self.r.recognize_google_cloud(audio)
        else:
            raise ValueError("Empty audio input")

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