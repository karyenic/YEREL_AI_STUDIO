import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Mini Buton Stilleri
    btn_css = """
/* Mini Kopyala ve İndir Buton Stilleri */
.msg-actions {
    display: flex;
    gap: 6px;
    margin-top: 6px;
    justify-content: flex-end;
}
.msg-action-btn {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #e2e8f0;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
}
.msg-action-btn:hover {
    background: rgba(255, 255, 255, 0.25);
    color: #ffffff;
}
"""
    if "</style>" in content and ".msg-action-btn" not in content:
        content = content.replace("</style>", btn_css + "\n</style>")

    # 2. Kopyala ve İndir Fonksiyonları
    btn_js = """
<script>
function copyMsgText(btn) {
    const msgContainer = btn.closest('.message-bubble') || btn.closest('.chat-bubble') || btn.parentElement.parentElement;
    if (!msgContainer) return;
    
    // Buton metinlerini ve tarihleri süzerek temiz metni al
    const clone = msgContainer.cloneNode(true);
    const actions = clone.querySelector('.msg-actions');
    if (actions) actions.remove();
    
    const textToCopy = clone.innerText.trim();
    navigator.clipboard.writeText(textToCopy).then(() => {
        const orig = btn.innerText;
        btn.innerText = "✓ Kopyalandı";
        setTimeout(() => btn.innerText = orig, 1500);
    });
}

function downloadMsgText(btn) {
    const msgContainer = btn.closest('.message-bubble') || btn.closest('.chat-bubble') || btn.parentElement.parentElement;
    if (!msgContainer) return;
    
    const clone = msgContainer.cloneNode(true);
    const actions = clone.querySelector('.msg-actions');
    if (actions) actions.remove();
    
    const textToDownload = clone.innerText.trim();
    const blob = new Blob([textToDownload], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `yanit_${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
}
</script>
"""
    if "</body>" in content and "copyMsgText" not in content:
        content = content.replace("</body>", btn_js + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Mini Kopyala/İndir altyapısı eklendi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")