echo off
title Python Embedded

set inst_dir=%CD%
cd /d "%inst_dir%"
echo %inst_dir%

if not defined PYTHON (set PYTHON=python)
if not defined PY_EMBEDDED (set "PY_EMBEDDED=%inst_dir%\python-embedded")
set ERROR_REPORTING=FALSE

if not exist "%PY_EMBEDDED%\python.exe" (
    curl -o "python-3.10.11-embed-amd64.zip" https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip
    mkdir python-embedded
    powershell -command "Expand-Archive -Path '%inst_dir%\python-3.10.11-embed-amd64.zip' -DestinationPath '%inst_dir%\python-embedded'"
    del "python-3.10.11-embed-amd64.zip"
    curl -L "https://github.com/ggerganov/whisper.cpp/releases/download/v1.6.0/whisper-cublas-12.2.0-bin-x64.zip" --output "whisper-cublas-12.2.0-bin-x64.zip"
    powershell -command "Expand-Archive -Path '%inst_dir%\whisper-cublas-12.2.0-bin-x64.zip' -DestinationPath '%inst_dir%\python-embedded'"
    del "whisper-cublas-12.2.0-bin-x64.zip"
)
set PYTHON="%PY_EMBEDDED%\python.exe"
echo venv %PYTHON%
goto:check_pip                      

:check_pip
if exist "%PY_EMBEDDED%\scripts\pip.exe" (
    echo pip set
    set PIP="%PY_EMBEDDED%\scripts\pip.exe"
    goto :install_requirements
)
goto:launch

:pip_install
echo install pip
if not exist "%PY_EMBEDDED%\get-pip.py" (
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o "%PY_EMBEDDED%\get-pip.py"
    rem Edit python310._pth to uncomment import site
    python310.zip
    powershell -command "(Get-Content '%PY_EMBEDDED%\python310._pth') -replace '#import site', 'import site' | Set-Content -Path '%PY_EMBEDDED%\python310._pth'"
    powershell -command "(Get-Content '%PY_EMBEDDED%\python310._pth') -replace 'python310.zip', 'python310.zip`r`n.`r`n..`r`n..modules' | Set-Content -Path '%PY_EMBEDDED%\python310._pth'"
)
%PYTHON% "%PY_EMBEDDED%\get-pip.py"
if %ERRORLEVEL% == 0 goto:check_pip
echo Couldn't install pip
goto :show_stdout_stderr

:install_requirements
echo Installing requirements
mkdir tmp 2>NUL

%PIP% install -r %inst_dir%\requirements.txt
%PIP% install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

del /F "%PY_EMBEDDED%\get-pip.py"
if %ERRORLEVEL% == 1 (
    echo Couldn't install requirements
    goto :show_stdout_stderr
)
goto :launch

:launch
if exist "%PY_EMBEDDED%\get-pip.py" (
    goto :install_requirements
)
cd %inst_dir%
%PYTHON% main.py %*
pause
if exist tmp rmdir /s /q tmp
exit /b

:show_stdout_stderr
echo.
echo exit code: %ERRORLEVEL%

for /f %%i in ("tmp\stdout.txt") do set size=%%~zi
if %size% equ 0 goto :show_stderr
echo.
echo stdout:
type tmp\stdout.txt

:show_stderr
for /f %%i in ("tmp\stderr.txt") do set size=%%~zi
if %size% equ 0 goto :endofscript
echo.
echo stderr:
type tmp\stderr.txt

:endofscript
echo.
echo Launch unsuccessful. Exiting.
pause
if exist tmp rmdir /s /q tmp
pause
