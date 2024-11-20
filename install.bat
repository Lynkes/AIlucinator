@echo off
title Python Embedded Setup

REM Define o diretório de instalação
set inst_dir=%CD%
cd /d "%inst_dir%"
echo Instalando no diretório: %inst_dir%
pause

REM Define variáveis de ambiente
set PYTHON=%inst_dir%\python-embedded\python.exe
set ERROR_REPORTING=TRUE

REM Verifica se o Python Embedded está instalado
if not exist "%PYTHON%" (
    echo Baixando e instalando Python Embedded...
    curl -o "python-3.10.11-embed-amd64.zip" https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip
    mkdir python-embedded
    powershell -command "Expand-Archive -Path '%inst_dir%\python-3.10.11-embed-amd64.zip' -DestinationPath '%inst_dir%\python-embedded'"
    del "python-3.10.11-embed-amd64.zip"
    if not exist "%PYTHON%" (
        echo Falha ao instalar Python Embedded.
        pause
        exit /b
    )
    echo Python Embedded instalado com sucesso.
)

echo Python configurado em: %PYTHON%
pause

REM Ajusta o arquivo python310._pth
:adjust_pth
echo Ajustando o arquivo python310._pth...
if exist "%inst_dir%\python-embedded\python310._pth" (
    copy /Y "%inst_dir%\python-embedded\python310._pth" "%inst_dir%\python-embedded\python310._pth.bak"
    (
        echo python310.zip
        echo .
        echo .\Lib
        echo .\Scripts
        echo .\DLLs
        echo .\tcl
        echo ..
        echo ..\modules
        echo .
                echo import site
    ) > "%inst_dir%\python-embedded\python310._pth"
    echo Arquivo python310._pth ajustado com sucesso.
) else (
    echo Arquivo python310._pth não encontrado. Verifique a instalação do Python Embedded.
    pause
    exit /b
)

pause

REM Verifica se o pip já está instalado
:check_pip
if exist "%inst_dir%\python-embedded\Scripts\pip.exe" (
    echo pip já instalado.
    set PIP="%inst_dir%\python-embedded\Scripts\pip.exe"
    pause
    goto install_requirements
) else (
    echo pip não encontrado. Instalando pip...
    goto pip_install
)

REM Instala o pip
:pip_install
if not exist "%inst_dir%\python-embedded\get-pip.py" (
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o "%inst_dir%\python-embedded\get-pip.py"
)
%PYTHON% "%inst_dir%\python-embedded\get-pip.py"
if not exist "%inst_dir%\python-embedded\Scripts\pip.exe" (
    echo Falha ao instalar pip.
    pause
    exit /b
)
set PIP="%inst_dir%\python-embedded\Scripts\pip.exe"
echo pip instalado com sucesso.
pause

REM Instala os requisitos do projeto
:install_requirements
echo Instalando dependências do projeto...
%PYTHON% %PIP% install -r "%inst_dir%\requirements.txt"
%PYTHON% %PIP% install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
if %ERRORLEVEL% neq 0 (
    echo Falha ao instalar dependências.
    pause
    exit /b
)

echo Dependências instaladas com sucesso.
pause

REM Baixa dependências adicionais do projeto
:download_dependencies
echo Baixando dependências adicionais...

REM Baixa Whisper e descompacta
echo Baixando Whisper...
curl -o "whisper-cublas-12.2.0-bin-x64.zip" https://github.com/ggerganov/whisper.cpp/releases/download/v1.6.0/whisper-cublas-12.2.0-bin-x64.zip
if not exist "whisper-cublas-12.2.0-bin-x64.zip" (
    echo Falha ao baixar o Whisper.
    pause
    exit /b
)
mkdir submodules
powershell -Command "Expand-Archive -Path '%inst_dir%\whisper-cublas-12.2.0-bin-x64.zip' -DestinationPath '%inst_dir%\submodules\whisper.cpp'"
del "whisper-cublas-12.2.0-bin-x64.zip"
if not exist "%inst_dir%\submodules\whisper.cpp\whisper.exe" (
    echo Falha ao extrair o Whisper.
    pause
    exit /b
)
echo Whisper instalado com sucesso.
pause

REM Baixa modelos necessários
echo Baixando modelos do Whisper...
mkdir models
curl -o "models\ggml-large-v3.bin" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
if not exist "models\ggml-large-v3.bin" (
    echo Falha ao baixar o modelo ggml-large-v3.bin.
    pause
    exit /b
)
echo Modelos baixados com sucesso.
pause

REM Baixa e solicita instalação do Ollama
echo Baixando Ollama...
curl -o "OllamaSetup.exe" https://ollama.com/download/OllamaSetup.exe
if not exist "OllamaSetup.exe" (
    echo Falha ao baixar o instalador do Ollama.
	echo Baixe manualmente em https://ollama.com/download/OllamaSetup.exe
	echo Execute no terminal depois da instalacao>
	echo ollama pull nomic-embed-text
	echo ollama pull llama3.2
    pause
    exit /b
)
echo Por favor, instale o Ollama manualmente.
echo Execute no terminal depois da instalacao>
echo ollama pull nomic-embed-text
echo ollama pull llama3.2
pause

REM Lança o programa principal
:launch
cd "%inst_dir%"
%PYTHON% main.py %*
pause
exit /b
