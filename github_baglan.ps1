# ============================================
# Yerel AI Studio projesini GitHub'a gonderme
# ============================================
# KULLANIM: Asagidaki KULLANICI_ADINIZ ve REPO_ADI kisimlarini kendi
# GitHub bilgilerinizle degistirdikten sonra bu dosyayi PowerShell'de
# calistirin:
#   powershell -ExecutionPolicy Bypass -File "C:\AI_YEREL\AI_YEREL_V3\github_baglan.ps1"

Set-Location -Path "C:\AI_YEREL\AI_YEREL_V3"

# --- BURAYI KENDINIZE GORE DUZENLEYIN ---
$githubRepoUrl = "https://github.com/karyenic/YEREL_AI_STUDIO.git"
# -----------------------------------------

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " GitHub'a Baglanma" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

where.exe git 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[HATA] Git kurulu degil. https://git-scm.com/download/win adresinden kurun." -ForegroundColor Red
    Read-Host "Cikmak icin Enter'a basin"
    exit 1
}

# .gitignore olustur (venv, uploads, excels, .env gibi hassas/gereksiz dosyalar gonderilmesin)
if (-not (Test-Path ".gitignore")) {
    Write-Host "[BILGI] .gitignore olusturuluyor (venv, .env, gecici dosyalar haric tutuluyor)..." -ForegroundColor Cyan
    @"
venv/
__pycache__/
*.pyc
.env
uploads/
excels/
log.txt
"@ | Out-File -FilePath ".gitignore" -Encoding utf8
} else {
    Write-Host "[OK] .gitignore zaten mevcut." -ForegroundColor Green
}

if (-not (Test-Path ".git")) {
    Write-Host "[BILGI] Git deposu baslatiliyor..." -ForegroundColor Cyan
    git init
    git branch -M main
} else {
    Write-Host "[OK] Git deposu zaten mevcut." -ForegroundColor Green
}

Write-Host "[BILGI] Dosyalar ekleniyor..." -ForegroundColor Cyan
git add .

Write-Host "[BILGI] Kaydediliyor (commit)..." -ForegroundColor Cyan
git commit -m "Yerel AI Studio guncelleme"

$existingRemote = git remote 2>$null
if ($existingRemote -notcontains "origin") {
    Write-Host "[BILGI] GitHub uzak baglantisi ekleniyor..." -ForegroundColor Cyan
    git remote add origin $githubRepoUrl
} else {
    Write-Host "[OK] 'origin' zaten tanimli." -ForegroundColor Green
}

Write-Host "[BILGI] GitHub'a gonderiliyor (ilk seferde giris istenebilir)..." -ForegroundColor Cyan
git push -u origin main

Write-Host ""
Write-Host "[OK] Islem tamamlandi." -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a basin"
