class STTBase:
    def __init__(self):
        pass

    def recognize_speech(self, audio) -> tuple[str, str, float]:
        """
        Recognizes and transcribes speech from the given audio input.
        
        :param audio: The audio input containing speech to transcribe.
        :return: A tuple containing the transcribed text, detected language, and language probability.
        """
        raise NotImplementedError("This method should be overridden in subclasses")
