import os, re

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ HATA: static/index.html dosyası bulunamadı!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

print("=" * 60)
print("🔍 REVIZE SİMÜLASYON v2 (Diske Yazma Yetkisi Kapalı)")
print("=" * 60)

# Üst Bar Buton Grubunu Kesin Tespit Etme
# Sağ üstteki Tema / Çıkış / Statü buton grubunu yakalar
target_pattern = r'(<div[^>]*class="[^"]*d-flex[^"]*"[^>]*>[\s\S]*?<button[^>]*>.*?Tema.*?</button>)'
match = re.search(target_pattern, content, re.IGNORECASE)

if not match:
    # Alternatif: Tema butonunun olduğu doğrudan kapsayıcı
    target_pattern = r'(<button[^>]*>.*?Tema.*?</button>)'
    match = re.search(target_pattern, content, re.IGNORECASE)

role_select_html = """<select id="roleSelect" class="form-select form-select-sm" style="width: auto; height: 32px; border-radius: 16px; padding: 0 10px; font-size: 0.81rem; font-weight: 600; background-color: var(--bg-hist-item, #1e222d); color: var(--text-body, #e2e8f0); border: 1px solid var(--border-color, #33394b); margin-right: 8px;">
        <option value="default">🎯 Rol: Genel</option>
        <option value="coder">💻 Rol: Yazılım Mimarı</option>
        <option value="writer">📝 Rol: Teknik Yazar</option>
        <option value="analyst">📊 Rol: Veri Analisti</option>
    </select>"""

if match:
    target_str = match.group(1)
    simulated_str = role_select_html + "\n        " + target_str
    print("\n[2. SİMÜLASYON REVİZE: Gerçek Topbar Hedefi]")
    print("--- BULUNAN HEDEF ELEMAN ---")
    print(target_str)
    print("--- SİMÜLE EDİLEN YENİ YAPI ---")
    print(simulated_str)
else:
    print("\n❌ HEDEF BULUNAMADI: Tema butonu veya üst bar konteyneri tespit edilemedi.")

print("\n" + "=" * 60)
print("🛡️ DİSK DURUMU: index.html DOSYASI DEĞİŞTİRİLMEDİ (0 Byte Yazıldı)")
print("=" * 60)