import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Yanıt penceresine bulaşan tüm eski blink animasyonlarını ve CSS'leri temizle
    content = re.sub(r'@keyframes\s+(histBlink|sidebarBlinkAnim|sidebarOnlyBlink)\s*\{[\s\S]*?\}', '', content)
    content = re.sub(r'\.hist-blink\s*\{[\s\S]*?\}', '', content)
    content = re.sub(r'#sidebar\s+\.hist-blink[\s\S]*?\}', '', content)

    # 2. Yalnızca Sol Panele Özel Temiz CSS
    sidebar_blink_css = """
/* YALNIZCA SOL MENÜ SOHBET KARTLARI İÇİN BLINK */
#historyList .hist-item.hist-blink, #sidebar .hist-item.hist-blink {
    animation: strictSidebarBlink 0.6s ease-in-out 3 !important;
}
@keyframes strictSidebarBlink {
    0% { background-color: rgba(59, 130, 246, 0.4); }
    50% { background-color: rgba(59, 130, 246, 0.95); }
    100% { background-color: transparent; }
}
"""
    if "</style>" in content:
        content = content.replace("</style>", sidebar_blink_css + "\n</style>")

    # 3. Yalnızca Sol Menüdeki Aktif Öğeyi Bulan Temiz JS
    sidebar_blink_js = """
<script>
function triggerSidebarBlink() {
    // Sadece sol listedeki aktif sohbet kartını hedefle
    const historyList = document.getElementById('historyList') || document.getElementById('sidebar');
    if (!historyList) return;

    const activeCard = historyList.querySelector('.hist-item.active') || historyList.querySelector('.active');
    if (activeCard) {
        activeCard.classList.remove('hist-blink');
        void activeCard.offsetWidth; // Force Reflow
        activeCard.classList.add('hist-blink');
    }
}
</script>
"""
    # Eski triggerSidebarBlink fonksiyonu varsa temizle ve yenisini ekle
    if "function triggerSidebarBlink()" in content:
        content = re.sub(r'<script>\s*function triggerSidebarBlink\(\)[\s\S]*?</script>', '', content)
        content = re.sub(r'function triggerSidebarBlink\(\)\s*\{[\s\S]*?\}', '', content)

    if "</body>" in content:
        content = content.replace("</body>", sidebar_blink_js + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Yanıt penceresindeki tüm animasyonlar temizlendi, blink tamamen sol panele hapsedildi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")