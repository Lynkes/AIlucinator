from dotenv import load_dotenv
import speech_recognition as sr
import os

class STTBase:
    def __init__(self):
        load_dotenv()
        provider_name = os.getenv('STT')
        self.provider = self.get_stt_provider(provider_name)
        self.r = sr.Recognizer()
        self.r.dynamic_energy_threshold = False
        self.r.energy_threshold = 150  # 300 is the default value of the SR library
        self.mic = sr.Microphone(device_index=0)

    @staticmethod
    def get_stt_provider(provider_name):
        if provider_name == 'google':
            from .google import GoogleSTT
            return GoogleSTT()
        elif provider_name == 'whisper':
            from .whisper import WhisperSTT
            return WhisperSTT()
        # Add other STT providers as needed
        else:
            raise ValueError(f"Unknown STT provider: {provider_name}")
        

    def listen_for_voice(self, timeout: int | None = 5):
        with self.mic as source:
            print("\nListening...")
            self.r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.r.listen(source, timeout)
                print("No longer listening")
                return audio
            except sr.WaitTimeoutError:
                print("Listening timed out")
            except Exception as e:
                print(f"An error occurred while listening: {e}")
            return None

    def recognize_speech(self, audio):
        return self.provider.recognize_speech(audio)
