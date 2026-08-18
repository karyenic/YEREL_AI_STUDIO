import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Kırmızı Durdur Butonu CSS'i
    stop_css = """
/* Durdur Butonu Stili */
.btn-stop {
    background-color: #ef4444 !important;
    color: #ffffff !important;
}
.btn-stop:hover {
    background-color: #dc2626 !important;
}
"""
    if "</style>" in content and ".btn-stop" not in content:
        content = content.replace("</style>", stop_css + "\n</style>")

    # 2. AbortController Değişkeni Tanımlama
    if "let currentAbortController = null;" not in content:
        content = content.replace("let currentImages = [],", "let currentAbortController = null;\n    let currentImages = [],")

    # 3. Button Durumu Güncelleyici (updateSendButtonState)
    old_btn_state = """function updateSendButtonState() {
        const conv = conversations[currentConvId];
        const pending = !!(conv && conv.pending);
        sendBtn.disabled = pending;
        sendBtn.textContent = pending ? 'Düşünüyor...' : 'Gönder';
    }"""

    new_btn_state = """function updateSendButtonState() {
        const conv = conversations[currentConvId];
        const pending = !!(conv && conv.pending);
        if (pending) {
            sendBtn.disabled = false;
            sendBtn.textContent = '🔴 Durdur';
            sendBtn.classList.add('btn-stop');
        } else {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Gönder';
            sendBtn.classList.remove('btn-stop');
        }
    }"""

    if old_btn_state in content:
        content = content.replace(old_btn_state, new_btn_state)

    # 4. Gönder Butonu Tıklama Mantığı
    old_click = "sendBtn.onclick = () => sendMessage();"
    new_click = """sendBtn.onclick = () => {
        const conv = conversations[currentConvId];
        if (conv && conv.pending) {
            if (currentAbortController) {
                currentAbortController.abort();
            }
        } else {
            sendMessage();
        }
    };"""

    if old_click in content:
        content = content.replace(old_click, new_click)

    # 5. Fetch Sinyal Bağlantısı
    old_fetch_body = "const body = hasImages\n            ? { prompt: userMsg, model, images: imagesToSend, history }\n            : { prompt: userMsg, model, history };"
    
    new_fetch_body = """const body = hasImages
            ? { prompt: userMsg, model, images: imagesToSend, history }
            : { prompt: userMsg, model, history };

        currentAbortController = new AbortController();"""

    if old_fetch_body in content and "currentAbortController = new AbortController();" not in content:
        content = content.replace(old_fetch_body, new_fetch_body)

    # 6. Fetch İsteğine signal Ekleme
    old_fetch_call = "body: JSON.stringify(body)"
    new_fetch_call = "body: JSON.stringify(body),\n                signal: currentAbortController.signal"

    if old_fetch_call in content and "signal:" not in content:
        content = content.replace(old_fetch_call, new_fetch_call)

    # 7. Finally Bloğunda AbortController Sıfırlama
    old_finally = "conv.pending = false;"
    new_finally = "currentAbortController = null;\n            conv.pending = false;"

    if old_finally in content and "currentAbortController = null;" not in content:
        content = content.replace(old_finally, new_finally)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ V5 Akışına Uyumlu Durdur (Abort) Düğmesi Yüklendi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")