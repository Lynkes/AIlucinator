# Projeto de Chatbot AI com Integração de Modelos e Filas

Este projeto implementa um chatbot AI avançado que combina processamento de linguagem natural (NLP), reconhecimento de fala (STT), síntese de fala (TTS), gerenciamento de filas e integração com APIs externas. Além disso, utiliza um banco de dados vetorial para aplicar a técnica de Recuperação-Aumentada por Geração (RAG) em modelos de linguagem (LLMs), proporcionando uma experiência interativa e personalizada.

## Sumário

- [Visão Geral](#visão-geral)
- [Requisitos](#requisitos)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

## Visão Geral

O sistema é composto pelos seguintes componentes principais:

- **`Kokoro`**: Classe para processamento de linguagem natural, reconhecimento de fala (STT) e síntese de fala (TTS).
- **`Queues`**: Gerencia a execução do chatbot, coordenando a interação com a personalidade definida e as filas de mensagens.
- **Banco de Dados Vetorial**: Utiliza a técnica de Recuperação-Aumentada por Geração (RAG) para melhorar as respostas dos modelos de linguagem, armazenando e recuperando informações relevantes para contextos conversacionais.
- **Configuração e Variáveis de Ambiente**: Gerencia variáveis essenciais para a operação do sistema e configura a modularidade para diferentes provedores de recursos.

## Requisitos

- Python 3.7 ou superior
- Bibliotecas Python:
  - `torch`
  - `python-dotenv`
  - `chroma` (para gerenciamento do banco de dados vetorial)
  - Outros requisitos específicos estão listados no `requirements.txt`.

## Configuração do Ambiente

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/usuario/projeto-ai.git
   cd projeto-ai
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Crie um arquivo `.env` com as variáveis de ambiente necessárias:**

   ```env
   PERSONALITY=nome_da_personalidade
   LLMMODEL=modelo_llm
   LLM=provedor_llm
   STT=provedor_stt
   TTS=provedor_tts
   MODEL_SIZE=tamanho_do_modelo
   EMBEDDING_SERVICE=serviço_de_embeddings
   DEBUG=modo_de_debug
   ```

## Estrutura do Projeto

```
Allucinator/
├── main.py               # Ponto de entrada principal do programa
├── conversations/
│   ├── GLaDOS/
│   │   ├── chroma/       # Banco de dados persistente para conversas (RAG)
│   │   ├── filtered_words.txt  # Lista de palavras filtradas
│   │   ├── keyword_map.json    # Mapeamento de palavras-chave
│   ├── GLaDOS.txt        # Template de prompt para a personalidade GLaDOS
├── modules/
│   ├── __init__.py       # Inicializa o pacote modules
│   ├── llm/
│   │   ├── llm_base.py   # Base para integração com modelos de linguagem
│   │   ├── ollama.py     # Integração com o provedor de LLM Ollama
│   │   ├── openai.py     # Integração com o provedor de LLM OpenAI
│   ├── stt/
│   │   ├── google.py     # Integração com o provedor STT Google
│   │   ├── stt_base.py   # Base para integração com provedores de STT
│   │   ├── whisper.py    # Integração com o provedor STT Whisper
│   ├── tts/
│   │   ├── mspyttsx3.py  # Integração com o TTS Microsoft Pyttsx3
│   │   ├── pipertts.py   # Integração com o TTS Piper
│   │   ├── tts_base.py   # Base para integração com provedores de TTS
│   │   ├── vits2.py      # Implementação do TTS VITS2
│   ├── utils/
│   │   ├── audio_utils.py# Funções utilitárias para gerenciamento de áudio
│   │   ├── conversation_utils.py # Funções utilitárias para gerenciamento de conversas
│   │   ├── db_utils.py   # Funções utilitárias para interação com banco de dados
│   │   ├── env_checker.py # Funções para verificação das variáveis de ambiente
│   ├── kokoro.py         # Implementação da classe Kokoro (NLP, STT, TTS)
│   └── queues.py         # Implementação da classe Queues (Gerenciamento de filas)
├── .env                  # Arquivo de configuração das variáveis de ambiente
└── requirements.txt      # Lista de dependências do projeto
```

### `main.py`

Script principal que configura o ambiente, carrega as variáveis de ambiente e inicializa os componentes principais da aplicação.

### `modules/kokoro.py`

Implementa a classe `Kokoro`, responsável por:

- Processamento de linguagem natural
- Reconhecimento de fala (STT)
- Síntese de fala (TTS)

### `modules/queues.py`

Implementa a classe `Queues`, que coordena a execução do chatbot, integrando com a personalidade definida e gerenciando o fluxo de mensagens.

### `modules/utils/env_checker.py`

Função para verificar se as variáveis de ambiente estão configuradas corretamente.

### Banco de Dados Vetorial

- **Chroma**: Utilizado para armazenar e recuperar embeddings de conversas, melhorando a precisão das respostas dos LLMs através da técnica RAG.

## Como Executar

1. **Certifique-se de que o ambiente está configurado corretamente e as dependências estão instaladas.**

2. **Execute o script principal:**

   ```bash
   python main.py
   ```

   O sistema carregará as variáveis de ambiente, configurará os componentes principais e iniciará a execução do chatbot.

## Contribuindo

Contribuições são bem-vindas! Para colaborar, por favor, abra um issue ou envie um pull request com melhorias ou correções. Certifique-se de seguir as diretrizes de contribuição do projeto.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
```

Essa versão do README.md agora inclui informações sobre o banco de dados vetorial e o uso da técnica RAG, além de destacar a modularidade do projeto para integração com diferentes provedores de recursos. Se precisar de mais ajustes ou adicionar outras informações, é só me avisar!
