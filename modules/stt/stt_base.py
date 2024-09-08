class STTBase:
    @staticmethod
    def get_stt_provider(provider_name, model_size=None, device=None, compute_type=None):
        if provider_name == 'google':
            from .google import GoogleSTT
            return GoogleSTT()
        elif provider_name == 'whisper':
            from .whisper import WhisperSTT
            return WhisperSTT(model_size_or_path=model_size, device=device, compute_type=compute_type)
        # Add other STT providers as needed
        else:
            raise ValueError(f"Unknown STT provider: {provider_name}")
        
    def recognize_speech(self, audio):
        return self.provider.recognize_speech(audio)
    
    def listen_for_voice(self, timeout):
        return self.provider.listen_for_voice(timeout)
