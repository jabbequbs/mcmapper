@echo off
setlocal

set VENV=python3
if not exist %VENV%\Scripts\activate.bat (
    py -3 -m venv %VENV%
    call %VENV%\Scripts\activate.bat
    pip install -r requirements.txt
    call %VENV%\Scripts\deactivate.bat
)

call %VENV%\Scripts\activate.bat
start "" pythonw scripts\main.py
exit /b
