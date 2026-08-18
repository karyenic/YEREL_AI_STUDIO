import os, re

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ HATA: static/index.html dosyası bulunamadı!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    original_content = f.read()

print("=" * 60)
print("🔍 DRY-RUN SİMÜLASYONU BAŞLATILDI (Diske Yazma Yetkisi Kapalı)")
print("=" * 60)

# 1. TEST: "+ Yeni Sohbet" Ekran Sıfırlama Bloğu Simülasyonu
new_chat_match = re.search(r'(function\s+(?:newChat|createNewChat)\s*\([^)]*\)\s*\{)', original_content)
if new_chat_match:
    target_func = new_chat_match.group(1)
    simulated_func = target_func + "\n        const chatBox = document.getElementById('chatBox'); if (chatBox) chatBox.innerHTML = '';"
    print("\n[1. SİMÜLASYON: Yeni Sohbet Temizleme Kodu]")
    print("--- ORİJİNAL KOD BLOK ---")
    print(target_func)
    print("--- SİMÜLE EDİLEN KOD BLOK ---")
    print(simulated_func)
else:
    print("\n❌ 1. TEST BAŞARISIZ: newChat fonksiyonu tespit edilemedi!")

# 2. TEST: Üst Bar Rol Seçici HTML Entegrasyonu Simülasyonu
# Topbar d-flex veya ollamaStatus alanını yakalama
topbar_match = re.search(r'(<[^>]*id="ollamaStatus"[^>]*>)', original_content)
if not topbar_match:
    topbar_match = re.search(r'(<[^>]*>(?:\s*|.*?)[ÖöO]llama[\s\S]*?</[^>]*>)', original_content)

role_select_html = """<select id="roleSelect" class="form-select form-select-sm" style="width: auto; height: 32px; border-radius: 16px; padding: 0 10px; font-size: 0.81rem; font-weight: 600; background-color: var(--bg-hist-item, #1e222d); color: var(--text-body, #e2e8f0); border: 1px solid var(--border-color, #33394b); margin-right: 8px;">
        <option value="default">🎯 Rol: Genel</option>
        <option value="coder">💻 Rol: Yazılım Mimarı</option>
        <option value="writer">📝 Rol: Teknik Yazar</option>
        <option value="analyst">📊 Rol: Veri Analisti</option>
    </select>"""

if topbar_match:
    target_html = topbar_match.group(1)
    simulated_html = role_select_html + "\n        " + target_html
    print("\n[2. SİMÜLASYON: Topbar Rol Dropdown HTML Bloğu]")
    print("--- ORİJİNAL HTML HEDEF ---")
    print(target_html)
    print("--- SİMÜLE EDİLEN HTML BÜTÜNÜ ---")
    print(simulated_html)
else:
    print("\n❌ 2. TEST BAŞARISIZ: Üst bar Ollama hedef etiketleri bulunamadı!")

print("\n" + "=" * 60)
print("🛡️ DİSK DURUMU: index.html DOSYASI DEĞİŞTİRİLMEDİ (0 Byte Yazıldı)")
print("=" * 60)