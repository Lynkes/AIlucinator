class LLMBase:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        """
        Generates a response based on the provided prompt.
        
        :param prompt: The input text to generate a response for.
        :return: The generated response as a string.
        """
        raise NotImplementedError("This method should be overridden in subclasses")
