import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Sol menüdeki öğeye blink efekti sınıfını ekle
    old_code = "div.className = 'hist-item'"
    new_code = "div.className = 'hist-item' + (conv.isJustFinished ? ' blink-effect' : '')"
    
    if old_code in content and "blink-effect" not in content:
        content = content.replace(old_code, new_code)
        
        # Blink CSS kuralını ekle
        css_blink = """
        @keyframes hist-blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; background-color: #2b6e9e; color: #ffffff; }
        }
        .hist-item.blink-effect { animation: hist-blink 0.6s ease-in-out 3; }
        """
        content = content.replace("</style>", css_blink + "\n</style>")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ yama.py: Orijinal HTML korundu, sol menü blink efekti eklendi!")
    else:
        print("ℹ️ Dosya zaten orijinal veya yama önceden uygulanmış.")