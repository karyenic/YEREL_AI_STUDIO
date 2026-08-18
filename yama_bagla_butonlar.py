import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Asistan mesaj balonlarına butonları otomatik ekleyen script
    attach_script = """
<script>
function attachMiniButtons() {
    // Model/Asistan yanıt balonlarını hedefler
    const botBubbles = document.querySelectorAll('.bot, .assistant, [data-role="assistant"], .message-bubble:not(.user)');
    botBubbles.forEach(bubble => {
        if (!bubble.querySelector('.msg-actions') && bubble.innerText.trim().length > 0) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'msg-actions';
            actionsDiv.innerHTML = `
                <button class="msg-action-btn" onclick="copyMsgText(this)">📋 Kopyala</button>
                <button class="msg-action-btn" onclick="downloadMsgText(this)">💾 İndir (.txt)</button>
            `;
            bubble.appendChild(actionsDiv);
        }
    });
}

// Balonlar oluştukça butonları otomatik bağla
setInterval(attachMiniButtons, 1000);
</script>
"""
    if "</body>" in content and "attachMiniButtons" not in content:
        content = content.replace("</body>", attach_script + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Mini Kopyala/İndir düğmeleri asistan mesajlarına bağlandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")