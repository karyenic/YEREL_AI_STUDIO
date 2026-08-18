import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Üst Bara Gelecek Rol Seçici Dropdown HTML
    topbar_role_html = """
        <select id="topbarRoleSelect" class="form-select form-select-sm me-2" style="width: auto; max-width: 175px; background-color: var(--bg-input-field, #282c38); color: var(--text-body, #ffffff); border: 1px solid var(--border-color, #383e50); font-size: 0.82rem; font-weight: 500; cursor: pointer;">
            <option value="default">🎯 Rol: Genel</option>
            <option value="coder">💻 Rol: Yazılım Mimarı</option>
            <option value="writer">📝 Rol: Teknik Yazar</option>
            <option value="analyst">📊 Rol: Veri Analisti</option>
        </select>
    """

    # 2. Sol Menüye Yönlendirme İkazı
    sidebar_note_html = """
        <div style="font-size: 0.73rem; color: var(--text-muted, #888d9a); margin-top: 4px; margin-bottom: 10px; opacity: 0.85;">
            💡 <i>Rol seçimi üst bardadır ↗️</i>
        </div>
    """

    # Topbar yerleşimi (Ollama/Status rozetlerinin hemen soluna)
    if 'id="topbarRoleSelect"' not in content:
        if 'id="ollamaStatus"' in content:
            content = content.replace('id="ollamaStatus"', 'id="ollamaStatus"' if False else topbar_role_html + '\n<span id="ollamaStatus"')
        elif 'Ollama' in content:
            content = re.sub(r'(<[^>]*>(?: O|O)llama[\s\S]*?</[^>]*>)', topbar_role_html + r'\1', content, count=1)

    # Sol panel yönlendirme etiketi yerleşimi (modelSelect altına)
    if 'Rol seçimi üst bardadır' not in content and 'id="modelSelect"' in content:
        content = re.sub(
            r'(<select[^>]*id="modelSelect"[^>]*>[\s\S]*?</select>)',
            r'\1\n' + sidebar_note_html,
            content
        )

    # 3. Bağımsız JS Rol Mantığı
    role_js = """
    const SYSTEM_ROLES = {
        default: "",
        coder: "Sen kıdemli bir yazılım mimarısın. Yanıtlarında temiz, optimize edilmiş, güvenli kod yazımına ve mimari açıklamalara öncelik ver.",
        writer: "Sen teknik metin yazarı ve akademisyensin. Dilin net, ölçülü ve dilbilgisine tam uygun olsun.",
        analyst: "Sen kıdemli bir veri analistisin. Yanıtlarını mantıksal adımlara böl, analitik yaklaşımla sun."
    };

    function getSelectedRolePrompt() {
        const el = document.getElementById('topbarRoleSelect');
        return el ? (SYSTEM_ROLES[el.value] || "") : "";
    }
"""

    if "const SYSTEM_ROLES =" not in content and "</script>" in content:
        content = content.replace("</script>", role_js + "\n</script>", 1)

    # 4. Fetch Payload Entegrasyonu (Sadece system parametresi ekler)
    if "system: getSelectedRolePrompt()" not in content:
        content = content.replace(
            ": { prompt: userMsg, model, history };",
            ": { prompt: userMsg, model, history, system: getSelectedRolePrompt() };"
        )
        content = content.replace(
            ": { prompt: userMsg, model, images: imagesToSend, history };",
            ": { prompt: userMsg, model, images: imagesToSend, history, system: getSelectedRolePrompt() };"
        )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Sağ üst bar Rol Seçici ve Sol Panel Yönlendirmesi eklendi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")