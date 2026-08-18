import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. V5'in Titremesiz Yanıt ve Yeşil Bildirim CSS'i
    v5_css = """
/* V5 Yanıt Bildirim Animasyonu */
@keyframes newReplyPulse {
    0%, 100% { background: var(--bg-hist-item, #1e1e26); box-shadow: none; }
    50% { background: #1c3d2a; box-shadow: 0 0 0 2px rgba(52, 199, 122, 0.35); }
}
.hist-item.new-reply, .chat-history-item.new-reply {
    animation: newReplyPulse 1.1s ease-in-out 3;
}
"""
    if "</style>" in content and "newReplyPulse" not in content:
        content = content.replace("</style>", v5_css + "\n</style>")

    # 2. V5'in Titremeyi Engelleyen updateStreamingBubble Fonksiyonu
    v5_js = """
// V5 Titremesiz Canlı Akış Güncelleyicisi
function updateStreamingBubble(conv) {
    const wrapper = document.getElementById('pendingWrapper');
    const content = document.getElementById('pendingContent');
    if (!wrapper || !content) {
        if (typeof renderChat === 'function') renderChat();
        return;
    }
    if (conv && conv.streamingText) {
        content.textContent = conv.streamingText;
    }
    const chatBox = document.getElementById('chatBox') || document.querySelector('.chat-container');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}
"""
    if "</script>" in content and "updateStreamingBubble" not in content:
        content = content.replace("</script>", v5_js + "\n</script>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ V5 Hibrit Yaması Başarıyla Uygulandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")