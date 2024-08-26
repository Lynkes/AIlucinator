import pyttsx3

class Pyttsx3:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female

    def speak(self, text, clean_queue=True):
        if clean_queue:
            self.engine.stop()  # Clear the playback queue
        self.engine.say(text)
        self.engine.runAndWait()
