import speech_recognition as sr
from modules.stt.stt_base import STTBase


class GoogleSTT(STTBase):
    
    def recognize_speech(self, audio):
        if audio:
            return self.recognizer.recognize_google_cloud(audio)
        else:
            raise ValueError("Empty audio input")

        