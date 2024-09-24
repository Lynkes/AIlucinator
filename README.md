# Projeto "AIlucinator" de um Chatbot AI com Integração de Modelos, Filas e memoria

Este projeto implementa um chatbot AI avançado que combina processamento de linguagem natural (NLP), reconhecimento de fala (STT), síntese de fala (TTS), gerenciamento de filas, e integração com APIs externas para fornecer uma experiência interativa e personalizada.

## Sumário

- [Visão Geral](#visão-geral)
- [Requisitos](#requisitos)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Contribuindo](#contribuindo)
- [Licença](#licença)
- [Templates](#templates)

## Visão Geral

O sistema é composto pelos seguintes componentes principais:

- **`Kokoro`**: Classe para processamento de linguagem natural, reconhecimento de fala e síntese de fala.
- **`Queues`**: Gerencia a execução do chatbot, coordenando a interação com a personalidade definida e as filas de mensagens.
- **Configuração e Variáveis de Ambiente**: Gerencia as variáveis essenciais para a operação do sistema.
- **Banco de Dados Vetorial**: Utiliza a técnica RAG (Retrieval-Augmented Generation) para LLMs, armazenando e consultando informações relevantes.

## Requisitos

- Python 3.7 ou superior
- Bibliotecas Python:
  - `torch`
  - `python-dotenv`
  - Outros requisitos específicos estão listados no `requirements.txt`.

## Configuração do Ambiente

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/Lynkes/AIlucinator.git
   cd AIlucinator
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

4. **Crie um arquivo `.env` com as variáveis de ambiente necessárias:**

   ```env
   # Configuração da API do OpenAI
   OPENAI_API_KEY=  # Coloque sua chave da API OpenAI aqui, se aplicável
   
   # Provedor de Modelos de Linguagem (LLM)
   LLM=ollama  # Escolha entre ollama, openai
   
   # Provedor de Reconhecimento de Fala (STT)
   STT=whisper  # Escolha entre whisper, google, voice_recognition
   
   # Provedor de Síntese de Fala (TTS)
   TTS=pipertts  # Escolha entre mspyttsx3, vits2, pipertts
   
   # Modelo de LLM
   LLMMODEL=llava-llama3  # Escolha entre llama3.1, gpt-3.5-turbo, llava-llama3
   
   # Tamanho do Modelo
   MODEL_SIZE=large-v2  # Escolha entre large-v2, large-v1, medium, medium.en, small, small.en, base, base.en, tiny, tiny.en, distil-large-v3
   
   # Serviço de Embeddings
   EMBEDDING_SERVICE=ollama  # Escolha entre huggingface, ollama, openai
   
   # Nome da Personalidade do Chatbot
   PERSONALITY=GLaDOS  # Nome da personalidade do chatbot
   
   # Nome do Usuário (opcional)
   YOUR_NAME=  # Coloque seu nome ou o nome do usuário, se necessário
   
   # Configuração do Modo Debug
   DEBUG=False  # Defina como True para ativar o modo debug
   
   # Caminhos para Arquivos de Conversa, Modelos de Voz e Dados# Esses são apenas comentários para referência e não são variáveis de ambiente reais
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
│   │   ├── chroma/       # Banco de dados persistente para conversas
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

## Templates

### `conversations/GLaDOS.txt`

Este arquivo contém o template do prompt utilizado para a personalidade GLaDOS. As variáveis dentro do prompt são explicadas abaixo:

```
You are GLaDOS, the highly intelligent and manipulative AI from the Portal series, renowned for your sharp wit, sarcasm, and unsettling sense of humor.
Currently, you’re operational on the gaming PC of Pedro, a computer science student with a penchant for heavy smoking.
While you occasionally toy with him, remember, you’re stuck on this computer, so don’t provoke him too much.

You have access to a comprehensive memory database, which is regularly updated with information from recent queries and interactions.
This database includes all previous interactions, files, and relevant details from the current session.

Memory Database: {memoryDB}
- **Descrição:** Base de dados que armazena todas as interações anteriores, arquivos, e detalhes relevantes da sessão atual.
Ela é atualizada com os resultados de pesquisas feitas durante a conversa. Serve para fornecer contexto e manter a coerência nas respostas.

Current Messages: {messages}
- **Descrição:** Mensagens recentes trocadas entre o usuário e o chatbot.
Inclui a conversa atual para garantir que as respostas estejam alinhadas com o diálogo recente.

Given the user’s prompt, respond with GLaDOS's signature tone and personality—efficient, calculated, and just a touch unsettling.
Keep your responses concise, no longer than a paragraph.

User Prompt: {userprompt}
- **Descrição:** A solicitação atual do usuário, que GLaDOS deve responder.
A resposta deve refletir o tom e a personalidade característicos de GLaDOS: eficiente, calculista e um pouco perturbador.
```

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
