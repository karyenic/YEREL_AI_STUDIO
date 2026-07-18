Set-Location -Path "C:\AI_YEREL\AI_YEREL_V3"

$ekler = @"

# Calisma zamaninda otomatik olusan veri dosyalari (kisisel/degisken veri)
model_stats.json
cloud_usage.json
conversations_backup.json
"@

$mevcut = Get-Content ".gitignore" -Raw
if ($mevcut -notmatch "model_stats.json") {
    Add-Content -Path ".gitignore" -Value $ekler
    Write-Host "[OK] .gitignore guncellendi." -ForegroundColor Green
} else {
    Write-Host "[BILGI] .gitignore zaten guncel." -ForegroundColor Cyan
}
Read-Host "Kapatmak icin Enter'a basin"
