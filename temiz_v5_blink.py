import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Yanıt penceresine bulaşan tüm yapay setInterval ve blink scriptlerini temizle
    content = re.sub(r'<script>\s*function triggerSidebarBlink[\s\S]*?</script>', '', content)
    content = re.sub(r'<script>\s*let wasStreaming[\s\S]*?</script>', '', content)

    # 2. V5'in yerleşik .new-reply animasyonunu sol panel kartlarına tam kilitleme
    clean_css = """
/* V5 Yerleşik Sol Menü Bildirim Animasyonu */
#historyList .hist-item.new-reply, #sidebar .hist-item.new-reply {
    animation: v5SidebarPulse 1s ease-in-out 3 !important;
}
@keyframes v5SidebarPulse {
    0%, 100% { background-color: var(--bg-hist-item, #1e1e26); box-shadow: none; }
    50% { background-color: #1e4a3a; box-shadow: 0 0 0 2px rgba(52, 199, 122, 0.5); }
}
"""
    if "</style>" in content and "v5SidebarPulse" not in content:
        content = content.replace("</style>", clean_css + "\n</style>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Yapay döngüler temizlendi. Sol menü ikazı V5'in yerleşik mekanizmasına bağlandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")