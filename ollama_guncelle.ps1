Set-Location -Path "C:\AI_YEREL\AI_YEREL_V3"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Ollama Guncelleme" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[BILGI] Su anki Ollama surumunuz:" -ForegroundColor Cyan
ollama --version
Write-Host ""

Write-Host "[BILGI] Calisan Ollama servisi varsa kapatiliyor..." -ForegroundColor Cyan
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "[BILGI] Guncel Ollama kurulum dosyasi indirmek icin tarayici aciliyor..." -ForegroundColor Cyan
Write-Host "        Acilan sayfadan 'Download for Windows' butonuna tiklayip" -ForegroundColor Yellow
Write-Host "        indirilen OllamaSetup.exe dosyasini calistirin." -ForegroundColor Yellow
Write-Host "        Kurulum bittikten sonra bu pencereye donup Enter'a basin." -ForegroundColor Yellow
Start-Process "https://ollama.com/download/windows"

Read-Host "Kurulumu tamamladiktan sonra Enter'a basin"

Write-Host ""
Write-Host "[BILGI] Yeni surum kontrol ediliyor..." -ForegroundColor Cyan
ollama --version

Write-Host ""
Write-Host "[BILGI] llama3.2-vision modelini yeniden indirmeniz gerekebilir:" -ForegroundColor Cyan
Write-Host "        ollama pull llama3.2-vision:11b" -ForegroundColor Yellow
$pullNow = Read-Host "Simdi indirilsin mi? (E/H)"
if ($pullNow -eq "E" -or $pullNow -eq "e") {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    ollama pull llama3.2-vision:11b
    Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "[OK] Islem tamamlandi." -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a basin"
