class TTSBase:
    """
    Classe base para fornecer provedores de TTS (Text-to-Speech).
    Esta classe permite a seleção dinâmica de diferentes provedores de TTS
    com base no nome do provedor.

    Métodos Estáticos:
    -----------------
    get_tts_provider(provider_name):
        Retorna uma instância do provedor TTS baseado no nome fornecido.
        Parâmetros:
            provider_name (str): Nome do provedor TTS (ex: 'vits2', 'pipertts', 'mspyttsx3').
        Retorna:
            Uma instância do provedor TTS correspondente.
        Lança:
            ValueError: Se o provedor TTS for desconhecido.

    Métodos:
    --------
    generate_speech(text, temp_filename):
        Gera a fala a partir de um texto e salva o resultado em um arquivo temporário.
        Parâmetros:
            text (str): O texto de entrada para a geração da fala.
            temp_filename (str): O nome do arquivo temporário onde a fala será salva.
        Retorna:
            O caminho do arquivo com o áudio gerado.
    """

    @staticmethod
    def get_tts_provider(provider_name):
        """
        Método estático que retorna uma instância do provedor de TTS com base no nome fornecido.

        Parâmetros:
        -----------
        provider_name (str): Nome do provedor TTS (exemplo: 'vits2', 'pipertts', 'mspyttsx3').

        Retorna:
        --------
        Instância do provedor TTS correspondente ao nome do provedor.

        Exceções:
        ---------
        ValueError: Se o provedor TTS for desconhecido.
        """
        if provider_name == 'vits2':
            from .vits2 import Vits2TTS
            return Vits2TTS()
        elif provider_name == 'pipertts':
            from .pipertts import PiperTTS
            piper_exe_path = 'python-embedded\\piper\\piper.exe'  # Caminho para o executável do Piper
            model_path = 'conversations\\GLaDOS\\pipermodel\\glados.onnx'  # Caminho para o arquivo do modelo
            return PiperTTS(piper_exe_path, model_path)
        elif provider_name == 'mspyttsx3':
            from .mspyttsx3 import Pyttsx3TTS
            return Pyttsx3TTS()
        elif provider_name == 'onnxruntimetts':
            from .onnxruntimetts import OnnxTTS
            return OnnxTTS(model_path='conversations\\GLaDOS\\pipermodel\\glados.onnx', use_cuda=False, speaker_id=0)
        else:
            raise ValueError(f"Unknown TTS provider: {provider_name}")

    def generate_speech(self, text, temp_filename):
        """
        Método para gerar fala a partir de texto.

        Parâmetros:
        -----------
        text (str): O texto de entrada para o TTS gerar a fala.
        temp_filename (str): O nome do arquivo temporário onde a fala será salva.

        Retorna:
        --------
        Caminho do arquivo de áudio gerado.
        """
        return self.provider.generate_speech(text, temp_filename)
