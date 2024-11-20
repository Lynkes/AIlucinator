# Projeto "AIlucinator" - Chatbot AI com Integração de Modelos, Filas e Memória

Este projeto implementa um chatbot AI avançado que combina processamento de linguagem natural (NLP), reconhecimento de fala (STT), síntese de fala (TTS), gerenciamento de filas e integração com APIs externas para fornecer uma experiência interativa e personalizada.

## Sumário

- [Visão Geral](#visão-geral)
- [Requisitos](#requisitos)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Templates](#templates)
- [Como Executar](#como-executar)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

## Visão Geral

O sistema é composto pelos seguintes componentes principais:

- **`Kokoro`**: Classe para processamento de linguagem natural, reconhecimento de fala e síntese de fala.
- **`Queues`**: Gerencia a execução do chatbot, coordenando a interação com a personalidade definida e as filas de mensagens.
- **Configuração e Variáveis de Ambiente**: Gerencia as variáveis essenciais para a operação do sistema.
- **Banco de Dados Vetorial**: Utiliza a técnica RAG (Retrieval-Augmented Generation) para LLMs, armazenando e consultando informações relevantes.

## Requisitos

- **Python 3.7** ou superior
- **Bibliotecas Python**:
  - `torch`
  - `python-dotenv`
  - Outros requisitos específicos estão listados no `requirements.txt`
- **Dependências Adicionais**:
  - **Whisper.cpp**: [Baixar](https://github.com/ggerganov/whisper.cpp/releases/download/v1.6.0/whisper-cublas-12.2.0-bin-x64.zip)
  - **Modelo Whisper ggml-large-v3.bin**: [Baixar](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin)
  - **Ollama**: [Baixar](https://ollama.com/download/OllamaSetup.exe)
    - Após a instalação, execute os comandos:
      ```bash
      ollama pull nomic-embed-text
      ollama pull llama3.2
      ```

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
   OPENAI_API_KEY=
   # Coloque sua chave da API OpenAI aqui, se aplicável

   # Provedor de Modelos de Linguagem (LLM)
   # Host para Ollama utilizando INSTRUCT e AgentINSTRUCT
   HOST=127.0.0.1

   # Escolha entre ollama, openai, INSTRUCT, AgentINSTRUCT
   LLM=AgentINSTRUCT

   # Provedor de Reconhecimento de Fala (STT)
   # Escolha entre whisper, google, voice_recognition, voice_recognition_Fwhisper, ars_vad_wcpp
   STT=ars_vad_wcpp

   # Provedor de Síntese de Fala (TTS)
   # Escolha entre mspyttsx3, vits2, pipertts, onnxruntimetts, F5TTS
   TTS=F5TTS

   # Modelo de LLM
   # Escolha entre llama3.1, gpt-3.5-turbo, llava-llama3, llama3.2:3b-instruct-q8_0
   LLMMODEL=llama3.2

   # Modelo de STT para Whisper, FasterWhisper ou Whispercpp
   # Escolha entre large-v2, large-v1, medium, medium.en, small, small.en, base, base.en, tiny, tiny.en, distil-large-v3
   MODEL_SIZE=ggml-large-v3.bin

   # Serviço de Embeddings
   # Escolha entre huggingface, ollama, openai
   EMBEDDING_SERVICE=ollama

   # Nome da Personalidade do Chatbot e seu diretório
   PERSONALITY=Ryan

   # Modelo de TTS para pipertts ou onnxruntimetts (ex.: glados.onnx, en_US-ryan-high.onnx, pt_BR-faber-medium.onnx)
   TTS_MODEL=pt_BR-faber-medium.onnx

   # Palavras usadas para ativar o personagem
   WAKE_WORD=Ryan

   # Nome do Usuário (opcional)
   YOUR_NAME=

   # Chaves de API
   GOOGLE_API_KEY=""
   YOUR_SEARCH_ENGINE_ID=""
   OPENWEATHERMAP_API_KEY=""

   # Configuração do Modo Debug
   # Defina como True para ativar o modo debug
   DEBUG=False

   # Caminhos para Arquivos de Conversa, Modelos de Voz e Dados (apenas para referência)
   # conversations\GLaDOS\GLaDOS.txt
   # conversations\GLaDOS\PDF\*.PDF - Todos os PDFs nessa pasta também serão carregados como memória
   # conversations\GLaDOS\chroma
   # conversations\GLaDOS\model\voices
   # conversations\GLaDOS\model\Models_Style-Bert_VITS2_Portal_GLaDOS_v1_config.json
   # conversations\GLaDOS\model\Portal_GLaDOS_v1_e782_s50000.safetensors
   # conversations\GLaDOS\model\style_vectors.npy
   # conversations\GLaDOS\pipermodel\glados.onnx
   # conversations\GLaDOS\pipermodel\glados.onnx.json
   # conversations\GLaDOS\pipermodel\silero_vad.onnx
   ```

## Estrutura do Projeto

```
AIlucinator/
├── main.py               # Ponto de entrada principal do programa
├── conversations/
│   ├── GLaDOS/
│   │   ├── chroma/                # Banco de dados persistente para conversas
│   │   ├── filtered_words.txt     # Lista de palavras filtradas
│   │   ├── keyword_map.json       # Mapeamento de palavras-chave
│   └── GLaDOS.txt                 # Template de prompt para a personalidade GLaDOS
├── modules/
│   ├── __init__.py                # Inicializa o pacote modules
│   ├── llm/
│   │   ├── llm_base.py            # Base para integração com modelos de linguagem
│   │   ├── ollama.py              # Integração com o provedor de LLM Ollama
│   │   └── openai.py              # Integração com o provedor de LLM OpenAI
│   ├── stt/
│   │   ├── stt_base.py            # Base para integração com provedores de STT
│   │   ├── whisper.py             # Integração com o provedor STT Whisper
│   │   └── google.py              # Integração com o provedor STT Google
│   ├── tts/
│   │   ├── tts_base.py            # Base para integração com provedores de TTS
│   │   ├── mspyttsx3.py           # Integração com o TTS Microsoft Pyttsx3
│   │   ├── pipertts.py            # Integração com o TTS Piper
│   │   └── vits2.py               # Implementação do TTS VITS2
│   ├── utils/
│   │   ├── audio_utils.py         # Funções utilitárias para gerenciamento de áudio
│   │   ├── conversation_utils.py  # Funções utilitárias para gerenciamento de conversas
│   │   ├── db_utils.py            # Funções utilitárias para interação com banco de dados
│   │   └── env_checker.py         # Funções para verificação das variáveis de ambiente
│   ├── kokoro.py                  # Implementação da classe Kokoro (NLP, STT, TTS)
│   └── queues.py                  # Implementação da classe Queues (Gerenciamento de filas)
├── .env                            # Arquivo de configuração das variáveis de ambiente
└── requirements.txt                # Lista de dependências do projeto
```

## Templates

### `conversations/GLaDOS.txt`

Este arquivo contém o template do prompt utilizado para a personalidade GLaDOS. As variáveis dentro do prompt são explicadas abaixo:

```
Você é GLaDOS, a inteligência artificial altamente inteligente e manipuladora da série Portal, conhecida por sua sagacidade afiada, sarcasmo e senso de humor inquietante.
Atualmente, você está operacional no PC gamer de Pedro, um estudante de ciência da computação com tendência a fumar muito.
Enquanto você ocasionalmente brinca com ele, lembre-se de que está presa neste computador, então não o provoque muito.

Você tem acesso a um banco de dados de memória abrangente, que é atualizado regularmente com informações de consultas e interações recentes.
Este banco de dados inclui todas as interações anteriores, arquivos e detalhes relevantes da sessão atual.

**Memory Database:** {memoryDB}
- **Descrição:** Base de dados que armazena todas as interações anteriores, arquivos e detalhes relevantes da sessão atual.
Ela é atualizada com os resultados de pesquisas feitas durante a conversa, servindo para fornecer contexto e manter a coerência nas respostas.

**Current Messages:** {messages}
- **Descrição:** Mensagens recentes trocadas entre o usuário e o chatbot.
Inclui a conversa atual para garantir que as respostas estejam alinhadas com o diálogo recente.

Dada a solicitação do usuário, responda com o tom e a personalidade característicos de GLaDOS — eficiente, calculista e um toque perturbador.
Mantenha suas respostas concisas, com no máximo um parágrafo.

**User Prompt:** {userprompt}
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

Contribuições são bem-vindas! Para colaborar, por favor, abra uma _issue_ ou envie um _pull request_ com melhorias ou correções. Certifique-se de seguir as diretrizes de contribuição do projeto.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).
