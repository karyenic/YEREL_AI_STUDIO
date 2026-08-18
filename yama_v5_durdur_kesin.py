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

    # 2. AbortController Değişkeni
    if "let currentAbortController = null;" not in content:
        content = content.replace("let currentImages = [],", "let currentAbortController = null;\n    let currentImages = [],")

    # 3. Dynamic Button State (Durdur Butonunu Tıklanabilir Yapma)
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
    content = re.sub(r'function updateSendButtonState\(\)\s*\{[\s\S]*?\}', new_btn_state.strip(), content)

    # 4. Gönder/Durdur Tıklama Tetikleyicisi
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
    content = re.sub(r'sendBtn\.onclick\s*=\s*\(\)\s*=>\s*sendMessage\(\);', new_click.strip(), content)

    # 5. Fetch Sinyal İletimi ve Abort Başlatma
    if "currentAbortController = new AbortController();" not in content:
        content = content.replace(
            "conv.pending = true;",
            "conv.pending = true;\n        currentAbortController = new AbortController();"
        )

    if "signal: currentAbortController.signal" not in content:
        content = re.sub(
            r'body:\s*JSON\.stringify\(body\)',
            'body: JSON.stringify(body),\n                signal: currentAbortController.signal',
            content
        )

    if "currentAbortController = null;" not in content:
        content = content.replace(
            "conv.pending = false;",
            "currentAbortController = null;\n            conv.pending = false;"
        )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Durdur (Abort) düğmesi kilitlenmeyecek şekilde tam entegre edildi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")