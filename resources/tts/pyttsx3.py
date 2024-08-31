import pyttsx3
from .tts_base import TTSBase

class Pyttsx3TTS(TTSBase):
    def __init__(self):
        super().__init__()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)

    def generate_speech(self, text):
        self.engine.say(text)
        self.engine.runAndWait()
