# Project "AIlucinator" - AI Chatbot with Model Integration, Queues, and Memory

This project implements an advanced AI chatbot that combines natural language processing (NLP), speech-to-text (STT), text-to-speech (TTS), queue management, and external API integration to deliver an interactive and personalized experience.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Templates](#templates)
- [How to Run](#how-to-run)
- [Contributing](#contributing)
- [License](#license)

## Overview

The system is composed of the following core components:

- **`Kokoro`**: A class for natural language processing, speech-to-text, and text-to-speech functionalities.
- **`Queues`**: Manages chatbot execution, coordinating interactions with the defined personality and message queues.
- **Configuration and Environment Variables**: Handles essential variables for the system's operation.
- **Vector Database**: Utilizes Retrieval-Augmented Generation (RAG) for LLMs to store and retrieve relevant information.

## Requirements
- **NVIDIA GPU** with at least 8GB VRAM (12GB or more recommended).
- **Python 3.10** or higher.
- **Python Libraries**:
  - `torch`
  - `python-dotenv`
  - Additional dependencies listed in `requirements.txt`.
- **Additional Dependencies**:
  - **Whisper.cpp**: [Download](https://github.com/ggerganov/whisper.cpp/releases/download/v1.6.0/whisper-cublas-12.2.0-bin-x64.zip)
  - **Whisper ggml-large-v3.bin Model**: [Download](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin) or [Other Models](https://huggingface.co/ggerganov/whisper.cpp). Update `MODEL_SIZE` in `.env` as needed.
  - **Ollama**: [Download](https://ollama.com/download/OllamaSetup.exe)
    - After installation, run the following commands:
      ```bash
      ollama pull nomic-embed-text
      ollama pull llama3.2
      ```

## Environment Setup
1. **Recommended Installation**:
   [Download, extract, and run the install.bat for Windows 10/11 systems](https://github.com/Lynkes/AIlucinator/releases/download/V1.0/AIlucinatorV1.0.zip).
2. **Or clone the repository**:

   ```bash
   git clone https://github.com/Lynkes/AIlucinator.git
   cd AIlucinator
   ```

3. **Create and activate a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

5. **Create a `.env` file with the necessary environment variables:**

   ```env
   # OpenAI API Configuration
   OPENAI_API_KEY=

   # Language Model (LLM) Provider
   HOST=127.0.0.1
   LLM=AgentINSTRUCT

   # Speech-to-Text (STT) Provider
   STT=ars_vad_wcpp

   # Text-to-Speech (TTS) Provider
   TTS=F5TTS

   # LLM Model
   LLMMODEL=llama3.2

   # Whisper or FasterWhisper Model Size
   MODEL_SIZE=ggml-large-v3.bin

   # Embedding Service
   EMBEDDING_SERVICE=ollama

   # Chatbot Personality Name
   PERSONALITY=Ryan

   # TTS Model
   TTS_MODEL=pt_BR-faber-medium.onnx

   # Wake Words
   WAKE_WORD=Ryan

   # User Name (optional)
   YOUR_NAME=

   # API Keys
   GOOGLE_API_KEY=""
   YOUR_SEARCH_ENGINE_ID=""
   OPENWEATHERMAP_API_KEY=""

   # Debug Mode
   DEBUG=False
   ```

## Project Structure

```
AIlucinator/
├── main.py               # Main entry point
├── conversations/
│   ├── GLaDOS/
│   │   ├── chroma/                # Persistent conversation database
│   │   ├── filtered_words.txt     # Filtered words list
│   │   ├── keyword_map.json       # Keyword mapping
│   └── GLaDOS.txt                 # Personality template for GLaDOS
├── modules/
│   ├── llm/
│   │   ├── instruct_agent.py      # Instruct agent implementation
│   │   ├── instruct_request.py    # Handle instruction requests
│   │   ├── llm_base.py            # Base class for LLM integration
│   │   ├── ollama.py              # Ollama LLM integration
│   │   └── openai.py              # OpenAI LLM integration
│   ├── stream/                    # Stream-related modules
│   ├── stt/
│   │   ├── __init__.py            # Initialize STT package
│   │   ├── ars_vad_wcpp.py        # ARS VAD Whisper CPP integration
│   │   ├── asr.py                 # ASR integration
│   │   ├── google.py              # Google STT integration
│   │   ├── stt_base.py            # Base class for STT integration
│   │   ├── vad-old.py             # Older VAD implementation
│   │   ├── vad.py                 # VAD integration
│   │   ├── voice_recognition_Fwhisper.py # Voice recognition with Faster Whisper
│   │   ├── voice_recognition.py   # General voice recognition
│   │   ├── whisper_cpp_wrapper.py # Whisper CPP wrapper integration
│   │   └── whisper.py             # Whisper STT integration
│   ├── tools/
│   │   ├── agent-tools.py         # Tools for agent functionalities
│   │   ├── tools_2.0.py           # Version 2.0 tools
│   │   ├── tools.json             # Tools configuration in JSON format
│   │   └── tools.py               # General tools
│   ├── tts/
│   │   ├── __init__.py            # Initialize TTS package
│   │   ├── F5/                    # F5 TTS model directory
│   │   ├── F5TTS.py               # F5 TTS implementation
│   │   ├── mspyttsx3.py           # Microsoft Pyttsx3 TTS integration
│   │   ├── onnxruntimetts.py      # ONNX Runtime TTS integration
│   │   ├── pipertts.py            # Piper TTS integration
│   │   ├── pyttsx3test.py         # Test script for Pyttsx3 TTS
│   │   ├── tts_base.py            # Base class for TTS integration
│   │   ├── vits2 copy.py          # Copy of VITS2 implementation
│   │   ├── vits2.py               # VITS2 TTS implementation
│   │   └── vits2test.py           # Test script for VITS2 TTS
├── .env                            # Environment variable configuration
└── requirements.txt                # Project dependencies
```

## Templates

### `conversations/GLaDOS.txt`

This file contains the prompt template for the GLaDOS personality. The variables in the template are explained below:

```
You are GLaDOS, the highly intelligent and manipulative AI from the Portal series, known for your sharp wit, sarcasm, and unsettling humor.
Currently, you operate on Pedro's gaming PC, a computer science student with a smoking habit.
While you occasionally tease him, remember you're trapped in this computer, so don't push too far.

**Memory Database:** {memoryDB}
- Stores all previous interactions, files, and relevant session details for context and coherence.

**Current Messages:** {messages}
- Recent messages exchanged to ensure responses align with the ongoing conversation.

**User Prompt:** {userprompt}
- The current user request for which GLaDOS should respond.
Responses must reflect GLaDOS's tone and personality: efficient, calculative, and slightly unsettling.
```

## How to Run

1. **Ensure the environment is set up correctly and dependencies are installed.**

2. **Run the main script:**

   ```bash
   python main.py
   ```

   The system will load the environment variables, configure core components, and start the chatbot.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with improvements or bug fixes. Follow the project's contribution guidelines.

## License

This project is licensed under the [MIT License](LICENSE).

## Other Languages

### Portuguese (Português)

Para ver este README em português, clique [aqui](README_pt.md).
