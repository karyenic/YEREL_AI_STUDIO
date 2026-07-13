Set-Location -Path "C:\AI_YEREL\AI_YEREL_V3"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Python paketlerini kurma" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Calisma klasoru: $(Get-Location)"
Write-Host ""

if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "[HATA] venv bulunamadi. Once kurulum.bat dosyasini calistirin." -ForegroundColor Red
    Read-Host "Cikmak icin Enter'a basin"
    exit 1
}

Write-Host "[BILGI] Sanal ortam aktif ediliyor..." -ForegroundColor Cyan
try {
    & ".\venv\Scripts\Activate.ps1"
}
catch {
    Write-Host "[UYARI] PowerShell betik calistirma politikasi bunu engelliyor olabilir." -ForegroundColor Yellow
    Write-Host "        Bu betigi su komutla calistirmayi deneyin:" -ForegroundColor Yellow
    Write-Host '        powershell -ExecutionPolicy Bypass -File "C:\AI_YEREL\AI_YEREL_V3\paket_kur.ps1"' -ForegroundColor Yellow
    Read-Host "Cikmak icin Enter'a basin"
    exit 1
}

if (-not (Test-Path ".\requirements.txt")) {
    Write-Host "[HATA] requirements.txt bulunamadi. Once bu dosyayi klasore koyun." -ForegroundColor Red
    Read-Host "Cikmak icin Enter'a basin"
    exit 1
}

Write-Host "[BILGI] pip guncelleniyor..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "[BILGI] requirements.txt icindeki paketler kuruluyor (bu birkac dakika surebilir)..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "[HATA] Kurulumda sorun olustu, yukaridaki hata mesajina bakin." -ForegroundColor Red
    Read-Host "Cikmak icin Enter'a basin"
    exit 1
}

Write-Host ""
Write-Host "[OK] Tum paketler basariyla kuruldu." -ForegroundColor Green
Write-Host "     Simdi baslat.bat ile programi calistirabilirsiniz." -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a basin"
