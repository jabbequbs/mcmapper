@echo off
setlocal

cd %~dp0

set VENV=python3
if not exist %VENV%\Scripts\activate.bat (
    set PROMPT=
    echo on
    @echo Performing first time setup...
    py -3 -m venv %VENV%
    call %VENV%\Scripts\activate.bat
    pip install -r scripts\requirements.txt
    call %VENV%\Scripts\deactivate.bat
    @echo off
)

call %VENV%\Scripts\activate.bat
python scripts\main.py || pause
exit /b
