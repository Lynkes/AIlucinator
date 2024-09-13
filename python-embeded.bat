@echo off
title Python Embedded

set inst_dir=%CD%
cd /d "%inst_dir%"

if not defined PYTHON (set PYTHON=python)
if not defined PY_EMBEDDED (set "PY_EMBEDDED=%inst_dir%\python-embedded")
set ERROR_REPORTING=FALSE

if not exist "%PY_EMBEDDED%\python.exe" (
    curl -o "python-3.10.11-embed-amd64.zip" https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip
    mkdir python-embedded
    powershell -command "Expand-Archive -Path '%inst_dir%\python-3.10.11-embed-amd64.zip' -DestinationPath '%inst_dir%\python-embedded'"
    del "python-3.10.11-embed-amd64.zip"
)
set PYTHON="%PY_EMBEDDED%\python.exe"
echo venv %PYTHON%
goto:check_pip

:check_pip
if exist "%PY_EMBEDDED%\scripts\pip.exe" (
    echo pip set
    set PIP="%PY_EMBEDDED%\scripts\pip.exe"
    goto :launch
)
goto:pip_install

:pip_install
echo install pip
if not exist "%PY_EMBEDDED%\get-pip.py" (
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o "%PY_EMBEDDED%\get-pip.py"
    rem Edit python310._pth to uncomment import site
    powershell -command "(Get-Content '%PY_EMBEDDED%\python310._pth') -replace '#import site', 'import site' | Set-Content -Path '%PY_EMBEDDED%\python310._pth'"
)
%PYTHON% "%PY_EMBEDDED%\get-pip.py"
if %ERRORLEVEL% == 0 goto:check_pip
echo Couldn't install pip
goto :show_stdout_stderr

:install_requirements
echo Installing requirements
mkdir tmp 2>NUL
%PIP% install -r requirements.txt >tmp\stdout.txt 2>tmp\stderr.txt
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
%PYTHON% glados-ui.py %*
if exist tmp rmdir /s /q tmp
pause
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
if exist tmp rmdir /s /q tmp
pause
