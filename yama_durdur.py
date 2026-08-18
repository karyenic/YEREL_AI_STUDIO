import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Kırmızı Durdur Butonu CSS
    stop_css = """
/* Durdur Butonu Stili */
.btn-stop {
    background-color: #ef4444 !important;
    color: #ffffff !important;
    border-color: #dc2626 !important;
}
.btn-stop:hover {
    background-color: #dc2626 !important;
}
"""
    if "</style>" in content and ".btn-stop" not in content:
        content = content.replace("</style>", stop_css + "\n</style>")

    # 2. Durdurma Mantığı JS
    stop_js = """
<script>
let globalAbortController = null;

function setGeneratingState(isGenerating) {
    const sendBtn = document.getElementById('send-btn') || document.querySelector('button[onclick*="send"]');
    if (!sendBtn) return;

    if (isGenerating) {
        sendBtn.dataset.origText = sendBtn.innerHTML;
        sendBtn.innerHTML = "🔴 Durdur";
        sendBtn.classList.add('btn-stop');
        sendBtn.onclick = function(e) {
            e.preventDefault();
            if (globalAbortController) {
                globalAbortController.abort();
                globalAbortController = null;
            }
            setGeneratingState(false);
        };
    } else {
        sendBtn.innerHTML = sendBtn.dataset.origText || "Gönder";
        sendBtn.classList.remove('btn-stop');
        sendBtn.onclick = null; // Varsayılan form/click fonksiyonuna döner
    }
}
</script>
"""
    if "</body>" in content and "setGeneratingState" not in content:
        content = content.replace("</body>", stop_js + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Durdur butonu altyapısı eklendi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")