# AI_YEREL_GPT — Düzeltilmiş app.py Kurulum Talimatı

## Nasıl kurulur
1. Mevcut `C:\AI_YEREL\AI_YEREL_GPT\app.py` ve `index.html` dosyalarını yedekle (örn. `_eski` ekiyle kopyala).
2. Bu ekteki **`app.py`** ve **`index.html`**'i aynı dizine, üzerine yaz.
3. Bu ekteki **`prompts.json`**'ı da aynı dizine üzerine yaz.
4. Bu ekteki **`durdur.bat`**'ı da üzerine yaz (Ollama'yı artık gerçekten kapatıyor).
5. `prompt_v5.json` ve `prompts_v5.json` dosyalarını silebilirsin — artık gerekmiyorlar, tek doğru dosya `prompts.json`.
6. `baslat.bat` ile normal şekilde başlat.

## Neler değişti

### Düzeltilen 3 bug
1. **`models.json` artık gerçekten okunuyor** — yol `config/models.json` yerine kök dizindeki `models.json` olarak düzeltildi.
2. **`prompts.json` artık gerçekten kullanılıyor** — kod ile dosyanın şeması artık eşleşiyor, kendi yazdığın master prompt devrede.
3. **`skills.json`'daki 5 skill artık çalışıyor** — teknik_resim_okuyucu, cad_step_generator, tolerans_ve_kalite_kontrol, maliyet_ve_hacim_hesaplayici, excel_bom_parser artık `/models` listesinde `jskill:<isim>` anahtarıyla görünüyor ve seçildiğinde kendi model + talimatıyla çalışıyor.

### Eklenen 3 iyileştirme
4. **GPU ayarı** — `OLLAMA_NUM_GPU` ortam değişkeni ile Ollama'ya kaç katmanı Arc 140V'ye yükleyeceği söyleniyor (varsayılan: 999). Sorun çıkarsa `.env`'e `OLLAMA_NUM_GPU=0` ekle.
5. **Otomatik model seçimi** — `model: "auto"` gönderilirse ("neden", "kanıtla", "adım adım" gibi kelimeler geçen istekler deepseek-r1'e, diğerleri varsayılan modele gider).
6. **Gerçek web araştırma modu** — `/models` artık `arastirma:gemini-search` döndürüyor (Gemini API anahtarın varsa).

### Bu turda eklenenler
7. **V5 kalıntıları temizlendi** — `app.py`'deki hardcoded fallback prompt ve `index.html`'in sayfa başlığı artık "Yerel AI Studio GPT" diyor. (`migration_report.txt` içindeki V5 referansı sadece geçmişe dönük bir kayıt, dokunmadım.)
8. **"⏻ Çıkış" butonu eklendi** (üst çubukta, sağda) — tıklanınca backend'deki yeni `/shutdown` endpoint'ini çağırıyor; bu da hem Flask sürecini hem Ollama'yı (`ollama.exe` + `ollama_llama_server.exe`) birlikte kapatıyor. Not: tarayıcı güvenlik kısıtlaması yüzünden `window.close()` her tarayıcı/sekme türünde otomatik çalışmayabilir — çalışmazsa sekmeyi elle kapatman yeterli, arka plandaki süreçler zaten kapanmış olacak.
9. **`durdur.bat` düzeltildi** — eskiden sadece Flask'ı (`python.exe`) kapatıyordu, Ollama'yı hiç kapatmıyordu ("sonraki aşamada eklenecek" notu duruyordu). Artık ikisini de kapatıyor.

## Dürüst bir not: test edemedim
Bu ortamda gerçek bir Ollama servisi çalıştıramadığım için kodu **kod incelemesi ve sözdizimi kontrolüyle** doğruladım (Python derleyici hatasız derliyor), ama uçtan uca gerçek bir isteği senin makinende çalıştıramadım. Yani:
- Routing mantığı (auto, jskill, arastirma) **kod olarak doğru görünüyor**, ama gerçek modellerle ilk denemede küçük bir uyumsuzluk çıkabilir.
- `arastirma:gemini-search` özellikle risk taşıyor — Gemini kütüphanesinin arama aracı sözdizimi sürüme göre değişebiliyor, bu alan hızlı gelişiyor. İlk denemede hata alırsan mesajı bana ilet, birlikte düzeltiriz.
- `num_ctx` tablosundaki değerler (örn. qwen2.5:7b için 8192) eski CPU-only donanımın için konservatif seçilmiş — artık 32GB RAM + 16GB GPU'n olduğuna göre bu değerleri yükseltebilirsin (Qwen2.5 modelleri native olarak 32768'e kadar destekliyor). Bunu değiştirmedim çünkü RAM/VRAM kullanımını doğrudan etkiliyor, önce mevcut haliyle test edip sonra birlikte kademeli artıralım istersen.

## Test etme sırası
1. Önce hiçbir şeye dokunmadan `baslat.bat` ile aç, normal sohbetin hâlâ çalıştığını doğrula.
2. Bir JSON skill dene (örn. teknik resim görseli yükleyip `jskill:teknik_resim_okuyucu` seç — frontend dropdown'ında görünmüyorsa `http://127.0.0.1:5000/models` adresini tarayıcıda açıp listede olduğunu kontrol et).
3. "⏻ Çıkış" butonunu dene, Görev Yöneticisi'nden `python.exe` ve `ollama.exe`'nin gerçekten kapandığını doğrula.
4. GPU kullanımını Görev Yöneticisi'nden izle.
5. Araştırma modunu dene, hata alırsan tam mesajı bana ilet.

Herhangi bir adımda hata alırsan tam hata mesajını buraya yapıştır, birlikte bakarız.
