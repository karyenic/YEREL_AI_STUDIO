@echo off
title Yerel AI Studio V3 - Motor Odasi
cd /d "%~dp0"
echo [Sistem] Sanal ortam yukleniyor...
if not exist venv\Scripts\activate.bat (
    echo [Hata] venv klasoru eksik veya bozuk! Lutfen venv yenileme adimini uygulayin.
    pause
    exit /b
)
call venv\Scripts\activate.bat
echo [Sistem] Kararli kutuphaneler kontrol ediliyor...
pip install -r requirements.txt --quiet
echo [Sistem] Tarayici arayuzu aciliyor...
start http://127.0.0.1:5000
echo [Sistem] Flask Web Sunucusu Atesleniyor...
python app.py
pause