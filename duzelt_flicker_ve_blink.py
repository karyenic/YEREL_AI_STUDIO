import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Yanıt penceresini sürekli titreten CSS animasyonunu kaldırıyoruz
    content = content.replace("animation: fadeInUp 0.25s ease;", "/* animation disabled */")
    content = content.replace("animation:fadeInUp 0.25s ease;", "/* animation disabled */")

    # 2. Yanıt alanına bulaşan tüm eski script/döngü parçalarını temizliyoruz
    content = re.sub(r'<script>\s*function triggerSidebarBlink[\s\S]*?</script>', '', content)
    content = re.sub(r'<script>\s*let wasStreaming[\s\S]*?</script>', '', content)

    # 3. YALNIZCA sol menüdeki aktif sohbet kartına özel, 1 saniyelik temiz yeşil ikaz
    strict_sidebar_css = """
/* SADECE SOL MENÜ AKTİF SOHBET KARTINA ÖZEL İKAZ */
#historyList .hist-item.active.card-pulse {
    animation: sidebarPulseAnim 0.6s ease-in-out 2 !important;
}
@keyframes sidebarPulseAnim {
    0%, 100% { background-color: var(--bg-hist-active, #2b6e9e); }
    50% { background-color: #059669; }
}
"""
    if "</style>" in content and "sidebarPulseAnim" not in content:
        content = content.replace("</style>", strict_sidebar_css + "\n</style>")

    # 4. Yanıt bittiğinde sadece sol menüdeki ilgili karta uygulanacak JS
    sidebar_js = """
<script>
function triggerSidebarBlink() {
    const activeItem = document.querySelector('#historyList .hist-item.active');
    if (activeItem) {
        activeItem.classList.remove('card-pulse');
        void activeItem.offsetWidth;
        activeItem.classList.add('card-pulse');
        setTimeout(() => activeItem.classList.remove('card-pulse'), 1300);
    }
}
</script>
"""
    if "</script>" in content and "function triggerSidebarBlink()" not in content:
        content = content.replace("</script>", sidebar_js + "\n</script>")

    # 5. Yanıt tamamlandığında fonksiyonu tek bir noktadan çağırma
    target_code = "addMessageTo(convId, 'assistant', accumulated, finalModel, finalFallback, finalRequestedModel);"
    if target_code in content and "triggerSidebarBlink();" not in content:
        content = content.replace(target_code, target_code + "\n            triggerSidebarBlink();")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Yanıt penceresindeki titreme animasyonu silindi, blink sadece sol menüye sabitlendi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")