import os

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ HATA: static/index.html bulunamadı!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

target_1 = "? { prompt: userMsg, model, images: imagesToSend, history }"
replacement_1 = "? { prompt: userMsg, model, images: imagesToSend, history: (history || []).slice(-10) }"

target_2 = ": { prompt: userMsg, model, history, system: getSelectedRolePrompt() };"
replacement_2 = ": { prompt: userMsg, model, history: (history || []).slice(-10), system: getSelectedRolePrompt() };"

target_2_alt = ": { prompt: userMsg, model, history, system: getSelectedSystemPrompt() };"
replacement_2_alt = ": { prompt: userMsg, model, history: (history || []).slice(-10), system: getSelectedSystemPrompt() };"

if target_1 in content:
    content = content.replace(target_1, replacement_1, 1)

if target_2 in content:
    content = content.replace(target_2, replacement_2, 1)
elif target_2_alt in content:
    content = content.replace(target_2_alt, replacement_2_alt, 1)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Kayar Pencere (Sliding Window) canlı koda başarıyla işlendi.")