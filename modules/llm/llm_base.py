class LLMBase:
    """
    Classe base para fornecimento de provedores LLM (Large Language Models).
    Esta classe permite selecionar dinamicamente diferentes provedores de LLM
    com base no nome do provedor.

    Métodos Estáticos:
    -----------------
    get_llm_provider(provider_name, host=None):
        Retorna uma instância do provedor LLM baseado no nome fornecido.
        Parâmetros:
            provider_name (str): Nome do provedor LLM (ex: 'openai', 'ollama').
            host (str, opcional): Endereço do servidor do provedor.
        Retorna:
            Uma instância do provedor LLM correspondente.
        Lança:
            ValueError: Se o provedor LLM for desconhecido.

    Métodos:
    --------
    chat(messages, model):
        Gera uma resposta baseada em uma lista de mensagens e no modelo fornecido.
        Parâmetros:
            messages (list): Lista de mensagens a serem usadas para gerar a resposta.
            model (str): O nome do modelo a ser utilizado para geração.
        Retorna:
            A resposta gerada pelo modelo LLM.

    generate(prompt, model):
        Gera uma resposta baseada no prompt e no modelo fornecido.
        Parâmetros:
            prompt (str): O texto de entrada para gerar a resposta.
            model (str): O nome do modelo a ser utilizado para geração.
        Retorna:
            A resposta gerada pelo modelo LLM.
    """

    @staticmethod
    def get_llm_provider(provider_name, host=None, save_folderpath=None, GOOGLE_API_KEY=None, YOUR_SEARCH_ENGINE_ID=None, OPENWEATHERMAP_API_KEY=None,):
        """
        Método estático que retorna uma instância do provedor LLM com base no nome fornecido.

        Parâmetros:
        -----------
        provider_name (str): Nome do provedor LLM (exemplo: 'openai', 'ollama').
        host (str, opcional): Endereço do servidor do provedor.

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
        elif provider_name == 'INSTRUCT':
            from .instruct_request import INSTRUCT
            return INSTRUCT(host=host)
        elif provider_name == 'AgentINSTRUCT':
            from .instruct_agent import AgentINSTRUCT
            return AgentINSTRUCT(host=host, save_folderpath=save_folderpath, GOOGLE_API_KEY=GOOGLE_API_KEY, YOUR_SEARCH_ENGINE_ID=YOUR_SEARCH_ENGINE_ID, OPENWEATHERMAP_API_KEY=OPENWEATHERMAP_API_KEY,)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    async def chat(self, messages, model):
        """
        Método assíncrono para gerar uma resposta com base em uma lista de mensagens e em um modelo.

        Parâmetros:
        -----------
        messages (list): Lista de mensagens de entrada para o LLM gerar uma resposta.
        model (str): O modelo LLM a ser utilizado para a geração da resposta.

        Retorna:
        --------
        str: Resposta gerada pelo modelo LLM.
        """
        return await self.provider.chat(messages, model)

    async def generate(self, prompt, model):
        """
        Método assíncrono para gerar uma resposta com base em um prompt e em um modelo.

        Parâmetros:
        -----------
        prompt (str): O texto de entrada para o LLM gerar uma resposta.
        model (str): O modelo LLM a ser utilizado para a geração da resposta.

        Retorna:
        --------
        str: Resposta gerada pelo modelo LLM.
        """
        return await self.provider.generate(prompt, model)
