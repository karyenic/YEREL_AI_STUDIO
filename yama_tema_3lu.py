import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Dim (Loş) Tema CSS Tanımı
    dim_css = """
        body.dim-theme {
            --bg-body: #1a1c23;
            --text-body: #d5d8e1;
            --text-muted: #888d9a;
            --bg-sidebar: #20232d;
            --border-color: #313543;
            --bg-hist-item: #282c38;
            --bg-hist-active: #2b6e9e;
            --bg-input-field: #282c38;
            --border-input: #383e50;
            --bg-topbar: #20232d;
            --bg-chatbox: #1a1c23;
            --bg-msg-user: #23527a;
            --text-msg-user: #ffffff;
            --bg-msg-assistant: #282c38;
            --text-msg-assistant: #d5d8e1;
            --bg-msg-system: #422d2d;
            --text-msg-system: #f5a996;
            --bg-input-area: #20232d;
            --bg-prompt-field: #15171e;
            --text-prompt-field: #ffffff;
            --bg-preview: #15171e;
        }
"""
    if "</style>" in content and "dim-theme" not in content:
        content = content.replace("</style>", dim_css + "\n</style>")

    # 2. 3'lü Tema Değişim Mantığı (Dark -> Dim -> Light -> Dark)
    old_theme_js = r'themeToggle\.onclick\s*=\s*\(\)\s*=>\s*\{[\s\S]*?\};'
    
    new_theme_js = """
    const themes = ['dark', 'dim', 'light'];
    const themeLabels = { dark: '🌙 Koyu', dim: '🕯️ Loş', light: '☀️ Açık' };

    function applyTheme(themeName) {
        document.body.classList.remove('dim-theme', 'light-theme');
        if (themeName === 'dim') document.body.classList.add('dim-theme');
        if (themeName === 'light') document.body.classList.add('light-theme');
        themeToggle.innerHTML = themeLabels[themeName] || '🌓 Tema';
        localStorage.setItem('theme', themeName);
    }

    themeToggle.onclick = () => {
        let current = localStorage.getItem('theme') || 'dark';
        let nextIndex = (themes.indexOf(current) + 1) % themes.length;
        applyTheme(themes[nextIndex]);
    };

    // Sayfa ilk yüklendiğinde hafızadaki temayı uygula
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
"""

    if re.search(old_theme_js, content):
        content = re.sub(old_theme_js, new_theme_js.strip(), content)
        
        # Eski light-theme kontrol bloğunu pasifleştir
        content = content.replace("if (localStorage.getItem('theme') === 'light')", "if (false)")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ 3'lü Tema Döngüsü (Dark / Dim / Light) Başarıyla Yüklendi.")
    else:
        print("❌ HATA: themeToggle click fonksiyonu bulunamadı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")