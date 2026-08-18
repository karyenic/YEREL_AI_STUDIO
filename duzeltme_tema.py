import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. CSS Değişkenleri ve Temaların Netleştirilmesi
    tema_css = """
/* 3'lü Tema Stilleri */
body.dim-theme {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
}
body.dim-theme .sidebar, body.dim-theme #sidebar {
    background-color: #0f172a !important;
}
body.dim-theme .chat-container, body.dim-theme .main-content {
    background-color: #1e293b !important;
}

body.light-theme {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}
body.light-theme .sidebar, body.light-theme #sidebar {
    background-color: #e2e8f0 !important;
}
body.light-theme .chat-container, body.light-theme .main-content {
    background-color: #ffffff !important;
}
</style>"""

    if "</style>" in content and "body.dim-theme {" not in content:
        content = content.replace("</style>", tema_css)

    # 2. Eskimiş toggleTheme fonksiyonunu yenisiyle ezme
    yeni_js = """
function toggleTheme() {
    const body = document.body;
    let btn = document.getElementById('theme-btn') || document.querySelector('[onclick*="toggleTheme"]');
    
    if (!body.classList.contains('dim-theme') && !body.classList.contains('light-theme')) {
        body.classList.add('dim-theme');
        if (btn) btn.innerHTML = '🌗 Tema (Loş)';
    } else if (body.classList.contains('dim-theme')) {
        body.classList.remove('dim-theme');
        body.classList.add('light-theme');
        if (btn) btn.innerHTML = '☀️ Tema (Açık)';
    } else {
        body.classList.remove('light-theme');
        if (btn) btn.innerHTML = '🌙 Tema (Koyu)';
    }
}
"""
    # Eğer eski toggleTheme varsa onu değiştir, yoksa script kapanışının hemen üstüne ekle
    if "function toggleTheme()" in content:
        content = re.sub(r'function toggleTheme\(\)\s*\{[\s\S]*?\}', yeni_js, content)
    else:
        content = content.replace("</script>", yeni_js + "\n</script>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Tema Düzeltmesi Yapıldı: 3'lü Tema Döngüsü bağlandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")