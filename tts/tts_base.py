class TTSBase:
    def __init__(self):
        pass

    def generate_voice(self, sentence: str, clean_queue: bool = True) -> None:
        """
        Converts the input text into speech.
        
        :param sentence: The text to convert to speech.
        :param clean_queue: Whether to clear the playback queue before speaking.
        """
        raise NotImplementedError("This method should be overridden in subclasses")
