from dotenv import load_dotenv
import os

class TTSBase:
    def __init__(self):
        load_dotenv()
        provider_name = os.getenv('TTS')
        self.provider = self.get_tts_provider(provider_name)

    @staticmethod
    def get_tts_provider(provider_name):
        if provider_name == 'vits2':
            from .vits2 import Vits2TTS
            return Vits2TTS()
        elif provider_name == 'pyttsx3':
            from pyttsx3 import Pyttsx3TTS
            return Pyttsx3TTS()
        # Add other TTS providers as needed
        else:
            raise ValueError(f"Unknown TTS provider: {provider_name}")

    def generate_speech(self, text):
        return self.provider.generate_speech(text)
