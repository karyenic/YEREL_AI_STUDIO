Set-Location -Path "C:\AI_YEREL\AI_YEREL_V3"

$logFile = "C:\AI_YEREL\AI_YEREL_V3\log.txt"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Hata Ayiklama Modu" -ForegroundColor Cyan
Write-Host " Tum ciktilar hem ekrana hem de su dosyaya yazilacak:" -ForegroundColor Cyan
Write-Host " $logFile" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "[HATA] venv bulunamadi. Once kurulum.bat dosyasini calistirin." -ForegroundColor Red
    Read-Host "Cikmak icin Enter'a basin"
    exit 1
}

Write-Host "[BILGI] Ollama baslatiliyor..." -ForegroundColor Cyan
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "[BILGI] Sanal ortam aktif ediliyor..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

Start-Process "http://127.0.0.1:5000"

Write-Host "[BILGI] Flask baslatiliyor..." -ForegroundColor Cyan
Write-Host "[BILGI] Tarayicida hatayi olusturan islemi (ornegin Gemini ile sohbet) tekrar deneyin." -ForegroundColor Yellow
Write-Host "[BILGI] Bitirdiginizde bu pencerede Ctrl+C'ye basip programi durdurun." -ForegroundColor Yellow
Write-Host ""

try { Stop-Transcript | Out-Null } catch {}

try {
    Start-Transcript -Path $logFile -Force -Encoding utf8 | Out-Null
    python app.py
}
finally {
    try { Stop-Transcript | Out-Null } catch {}

    Write-Host ""
    Write-Host "[BILGI] Ollama kapatiliyor..." -ForegroundColor Cyan
    Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Magenta
    Write-Host " ONEMLI HATA SATIRLARI (varsa):" -ForegroundColor Magenta
    Write-Host "============================================" -ForegroundColor Magenta
    if (Test-Path $logFile) {
        $important = Get-Content $logFile | Select-String -Pattern "MODEL HATASI", "\[Gemini\]", "Traceback", "Error", "error"
        if ($important) {
            $important | ForEach-Object { Write-Host $_.Line -ForegroundColor Yellow }
        } else {
            Write-Host "(Onemli bir hata satiri bulunamadi - sorun tekrar olusmamis olabilir)" -ForegroundColor Green
        }
    } else {
        Write-Host "(log.txt dosyasi bulunamadi)" -ForegroundColor Red
    }
    Write-Host "============================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "[OK] Program kapandi. Yukaridaki sari satirlari kopyalayip Claude'a yapistirin." -ForegroundColor Green
    Read-Host "Kapatmak icin Enter'a basin"
}