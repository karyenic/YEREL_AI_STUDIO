import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Rol Seçici Arayüz Bileşeni (Sol Panelde Şık Etiketli Düzgün Düzen)
    role_html = """
        <div class="mt-2 mb-2">
            <label class="form-label text-muted small mb-1" style="font-size: 0.78rem;">Rol seç</label>
            <select id="roleSelect" class="form-select form-select-sm" onchange="if(conversations[currentConvId] && conversations[currentConvId].messages.length===0) renderChat();" style="background-color: var(--bg-input-field); color: var(--text-body); border-color: var(--border-color);">
                <option value="default">🌐 Genel Yardımcı</option>
                <option value="coder">💻 Yazılım Mimarı</option>
                <option value="writer">📝 Teknik Yazar</option>
                <option value="analyst">📊 Veri Analisti</option>
            </select>
        </div>
    """

    if 'id="roleSelect"' not in content:
        content = re.sub(
            r'(<select[^>]*id="modelSelect"[^>]*>[\s\S]*?</select>)',
            r'\1\n' + role_html,
            content
        )

    # 2. System Prompts & Rol Tanımları JS
    role_js = """
    const SYSTEM_ROLES = {
        default: "",
        coder: "Sen kıdemli bir yazılım mimarısın. Yanıtlarında temiz, optimize edilmiş, güvenli kod yazımına ve mimari açıklamalara öncelik ver.",
        writer: "Sen teknik metin yazarı ve akademisyensin. Dilin net, ölçülü ve dilbilgisine tam uygun olsun.",
        analyst: "Sen kıdemli bir veri analistisin. Yanıtlarını mantıksal adımlara böl, analitik yaklaşımla sun."
    };

    function getSelectedSystemPrompt() {
        const roleElem = document.getElementById('roleSelect');
        return roleElem ? (SYSTEM_ROLES[roleElem.value] || "") : "";
    }
    """
    if "const SYSTEM_ROLES =" not in content and "</script>" in content:
        content = content.replace("</script>", role_js + "\n</script>", 1)

    # 3. İsteğe `system` parametresi ekleme
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

    # 4. Boş Sohbet Ekranına "Muhatap Kartı" Ekleme (renderChat() Başlangıcına)
    welcome_card_js = """
        if (conv.messages.length === 0) {
            const roleElem = document.getElementById('roleSelect');
            const roleLabel = roleElem ? roleElem.options[roleElem.selectedIndex].text : '🌐 Genel Yardımcı';
            const modelLabel = document.getElementById('modelSelect')?.value || 'Model';
            
            chatBox.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60%; opacity: 0.85; text-align: center;">
                    <div style="font-size: 2.2rem; margin-bottom: 8px;">🤖</div>
                    <h5 style="margin-bottom: 6px; color: var(--text-body); font-weight: 600;">Yeni Sohbet Hazır</h5>
                    <div style="font-size: 0.85rem; color: var(--text-muted); background: var(--bg-hist-item); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border-color); display: inline-block;">
                        Muhatap: <strong style="color: #60a5fa;">${modelLabel}</strong> &nbsp;|&nbsp; Rol: <strong style="color: #34d399;">${roleLabel}</strong>
                    </div>
                </div>
            `;
            return;
        }
    """

    if "renderChat()" in content and "Yeni Sohbet Hazır" not in content:
        content = re.sub(
            r'(function renderChat\(\)\s*\{[\s\S]*?const conv = conversations\[currentConvId\];[^\n]*)',
            r'\1\n' + welcome_card_js,
            content
        )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Arayüz düzenlendi. Yeni Sohbet ve Muhatap Kartı başarıyla eklendi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")