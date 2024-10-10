class STTBase:
    """
    Classe base para fornecimento de provedores de STT (Speech-to-Text).
    Esta classe permite selecionar dinamicamente diferentes provedores de STT
    com base no nome do provedor e nos parâmetros do modelo.

    Métodos Estáticos:
    -----------------
    get_stt_provider(provider_name, model_size=None, device=None, compute_type=None):
        Retorna uma instância do provedor STT baseado no nome fornecido.
        Parâmetros:
            provider_name (str): Nome do provedor STT (ex: 'google', 'whisper').
            model_size (str, opcional): Tamanho do modelo para provedores como Whisper.
            device (str, opcional): Dispositivo no qual o modelo será executado (ex: 'cuda', 'cpu').
            compute_type (str, opcional): Tipo de computação para o modelo (ex: 'float16', 'int8').
        Retorna:
            Uma instância do provedor STT correspondente.
        Lança:
            ValueError: Se o provedor STT for desconhecido.

    Métodos:
    --------
    recognize_speech(audio):
        Realiza o reconhecimento de fala a partir de um arquivo de áudio.
        Parâmetros:
            audio: O áudio de entrada a ser reconhecido.
        Retorna:
            Texto reconhecido a partir do áudio.

    listen_for_voice(timeout):
        Escuta o áudio de entrada e processa a fala dentro de um limite de tempo.
        Parâmetros:
            timeout (int): Tempo limite para escutar a entrada de voz.
        Retorna:
            Dados de áudio capturados dentro do tempo limite.
    """

    @staticmethod
    def get_stt_provider(provider_name, model_size=None, device=None, compute_type=None, wake_word=None):
        """
        Método estático que retorna uma instância do provedor STT com base no nome fornecido.

        Parâmetros:
        -----------
        provider_name (str): Nome do provedor STT (exemplo: 'google', 'whisper', 'voice_recognition').
        model_size (str, opcional): Tamanho do modelo para provedores que suportam esse parâmetro.
        device (str, opcional): Dispositivo no qual o modelo será executado (exemplo: 'cuda', 'cpu').
        compute_type (str, opcional): Tipo de computação para o modelo (exemplo: 'float16', 'int8').

        Retorna:
        --------
        Instância do provedor STT correspondente ao nome do provedor.

        Exceções:
        ---------
        ValueError: Se o provedor STT for desconhecido.
        """
        if provider_name == 'google':
            from .google import GoogleSTT
            return GoogleSTT()
        elif provider_name == 'whisper':
            from .whisper import WhisperSTT
            return WhisperSTT(model_size_or_path=model_size, device=device, compute_type=compute_type) 
        elif provider_name == 'voice_recognition':
            from .voice_recognition import VoiceRecognition
            return VoiceRecognition(model_size_or_path=model_size, device=device, compute_type=compute_type, wake_word=wake_word)
        elif provider_name == 'voice_recognition_Fwhisper': 
            from .voice_recognition_Fwhisper import VoiceRecognition
            return VoiceRecognition(model_size_or_path=model_size, device=device, compute_type=compute_type, wake_word=wake_word)
        elif provider_name == 'voice_recognition_CPP_bufer_ring':
            from .voice_recognition_CPP_bufer_ring import VoiceRecognition
            return VoiceRecognition(model_size_or_path=model_size, device=device, compute_type=compute_type, wake_word=wake_word)
        else:
            raise ValueError(f"Unknown STT provider: {provider_name}")
        
    def recognize_speech(self, audio):
        """
        Método para realizar o reconhecimento de fala a partir de um arquivo de áudio.

        Parâmetros:
        -----------
        audio: O áudio de entrada a ser reconhecido.

        Retorna:
        --------
        Texto reconhecido a partir do áudio.
        """
        return self.provider.recognize_speech(audio)
    
    def listen_for_voice(self, timeout):
        """
        Método para escutar áudio de entrada e processar a fala dentro de um limite de tempo.

        Parâmetros:
        -----------
        timeout (int): Tempo limite (em segundos) para escutar a entrada de voz.

        Retorna:
        --------
        Dados de áudio capturados dentro do tempo limite.
        """
        return self.provider.listen_for_voice(timeout)
