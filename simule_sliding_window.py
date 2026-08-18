import os, re

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ HATA: static/index.html dosyası bulunamadı!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

print("=" * 60)
print("🔍 KAYAR PENCERE (SLIDING WINDOW) SİMÜLASYONU (0 Byte Yazma)")
print("=" * 60)

# Fetch body içinde history parametresinin gönderildiği yerleri bul
matches = list(re.finditer(r' history\s*:\s*([a-zA-Z0-9_$]+)', content))

if matches:
    print(f"\n✅ Toplam {len(matches)} istek noktasında 'history' gönderimi yakalandı:\n")
    for i, match in enumerate(matches, 1):
        target_str = match.group(0)
        var_name = match.group(1)
        simulated_str = f" history: ({var_name} || []).slice(-10)"
        
        print(f"[{i}. İSTEK NOKTASI]")
        print(f"--- ORİJİNAL KOD  --- : {target_str.strip()}")
        print(f"--- SİMÜLE EDİLEN --- : {simulated_str.strip()}\n")
else:
    print("\n❌ HEDEF BULUNAMADI: Fetch isteği içindeki 'history' parametresi eşleşmedi.")

print("=" * 60)
print("🛡️ DİSK DURUMU: index.html DOSYASI DEĞİŞTİRİLMEDİ (0 Byte Yazıldı)")
print("=" * 60)