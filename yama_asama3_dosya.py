import os

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Dosya okuma ve paketleme JavaScript mantığı
    file_packet_script = """
<script>
document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.querySelector('input[type="file"]') || document.getElementById('file-input');
    const textarea = document.querySelector('textarea');

    if (fileInput && textarea) {
        fileInput.addEventListener('change', function(e) {
            const files = e.target.files;
            if (!files || files.length === 0) return;

            Array.from(files).forEach(file => {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    const contentText = evt.target.result;
                    const formattedPacket = `\\n\\n--- DOSYA BAŞLANGICI: ${file.name} ---\\n${contentText}\\n--- DOSYA BİTİŞİ: ${file.name} ---\\n`;
                    
                    textarea.value += formattedPacket;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                };
                reader.readAsText(file);
            });
        });
    }
});
</script>
"""
    if "</body>" in content and "DOSYA BAŞLANGICI" not in content:
        content = content.replace("</body>", file_packet_script + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 3. Aşama (Dosya Paketleme Sistemi) Başarıyla Uygulandı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")