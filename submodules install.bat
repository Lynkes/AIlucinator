@echo off
REM Download and install the required dependencies for the project on Windows

echo Downloading Llama...
REM curl -L "https://github.com/ggerganov/llama.cpp/releases/download/b3266/cudart-llama-bin-win-cu12.2.0-x64.zip" --output "cudart-llama-bin-win-cu12.2.0-x64.zip"
REM curl -L "https://github.com/ggerganov/llama.cpp/releases/download/b3266/llama-b3266-bin-win-cuda-cu12.2.0-x64.zip" --output "llama-bin-win-cuda-cu12.2.0-x64.zip"
echo Unzipping Llama...
REM tar -xf cudart-llama-bin-win-cu12.2.0-x64.zip -C submodules\llama.cpp
REM tar -xf llama-bin-win-cuda-cu12.2.0-x64.zip -C submodules\llama.cpp

echo Downloading Whisper...
curl -L "https://github.com/ggerganov/whisper.cpp/releases/download/v1.6.0/whisper-cublas-12.2.0-bin-x64.zip" --output "whisper-cublas-12.2.0-bin-x64.zip"
echo Unzipping Whisper...
mkdir submodules
tar -xf whisper-cublas-12.2.0-bin-x64.zip -C submodules\whisper.cpp

echo Cleaning up...
REM del whisper-cublas-12.2.0-bin-x64.zip
REM del cudart-llama-bin-win-cu12.2.0-x64.zip
REM del llama-bin-win-cuda-cu12.2.0-x64.zip

REM Download ASR and LLM Models
echo Downloading Models...
REM https://huggingface.co/distil-whisper/distil-medium.en/resolve/main/ggml-medium-32-2.en.bin
REM https://huggingface.co/distil-whisper/distil-large-v3-ggml/resolve/main/ggml-distil-large-v3.fp32.bin
curl -L "https://huggingface.co/distil-whisper/distil-large-v3-ggml/resolve/main/ggml-distil-large-v3.fp32.bin" --output  "models\ggml-distil-large-v3.fp32.bin"
REM curl -L "https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q6_K.gguf?download=true" --output "models\Meta-Llama-3-8B-Instruct-Q6_K.gguf"
echo Done!
