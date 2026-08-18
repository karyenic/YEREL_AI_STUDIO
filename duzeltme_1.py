import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. "Model seç" yazısını doğrudan parlak/net renge zorlama CSS'i
    model_css = """
/* Model Seç Etiketi Netleştirme */
label[for="model-select"], .model-label, label {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    opacity: 1 !important;
    display: block;
    margin-bottom: 6px;
}

/* 3'lü Tema Tanımları */
body.dim-theme {
    --bg-main: #1e293b;
    --bg-sidebar: #0f172a;
    --bg-card: #334155;
    --text-body: #e2e8f0;
    --border-color: #475569;
}
</style>"""

    if "</style>" in content and "dim-theme" not in content:
        content = content.replace("</style>", model_css)

    # 2. HTML içinde "Model seç" kelimesini geçen yeri doğrudan parlak stil ile kaplama
    content = content.replace(
        'Model seç',
        '<span style="color:#ffffff !important; font-weight:700 !important; font-size:0.95rem !important;">Model seç</span>'
    )

    # 3. Tema Butonu 3'lü Döngü JS Mantığı (Koyu 🌙 -> Loş 🌗 -> Açık ☀️)
    theme_js = """
function toggleTheme() {
    const body = document.body;
    const btn = document.getElementById('theme-btn') || document.querySelector('[onclick*="toggleTheme"]');
    
    if (!body.classList.contains('dim-theme') && !body.classList.contains('light-theme')) {
        // Koyu'dan -> Loş'a geçiş
        body.classList.add('dim-theme');
        if (btn) btn.innerHTML = '🌗 Tema (Loş)';
        localStorage.setItem('theme_mode', 'dim');
    } else if (body.classList.contains('dim-theme')) {
        // Loş'tan -> Açık'a geçiş
        body.classList.remove('dim-theme');
        body.classList.add('light-theme');
        if (btn) btn.innerHTML = '☀️ Tema (Açık)';
        localStorage.setItem('theme_mode', 'light');
    } else {
        // Açık'tan -> Koyu'ya geçiş
        body.classList.remove('light-theme');
        if (btn) btn.innerHTML = '🌙 Tema (Koyu)';
        localStorage.setItem('theme_mode', 'dark');
    }
}
</script>"""

    if "</script>" in content and "theme_mode" not in content:
        content = content.replace("</script>", theme_js)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Düzeltme Uygulandı: 'Model seç' parlatıldı ve 3'lü Tema döngüsü (Koyu/Loş/Açık) bağlandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")