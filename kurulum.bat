@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo  AI Yerel Studio V3 - Otomatik Kurulum
echo ============================================
echo Calisma klasoru: %cd%
echo.

REM --- 1) Python kontrolu -----------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi.
    echo         https://www.python.org/downloads/ adresinden Python kurun.
    echo         Kurulum ekraninda "Add Python to PATH" kutusunu isaretlemeyi unutmayin.
    pause
    exit /b 1
)
echo [OK] Python bulundu.

REM --- 2) Ollama kontrolu -------------------------------------------------
where ollama >nul 2>&1
if errorlevel 1 (
    echo [UYARI] 'ollama' komutu bulunamadi.
    echo          Kurulu degilse https://ollama.com adresinden indirin.
) else (
    echo [OK] Ollama bulundu.
)
echo.

REM --- 3) Gerekli klasorleri olustur --------------------------------------
if not exist "static" mkdir "static"
if not exist "excels" mkdir "excels"
if not exist "uploads" mkdir "uploads"
echo [OK] Klasorler hazir: static\, excels\, uploads\

REM --- 4) Sanal ortam (venv) ----------------------------------------------
if not exist "venv\Scripts\activate.bat" (
    echo [BILGI] Sanal ortam (venv) olusturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo [HATA] Sanal ortam olusturulamadi.
        pause
        exit /b 1
    )
) else (
    echo [OK] Sanal ortam zaten mevcut.
)

REM --- 5) Sanal ortami aktif et, paketleri kur -----------------------------
call venv\Scripts\activate.bat

echo [BILGI] pip guncelleniyor...
python -m pip install --upgrade pip >nul

if not exist "requirements.txt" (
    echo [HATA] requirements.txt bulunamadi.
    echo         Bu dosyayi "%cd%" klasorune koyup tekrar calistirin.
    pause
    exit /b 1
)

echo [BILGI] Gerekli Python paketleri kuruluyor, bu birkac dakika surebilir...
pip install -r requirements.txt
if errorlevel 1 (
    echo [HATA] Paket kurulumunda sorun olustu, yukaridaki hata mesajina bakin.
    pause
    exit /b 1
)
echo [OK] Python paketleri kuruldu.
echo.

REM --- 6) .env dosyasi kontrolu --------------------------------------------
if not exist ".env" (
    echo [UYARI] .env dosyasi bulunamadi.
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [BILGI] .env.example kopyalanarak .env olusturuldu.
        echo          Icine gercek GEMINI_API_KEY degerinizi yazmayi unutmayin.
    ) else (
        echo GEMINI_API_KEY=> ".env"
        echo [BILGI] Bos bir .env dosyasi olusturuldu.
        echo          Icine "GEMINI_API_KEY=..." satirini elle ekleyin.
    )
) else (
    echo [OK] .env dosyasi zaten mevcut, dokunulmadi.
)
echo.

REM --- 7) Onerilen yerel modelleri indirme (istege bagli) ------------------
set /p PULLMODELS="Onerilen kucuk/hizli yerel modelleri simdi indirmek ister misiniz? (E/H): "
if /I "%PULLMODELS%"=="E" (
    where ollama >nul 2>&1
    if errorlevel 1 (
        echo [UYARI] Ollama kurulu olmadigi icin model indirilemiyor. Once Ollama'yi kurun.
    ) else (
        echo [BILGI] Ollama servisi gecici olarak baslatiliyor...
        start /B ollama serve >nul 2>&1
        timeout /t 3 /nobreak >nul

        for %%M in (qwen2.5:3b llama3.2:3b gemma2:2b moondream:latest) do (
            echo [BILGI] %%M indiriliyor...
            ollama pull %%M
        )

        echo [BILGI] Gecici Ollama servisi kapatiliyor...
        taskkill /IM ollama.exe /F >nul 2>&1
        echo [OK] Modeller indirildi.
    )
)

echo.
echo ============================================
echo  Kurulum tamamlandi.
echo  Programi baslatmak icin: baslat.bat
echo ============================================
pause