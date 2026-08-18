import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Sol paneldeki "Model seç" yazısını belirginleştirme
    content = content.replace(
        'color:var(--text-muted); margin-bottom:4px;">Model seç',
        'color:var(--text-body); font-weight:600; margin-bottom:6px;">Model seç'
    )
    content = content.replace(
        'color: var(--text-muted); margin-bottom: 4px;">Model seç',
        'color: var(--text-body); font-weight: 600; margin-bottom: 6px;">Model seç'
    )

    # 2. Tarih ve Saat damgası font boyutunu büyütme (0.7rem/0.75rem -> 0.88rem)
    content = content.replace('font-size:0.7rem;', 'font-size:0.88rem; font-weight:500; opacity:0.85;')
    content = content.replace('font-size: 0.7rem;', 'font-size: 0.88rem; font-weight: 500; opacity: 0.85;')
    content = content.replace('font-size:0.75rem;', 'font-size:0.88rem; font-weight:500; opacity:0.85;')

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 1. Aşama Başarıyla Uygulandı: 'Model seç' netleştirildi, Saat/Tarih fontları büyütüldü.")
else:
    print("❌ HATA: static/index.html dosyası bulunamadı!")