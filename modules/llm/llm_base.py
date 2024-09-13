class LLMBase:
    """
    Classe base para fornecimento de provedores LLM (Large Language Models).
    Esta classe permite selecionar dinamicamente diferentes provedores de LLM
    com base no nome do provedor.

    Métodos Estáticos:
    -----------------
    get_llm_provider(provider_name):
        Retorna uma instância do provedor LLM baseado no nome fornecido.
        Parâmetros:
            provider_name (str): Nome do provedor LLM (ex: 'openai', 'ollama').
        Retorna:
            Uma instância do provedor LLM correspondente.
        Lança:
            ValueError: Se o provedor LLM for desconhecido.

    Métodos:
    --------
    generate_response(prompt, model):
        Gera uma resposta baseada no prompt e no modelo fornecidos.
        Parâmetros:
            prompt (str): O texto de entrada para gerar a resposta.
            model (str): O nome do modelo a ser utilizado para geração.
        Retorna:
            A resposta gerada pelo modelo LLM.
    """

    @staticmethod
    def get_llm_provider(provider_name):
        """
        Método estático que retorna uma instância do provedor LLM com base no nome fornecido.

        Parâmetros:
        -----------
        provider_name (str): Nome do provedor LLM (exemplo: 'openai', 'ollama').

        Retorna:
        --------
        Instância do provedor LLM correspondente ao nome do provedor.

        Exceções:
        ---------
        ValueError: Se o provedor LLM for desconhecido.
        """
        if provider_name == 'openai':
            from .openai import OpenAILLM
            return OpenAILLM()
        elif provider_name == 'ollama':
            from .ollama import OllamaLLM
            return OllamaLLM()
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    def generate_response(self, prompt, model):
        """
        Método para gerar uma resposta com base em um prompt e em um modelo.

        Parâmetros:
        -----------
        prompt (str): O texto de entrada para o LLM gerar uma resposta.
        model (str): O modelo LLM a ser utilizado para a geração da resposta.

        Retorna:
        --------
        Resposta gerada pelo modelo LLM.
        """
        return self.provider.generate_response(prompt, model)
