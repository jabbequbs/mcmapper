@echo off
setlocal

cd %~dp0

set VENV=python3
set PYTHON=%VENV%\Scripts\python.exe
if not exist %PYTHON% (
    echo Performing first time setup...
    echo py -3 -m venv %VENV%
    py -3 -m venv %VENV%
    echo %PYTHON% -m pip install -r scripts\requirements.txt
    %PYTHON% -m pip install -r scripts\requirements.txt
)

%PYTHON% scripts\viewer.py || pause
exit /b
