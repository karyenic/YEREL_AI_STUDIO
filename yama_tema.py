import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Loş Tema CSS Kuralları
    dim_css = """
/* Loş (Ara) Tema Stilleri */
body.dim-theme {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
}
body.dim-theme .sidebar, body.dim-theme #sidebar {
    background-color: #0f172a !important;
}
body.dim-theme .chat-container, body.dim-theme .main-content, body.dim-theme main {
    background-color: #1e293b !important;
}
body.dim-theme .chat-bubble, body.dim-theme .message-bubble {
    border-color: #475569 !important;
}
"""
    if "</style>" in content and "body.dim-theme" not in content:
        content = content.replace("</style>", dim_css + "\n</style>")

    # 2. Güvenli JS Eklemesi (Sayfa sonuna olay dinleyici ekleme)
    theme_script = """
<script>
document.addEventListener("DOMContentLoaded", function() {
    const themeBtn = document.getElementById('theme-btn') || document.querySelector('[onclick*="toggleTheme"]');
    if (themeBtn) {
        themeBtn.removeAttribute('onclick');
        themeBtn.addEventListener('click', function() {
            const body = document.body;
            if (!body.classList.contains('dim-theme') && !body.classList.contains('light-theme')) {
                // Koyu -> Loş
                body.classList.add('dim-theme');
                themeBtn.innerHTML = '🌗 Tema (Loş)';
            } else if (body.classList.contains('dim-theme')) {
                // Loş -> Açık
                body.classList.remove('dim-theme');
                body.classList.add('light-theme');
                themeBtn.innerHTML = '☀️ Tema (Açık)';
            } else {
                // Açık -> Koyu
                body.classList.remove('light-theme');
                themeBtn.innerHTML = '🌙 Tema (Koyu)';
            }
        });
    }
});
</script>
"""
    if "</body>" in content and "themeBtn.removeAttribute" not in content:
        content = content.replace("</body>", theme_script + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Tema Yaması Uygulandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")