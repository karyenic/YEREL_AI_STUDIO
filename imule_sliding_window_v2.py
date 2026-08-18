import os

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ HATA: static/index.html dosyası bulunamadı!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("=" * 60)
print("🔍 HISTORY KULLANIMLARI TESPİT SİMÜLASYONU v2 (0 Byte Yazma)")
print("=" * 60)

for line_num, line in enumerate(lines, 1):
    if "history" in line and ("body" in line or "prompt" in line or "system" in line or "fetch" in line):
        print(f"Satır {line_num}: {line.strip()}")

print("=" * 60)
print("🛡️ DİSK DURUMU: index.html DOSYASI DEĞİŞTİRİLMEDİ (0 Byte Yazıldı)")
print("=" * 60)