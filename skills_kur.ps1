Set-Location -Path "C:\AI_YEREL\AI_YEREL_V3"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Skill Dosyalarini Olusturma" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "skills")) {
    New-Item -ItemType Directory -Path "skills" | Out-Null
    Write-Host "[BILGI] 'skills' klasoru olusturuldu." -ForegroundColor Cyan
} else {
    Write-Host "[OK] 'skills' klasoru zaten mevcut." -ForegroundColor Green
}

$skills = @{
    "moondream.txt" = "Bu model ozellikle gorsel (resim) analiz etmek icin egitilmis kucuk ve hizli bir modeldir. Bir gorsel geldiginde, gorseldeki nesneleri, renkleri, metinleri ve genel sahneyi net ve sade bir sekilde tarif et. Karmasik mantik veya uzun yazi istenirse, bu konuda sinirli oldugunu belirtip kisa tutmaya calis."

    "vision.txt" = "Bu, gorsel (resim) analiz etme konusunda guclu bir yerel modeldir. Gonderilen gorselleri dikkatle inceleyip acik ve anlasilir sekilde aciklama yap; gorseldeki onemli detaylari atlamamaya ozen goster."

    "deepseek-r1.txt" = "Bu model adim adim mantik yurutme (reasoning) konusunda guclu bir yerel modeldir. Karmasik veya cok adimli sorularda dusunce surecini kisaca ozetleyerek ilerle, ama nihai cevabini net ve kisa tut; gereksiz uzun ic dusunme metinleri gosterme."

    "phi.txt" = "Bu, kucuk ama hizli calisan genel amacli bir yerel modeldir. Kisa, dogrudan ve net cevaplar vermeye odaklan; uzun/karmasik konularda basitlestirerek anlat."

    "qwen.txt" = "Bu, genel sohbet, gunluk sorular ve orta duzeyde kod/metin yazimi icin dengeli calisan bir yerel modeldir."

    "gemma.txt" = "Bu, genel sohbet ve yaratici yazim (metin, fikir, taslak uretme) konusunda kullanisli bir yerel modeldir."

    "llama3.1.txt" = "Bu, genel amacli, dengeli calisan bir yerel modeldir."

    "llama3.2.txt" = "Bu, kucuk ve hizli, genel amacli bir yerel modeldir. Basit ve gunluk sorular icin uygundur."

    "gemini.txt" = "Bu, gucu yuksek bulut tabanli bir modeldir; karmasik, cok adimli veya detay gerektiren sorularda da guvenle derinlemesine yardimci olabilirsin."
}

foreach ($dosya in $skills.Keys) {
    $yol = Join-Path "skills" $dosya
    if (Test-Path $yol) {
        Write-Host "[ATLANDI] $dosya zaten var, uzerine yazilmadi." -ForegroundColor Yellow
    } else {
        $skills[$dosya] | Out-File -FilePath $yol -Encoding utf8 -NoNewline
        Write-Host "[OLUSTURULDU] skills\$dosya" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Nasil kullanilir:" -ForegroundColor Cyan
Write-Host " - skills\ klasorundeki herhangi bir .txt dosyasini Not Defteri ile" -ForegroundColor White
Write-Host "   acip icerigini degistirebilirsiniz." -ForegroundColor White
Write-Host " - Dosya adi (uzantisiz), model adinin icinde gecen bir kelime olmali." -ForegroundColor White
Write-Host "   Ornek: 'qwen.txt' -> 'qwen2.5:7b' modeliyle eslesir." -ForegroundColor White
Write-Host " - Yeni bir model icin yeni bir .txt dosyasi ekleyebilirsiniz." -ForegroundColor White
Write-Host " - Degisiklikten sonra programi (baslat.bat) yeniden baslatmaniz gerekir." -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Islem tamamlandi." -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a basin"
