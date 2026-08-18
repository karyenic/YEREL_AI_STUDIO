import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Sadece #historyList altındaki aktif mesaja kilitli CSS
    strict_css = """
/* SADECE SOL MENÜDEKİ AKTİF SOHBET KARTINA ÖZEL İKAZ */
#historyList .hist-item.active.blink-active {
    animation: activeCardPulse 0.5s ease-in-out 3 !important;
}
@keyframes activeCardPulse {
    0%, 100% { background-color: var(--bg-hist-active, #2b6e9e); }
    50% { background-color: #059669; }
}
"""
    if "</style>" in content and "activeCardPulse" not in content:
        content = content.replace("</style>", strict_css + "\n</style>")

    # 2. Doğrudan çağrılacak tetikleme fonksiyonu
    blink_func = """
function triggerSidebarBlink() {
    const activeItem = document.querySelector('#historyList .hist-item.active');
    if (activeItem) {
        activeItem.classList.remove('blink-active');
        void activeItem.offsetWidth; // Reflow
        activeItem.classList.add('blink-active');
        setTimeout(() => activeItem.classList.remove('blink-active'), 1600);
    }
}
"""
    if "</script>" in content and "function triggerSidebarBlink()" not in content:
        content = content.replace("</script>", blink_func + "\n</script>")

    # 3. V5'in sendMessage yanıtı tamamlandığı satıra tetikleyiciyi bağlama
    target_code = "addMessageTo(convId, 'assistant', accumulated, finalModel, finalFallback, finalRequestedModel);"
    if target_code in content and "triggerSidebarBlink();" not in content:
        content = content.replace(target_code, target_code + "\n            triggerSidebarBlink();")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Blink efekti doğrudan V5 akışına kilitlendi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")