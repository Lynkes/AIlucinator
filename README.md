# 🤖 AIlucinator

### Advanced Modular AI Chatbot with LLM Integration, RAG Memory and Voice Interface

AIlucinator is an advanced AI chatbot developed as a Computer Science final graduation project, focused on modular architecture, multi-model integration, persistent memory, and on-premise AI deployment.

The system combines Natural Language Processing, Speech-to-Text, Text-to-Speech, vector databases, and Retrieval-Augmented Generation (RAG) to deliver a customizable and context-aware conversational experience.

---

## 🚀 Key Features

* 🔌 Multi-LLM integration (Ollama, OpenAI, AgentINSTRUCT)
* 🧠 Persistent memory with RAG (Retrieval-Augmented Generation)
* 📚 Vector database with embeddings (ChromaDB)
* 🎙️ Speech-to-Text (Whisper.cpp, Google, others)
* 🔊 Text-to-Speech (VITS2, Piper, F5TTS, etc.)
* 🧩 Fully modular and extensible architecture
* ⚙️ Environment-based configuration
* 🎭 Custom personality system
* 🔄 Queue-based execution management
* 🖥️ Designed for local GPU execution

---

## 🏗️ System Architecture

The application is structured into independent and extensible layers:

```
User Input
   ↓
STT Layer (Whisper / Google / etc.)
   ↓
Queue Manager
   ↓
LLM Layer (Ollama / OpenAI / AgentINSTRUCT)
   ↓
Embedding Service
   ↓
Vector Database (ChromaDB)
   ↓
Memory Context Injection (RAG)
   ↓
TTS Layer
   ↓
Audio Output
```

### Core Modules

* `llm/` → Language model provider integrations
* `stt/` → Speech recognition layer
* `tts/` → Speech synthesis layer
* `utils/` → Audio, database and conversation utilities
* `kokoro.py` → Core orchestration engine (NLP + STT + TTS)
* `queues.py` → Execution and message flow management

---

## 🧠 RAG & Memory System

AIlucinator implements:

* Embedding generation (Ollama / OpenAI / HuggingFace)
* Persistent vector storage (ChromaDB)
* Context-aware retrieval
* Continuous memory updates during conversation

This allows the chatbot to maintain coherence and contextual awareness across sessions.

---

## 🛠️ Tech Stack

* Python 3.10+
* PyTorch (CUDA)
* Ollama
* OpenAI API
* Whisper.cpp
* ChromaDB
* python-dotenv
* VITS2 / Piper TTS

---

## ⚙️ Requirements

* NVIDIA GPU (minimum 8GB VRAM, recommended 12GB+)
* Python 3.10+
* Ollama installed
* Whisper-compatible model
* CUDA-enabled PyTorch

---

## 🔧 Installation

Clone the repository:

```bash
git clone https://github.com/Lynkes/AIlucinator.git
cd AIlucinator
```

Create a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install PyTorch with CUDA:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Configure your `.env` file according to your setup.

---

## ▶️ Running the Application

```bash
python main.py
```

The system will initialize all configured modules and start the chatbot engine.

---

## 🎭 Personality System

Chatbot behavior is defined via customizable prompt templates:

```
conversations/<PERSONALITY>/
```

Each personality includes:

* Base prompt template
* Dedicated vector memory
* Memory files and embeddings
* Independent configuration

This allows the system to simulate different AI personas while preserving contextual memory.

---

## 🎯 Project Goals

This project demonstrates:

* Modular architecture for LLM-based systems
* Multi-provider model integration
* Practical implementation of RAG
* Persistent conversational memory
* Voice-enabled AI interfaces
* On-premise AI deployment
* Engineering-focused AI system design

---

## 📄 License

MIT License

---
