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
      # Configuração da API do OpenAI
      OPENAI_API_KEY=  
      # Coloque sua chave da API OpenAI aqui, se aplicável

      # Provedor de Modelos de Linguagem (LLM)
      LLM=INSTRUCT  
      # Escolha entre ollama, openai

      # Provedor de Reconhecimento de Fala (STT)
      STT=voice_recognition_CPP_bufer_ring
      # Escolha entre whisper, google, voice_recognition, voice_recognition_Fwhisper

      # Provedor de Síntese de Fala (TTS)
      TTS=onnxruntimetts  
      # Escolha entre mspyttsx3, vits2, pipertts

      # Modelo de LLM
      LLMMODEL=llama3.2:3b-instruct-q8_0  
      # Escolha entre llama3.1, gpt-3.5-turbo, llava-llama3, llama3.2:3b-instruct-q8_0

      # Modelo de SST 
      MODEL_SIZE=ggml-large-v3-turbo.bin
      # Escolha entre large-v2, large-v1, medium, medium.en, small, small.en, base, base.en, tiny, tiny.en, distil-large-v3

      # Serviço de Embeddings
      EMBEDDING_SERVICE=ollama 
      # Escolha entre huggingface, ollama, openai

      # Nome da Personalidade do Chatbot
      PERSONALITY=GLaDOS  

      # Nome do Usuário (opcional)
      YOUR_NAME=  
      # Coloque seu nome ou o nome do usuário, se necessário

      # Configuração do Modo Debug
      DEBUG=False  
      # Defina como True para ativar o modo debug

      # Caminhos para Arquivos de Conversa, Modelos de Voz e Dados
      # Esses são apenas comentários para referência e não são variáveis de ambiente reais
      #conversations\GLaDOS\GLaDOS.txt
      #conversations\GLaDOS\*.json Arquivos json serão carregados para o banco de dados como se fossem o historico de mensagem quando o limite de 8000 tokens é estourado ou se a conversa é salva e o codigo parado
      #conversations\GLaDOS\PDF\*.PDF Todos PDFs nessa pasta tambem serão carregados ao banco de dados como se fossem memoria,
      #conversations\GLaDOS\chroma
      #conversations\GLaDOS\model\voices
      #conversations\GLaDOS\model\Models_Style-Bert_VITS2_Portal_GLaDOS_v1_config.json
      #conversations\GLaDOS\model\Portal_GLaDOS_v1_e782_s50000.safetensors
      #conversations\GLaDOS\model\style_vectors.npy
      #conversations\GLaDOS\pipermodel\glados.onnx
      #conversations\GLaDOS\pipermodel\glados.onnx.json
      #conversations\GLaDOS\pipermodel\silero_vad.onnx
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