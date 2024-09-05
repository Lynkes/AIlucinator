class STTBase:
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
        
    def recognize_speech(self, audio):
        return self.provider.recognize_speech(audio)
    
    def listen_for_voice(self):
        return self.provider.listen_for_voice()
