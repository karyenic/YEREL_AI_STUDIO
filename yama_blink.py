import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Blink CSS Animasyonu
    blink_css = """
/* Sol Menü Blink Efekti */
@keyframes histBlink {
  0% { opacity: 1; background-color: rgba(59, 130, 246, 0.4); }
  50% { opacity: 0.3; background-color: rgba(59, 130, 246, 0.8); }
  100% { opacity: 1; background-color: transparent; }
}
.hist-blink {
  animation: histBlink 0.6s ease-in-out 3 !important;
}
"""
    if "</style>" in content and ".hist-blink" not in content:
        content = content.replace("</style>", blink_css + "\n</style>")

    # 2. Yanıt Bittiğinde Blink Tetikleme Mantığı
    blink_js = """
<script>
function triggerSidebarBlink() {
    const activeChat = document.querySelector('.chat-history-item.active') || 
                       document.querySelector('.history-item.active') || 
                       document.querySelector('.sidebar .active') ||
                       document.querySelector('[data-chat-id].active');
    if (activeChat) {
        activeChat.classList.remove('hist-blink');
        void activeChat.offsetWidth; // Reflow tetikleme
        activeChat.classList.add('hist-blink');
    }
}

// Model yanıt üretmeyi bitirdiğinde otomatik blink tetikler
let wasStreaming = false;
setInterval(() => {
    const isStreaming = document.querySelector('.streaming, .typing, .loading');
    if (isStreaming) {
        wasStreaming = true;
    } else if (wasStreaming) {
        wasStreaming = false;
        triggerSidebarBlink();
    }
}, 500);
</script>
"""
    if "</body>" in content and "triggerSidebarBlink" not in content:
        content = content.replace("</body>", blink_js + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Blink ikaz sistemi sol panele bağlandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")