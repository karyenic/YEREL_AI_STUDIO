@echo off
chcp 65001 >nul
title GK YEREL AI - Baslatici

cd /d "C:\AI_YEREL\AI_YEREL_GPT"

echo [1/3] Arka plan temizleniyor...
taskkill /F /IM ollama.exe /T >nul 2>&1
taskkill /F /IM ollama_llama_server.exe /T >nul 2>&1

timeout /t 1 /nobreak >nul

echo [2/3] GPU destegi ve Ollama baslatiliyor...
set OLLAMA_IGPU_ENABLE=1
start "" /b ollama serve >nul 2>&1

timeout /t 3 /nobreak >nul

echo [3/3] GK YEREL AI ve Tarayici aciliyor...
start "" "http://127.0.0.1:5000"
"venv\Scripts\python.exe" app.py

pause