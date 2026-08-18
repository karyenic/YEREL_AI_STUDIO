import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. "Model seç" etiketine doğrudan belirgin stil verme
    content = content.replace(
        'Model seç',
        '<span style="color:#ffffff !important; font-weight:700 !important; font-size:0.95rem !important;">Model seç</span>'
    )

    # 2. Tarih ve Saat damgası fontunu büyütme
    content = content.replace('font-size:0.7rem;', 'font-size:0.88rem; font-weight:500;')
    content = content.replace('font-size: 0.7rem;', 'font-size: 0.88rem; font-weight: 500;')
    content = content.replace('font-size:0.75rem;', 'font-size:0.88rem; font-weight:500;')

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Görsel yama uygulandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")