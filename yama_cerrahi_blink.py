import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Yalnızca sol listedeki aktif öğeyi hedefleyen CSS
    sidebar_flash_css = """
/* Sadece Sol Liste Aktif Kart İkazı */
#historyList .hist-item.active.sidebar-flash {
    animation: sidebarFlashAnim 0.6s ease-in-out 2 !important;
}
@keyframes sidebarFlashAnim {
    0%, 100% { background-color: var(--bg-hist-active, #2b6e9e); }
    50% { background-color: #10b981; }
}
"""
    if "</style>" in content and "sidebarFlashAnim" not in content:
        content = content.replace("</style>", sidebar_flash_css + "\n</style>")

    # 2. Yanıt tamamlandığında strictly #historyList çalıştıran tetikleyici
    flash_js = """
        // Yanıt bittiğinde sadece sol listedeki aktif kartı parlatır
        const activeSidebarItem = document.querySelector('#historyList .hist-item.active');
        if (activeSidebarItem) {
            activeSidebarItem.classList.remove('sidebar-flash');
            void activeSidebarItem.offsetWidth;
            activeSidebarItem.classList.add('sidebar-flash');
            setTimeout(() => activeSidebarItem.classList.remove('sidebar-flash'), 1200);
        }
"""

    # V5'in sendMessage içindeki finally bloğunda renderHistory() sonrasına ekleme
    if "renderHistory();" in content and "activeSidebarItem" not in content:
        # sendMessage içindeki son renderHistory çağrısını bulup altına ekliyoruz
        target = "if (convId === currentConvId) { renderChat(); updateSendButtonState(); }"
        content = content.replace(target, target + flash_js)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ Cerrahi Blink yaması uygulandı.")
    else:
        print("❌ HATA: Ekleme noktası bulunamadı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")