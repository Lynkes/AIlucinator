from tts.tts_base import TTSBase
import pyttsx3

class Pyttsx3Provider(TTSBase):
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)

    def generate_voice(self, sentence, clean_queue=True):
        if clean_queue:
            self.engine.stop()  # Clear the playback queue
        self.engine.say(sentence)
        self.engine.runAndWait()
