class TTSBase:
    @staticmethod
    def get_tts_provider(provider_name):
        if provider_name == 'vits2':
            from .vits2 import Vits2TTS
            return Vits2TTS()
        elif provider_name == 'pipertts':
            from .pipertts import PiperTTS
            piper_exe_path = 'piper\piper.exe'  # Path to piper.exe
            model_path = 'conversations\GLaDOS\pipermodel\glados.onnx'    # Path to the model file
            return PiperTTS(piper_exe_path, model_path)
        elif provider_name == 'mspyttsx3':
            from .mspyttsx3 import Pyttsx3TTS
            return Pyttsx3TTS()
        # Add other TTS providers as needed
        else:
            raise ValueError(f"Unknown TTS provider: {provider_name}")

    def generate_speech(self, text):
        return self.provider.generate_speech(text)
