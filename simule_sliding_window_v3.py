import os

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ HATA: static/index.html bulunamadı!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

print("=" * 60)
print("🔍 KAYAR PENCERE SİMÜLASYONU v3 (0 Byte Yazma)")
print("=" * 60)

target_1 = "? { prompt: userMsg, model, images: imagesToSend, history }"
replacement_1 = "? { prompt: userMsg, model, images: imagesToSend, history: (history || []).slice(-10) }"

# İlgili satırdaki fonksiyon ismine göre dinamik eşleştirme
if "getSelectedRolePrompt()" in content:
    target_2 = ": { prompt: userMsg, model, history, system: getSelectedRolePrompt() };"
    replacement_2 = ": { prompt: userMsg, model, history: (history || []).slice(-10), system: getSelectedRolePrompt() };"
else:
    target_2 = ": { prompt: userMsg, model, history, system: getSelectedSystemPrompt() };"
    replacement_2 = ": { prompt: userMsg, model, history: (history || []).slice(-10), system: getSelectedSystemPrompt() };"

print("\n[SATIR 1008: Resimli İletim]")
print(f"--- MEVCUT --- : {target_1}")
print(f"--- SİMÜLE  --- : {replacement_1}")

print("\n[SATIR 1009: Metin İletimi]")
print(f"--- MEVCUT --- : {target_2}")
print(f"--- SİMÜLE  --- : {replacement_2}")

print("\n" + "=" * 60)
print("🛡️ DİSK DURUMU: index.html DOSYASI DEĞİŞTİRİLMEDİ (0 Byte Yazıldı)")
print("=" * 60)