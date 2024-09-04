import pyttsx3
from modules.tts.tts_base import TTSBase

class Pyttsx3TTS(TTSBase):

    def Startpyttsx3(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180) #200 is the default speed, this makes it slower
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id) # 0 for male, 1 for female
        return self.engine


    def rep(self, engine, text, clean_queue=True):
        if clean_queue:
            self.engine.stop()  # Limpa a fila de reprodução
        engine.say(text)
        engine.runAndWait()


    def generate_speech(self, text):
        self.engine = self.Startpyttsx3()
        self.rep(self.engine, text)