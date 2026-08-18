import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Rol Seçici Arayüz Bileşeni (HTML)
    role_select_html = """
        <select id="roleSelect" class="form-select form-select-sm ms-2" style="max-width: 170px; background-color: var(--bg-input-field); color: var(--text-body); border-color: var(--border-color);">
            <option value="default">🌐 Genel Yardımcı</option>
            <option value="coder">💻 Yazılım Mimarı</option>
            <option value="writer">📝 Teknik Yazar</option>
            <option value="analyst">📊 Veri Analisti</option>
        </select>
    """

    # modelSelect öğesinin yanına yerleştirme
    if 'id="roleSelect"' not in content:
        if 'id="modelSelect"' in content:
            content = re.sub(r'(<select[^>]*id="modelSelect"[^>]*>[\s\S]*?</select>)', r'\1' + role_select_html, content)

    # 2. Rol Tanımları ve Sistem İstemcisi Mantığı (JS)
    role_js = """
    // System Prompt / Rol Tanımları
    const SYSTEM_ROLES = {
        default: "",
        coder: "Sen kıdemli bir yazılım mimarısın. Yanıtlarında temiz, optimize edilmiş, güvenli kod yazımına ve mimari açıklamalara öncelik ver.",
        writer: "Sen teknik metin yazarı ve akademisyensin. Dilin net, ölçülü, dilbilgisi kurallarına tam uygun ve açıklayıcı olmalıdır.",
        analyst: "Sen kıdemli bir veri analistisin. Yanıtlarını mantıksal adımlara böl, metodolojik ve analitik bir yaklaşımla sun."
    };

    function getSelectedSystemPrompt() {
        const roleElem = document.getElementById('roleSelect');
        if (!roleElem) return "";
        return SYSTEM_ROLES[roleElem.value] || "";
    }
"""

    if "const SYSTEM_ROLES =" not in content:
        if "</script>" in content:
            content = content.replace("</script>", role_js + "\n</script>", 1)

    # 3. İsteğe `system` Parametresinin Güvenli Eklenmesi
    # Post body içindeki json payload'a ekleme
    if "system: getSelectedSystemPrompt()" not in content:
        content = content.replace(
            "const body = hasImages",
            "const systemPrompt = getSelectedSystemPrompt();\n        const body = hasImages"
        )
        content = content.replace(
            ": { prompt: userMsg, model, history };",
            ": { prompt: userMsg, model, history, system: systemPrompt };"
        )
        content = content.replace(
            ": { prompt: userMsg, model, images: imagesToSend, history };",
            ": { prompt: userMsg, model, images: imagesToSend, history, system: systemPrompt };"
        )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Rol Seçici (System Prompt) modülü sıfır riskle entegre edildi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")