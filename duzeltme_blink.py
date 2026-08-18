import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Sadece sol sütun (sidebar) içerisindeki aktif kartı hedefleyen fonksiyon
    yeni_blink_js = """
function triggerSidebarBlink() {
    const sidebar = document.querySelector('.sidebar') || document.querySelector('#sidebar') || document.querySelector('aside') || document.querySelector('.left-panel');
    if (!sidebar) return;
    
    const activeChat = sidebar.querySelector('.active');
    if (activeChat) {
        activeChat.classList.remove('hist-blink');
        void activeChat.offsetWidth; // Reflow tetikleme
        activeChat.classList.add('hist-blink');
    }
}
"""

    if "function triggerSidebarBlink()" in content:
        content = re.sub(r'function triggerSidebarBlink\(\)\s*\{[\s\S]*?\}', yeni_blink_js.strip(), content)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Blink efekti sadece sol panele sabitlendi.")
    else:
        print("❌ HATA: triggerSidebarBlink fonksiyonu bulunamadı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")