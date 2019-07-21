@echo off
setlocal

cd %~dp0\bin
powershell.exe -NoProfile -ExecutionPolicy Bypass -File setup.ps1 || pause
exit /b
