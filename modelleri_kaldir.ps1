# ============================================================
# Gereksiz/Yavas Modelleri Diskten Kaldirma Betigi
# ============================================================
# NASIL CALISIR:
#   Asagidaki $modelsToRemove listesindeki her model icin
#   'ollama rm <model_adi>' calistirir. Bu, hem modeli diskten
#   siler hem de artik "ollama list" ciktisinda gorunmez, dolayisiyla
#   Yerel AI Studio'nun model listesinde de cikmaz.
#
# NASIL DUZENLENIR (ileride baska bir model kaldirmak isterseniz):
#   Asagidaki $modelsToRemove listesine, virgulle ayirarak, tirnak
#   icinde model adini ekleyin veya cikarin. Model adini "ollama list"
#   komutuyla tam olarak (ornegin "qwen2.5:3b" gibi, ":latest" dahil)
#   gorebilirsiniz.
#
# NOT: Bu betik SADECE diskten kaldirir. Yerel AI Studio kodundaki
# (app.py) model listelerinden ayrica cikarilmasi gerekmez - cunku
# uygulama, model listesini her zaman "ollama list" komutundan canli
# olarak okur. Yani bir modeli burada kaldirdiginizda, uygulama
# acildiginda o model zaten dropdown'da gorunmeyecektir.
# ============================================================

Set-Location -Path "C:\AI_YEREL\AI_YEREL_V3"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Gereksiz Modelleri Diskten Kaldirma" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------------------
# KALDIRILACAK MODELLER - bu listeyi ihtiyaciniza gore duzenleyin
# --------------------------------------------------------------
$modelsToRemove = @(
    "phi3:latest",          # phi4:latest daha iyi calistigi icin gereksiz hale geldi
    "llama3.2-vision:11b",  # Ollama surumunuzde "unknown model architecture: mllama" hatasi veriyordu
    "gemma4:12b"            # CPU-only (GPU'suz) bu laptopta 12B parametre cok yavas calisir
)

# Bilerek KALDIRILMAYAN modeller (bilginiz olsun):
#   phi4:latest         -> iyi calistigini bildirdiniz, DOKUNULMUYOR
#   qwen2.5:3b / 7b     -> genel kullanim icin tutuluyor
#   gemma2:2b           -> genel kullanim icin tutuluyor
#   llama3.2:3b, llama3.1:latest -> genel kullanim icin tutuluyor
#   deepseek-r1:1.5b    -> mantik/muhakeme gorevleri icin tutuluyor
#   moondream:latest, granite3.2-vision:2b -> gorsel analiz icin tutuluyor
# --------------------------------------------------------------

Write-Host "Su modeller kaldirilacak:" -ForegroundColor Yellow
foreach ($m in $modelsToRemove) {
    Write-Host "  - $m" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "phi4:latest DOKUNULMUYOR (iyi calistigi icin korunuyor)." -ForegroundColor Green
Write-Host ""

$onay = Read-Host "Devam etmek istiyor musunuz? (E/H)"
if ($onay -ne "E" -and $onay -ne "e") {
    Write-Host "Islem iptal edildi." -ForegroundColor Red
    Read-Host "Kapatmak icin Enter'a basin"
    exit 0
}

Write-Host ""
Write-Host "[BILGI] Ollama baslatiliyor (kapaliysa)..." -ForegroundColor Cyan
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

foreach ($m in $modelsToRemove) {
    Write-Host "[BILGI] Kaldiriliyor: $m ..." -ForegroundColor Cyan
    ollama rm $m
}

Write-Host ""
Write-Host "[BILGI] Guncel kurulu model listesi:" -ForegroundColor Cyan
ollama list

Write-Host ""
Write-Host "[OK] Islem tamamlandi. Disk alani serbest birakildi." -ForegroundColor Green
Write-Host "     Uygulama bir sonraki acilista bu modelleri artik listelemeyecek." -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a basin"