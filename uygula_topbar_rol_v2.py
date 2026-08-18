import os, re

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ HATA: static/index.html bulunamadı!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. "+ Yeni Sohbet" Ekran Sıfırlama Garantisi
if "chatBox.innerHTML = ''" not in content and 'chatBox.innerHTML = ""' not in content:
    content = re.sub(
        r'(function\s+(?:newChat|createNewChat)\s*\([^)]*\)\s*\{)',
        r"\1\n        const chatBox = document.getElementById('chatBox'); if (chatBox) chatBox.innerHTML = '';",
        content,
        count=1
    )

# 2. Topbar Rol Select HTML (Tema Butonunun Soluna)
role_select_html = """<select id="roleSelect" class="form-select form-select-sm" style="width: auto; height: 32px; border-radius: 16px; padding: 0 10px; font-size: 0.81rem; font-weight: 600; background-color: var(--bg-hist-item, #1e222d); color: var(--text-body, #e2e8f0); border: 1px solid var(--border-color, #33394b); margin-right: 8px;">
        <option value="default">🎯 Rol: Genel</option>
        <option value="coder">💻 Rol: Yazılım Mimarı</option>
        <option value="writer">📝 Rol: Teknik Yazar</option>
        <option value="analyst">📊 Rol: Veri Analisti</option>
    </select>\n        """

if 'id="roleSelect"' not in content:
    content = re.sub(
        r'(<button[^>]*id="themeToggle"[^>]*>)',
        role_select_html + r'\1',
        content,
        count=1
    )

# 3. System Prompt Tanımı ve İsteğe Ekleme JS
system_role_js = """
    // System Prompt / Rol Tanımları
    const SYSTEM_ROLES = {
        default: "",
        coder: "Sen kıdemli bir yazılım mimarısın. Yanıtlarında temiz, optimize edilmiş, güvenli kod yazımına ve mimari açıklamalara öncelik ver.",
        writer: "Sen teknik metin yazarı ve akademisyensin. Dilin net, ölçülü ve dilbilgisine tam uygun olsun.",
        analyst: "Sen kıdemli bir veri analistisin. Yanıtlarını mantıksal adımlara böl, analitik yaklaşımla sun."
    };

    function getSelectedSystemPrompt() {
        const el = document.getElementById('roleSelect');
        return el ? (SYSTEM_ROLES[el.value] || "") : "";
    }
"""

if "const SYSTEM_ROLES =" not in content and "</script>" in content:
    content = content.replace("</script>", system_role_js + "\n</script>", 1)

if "system: getSelectedSystemPrompt()" not in content:
    content = content.replace(
        ": { prompt: userMsg, model, history };",
        ": { prompt: userMsg, model, history, system: getSelectedSystemPrompt() };"
    )
    content = content.replace(
        ": { prompt: userMsg, model, images: imagesToSend, history };",
        ": { prompt: userMsg, model, images: imagesToSend, history, system: getSelectedSystemPrompt() };"
    )

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Onaylanan yapı canlı index.html dosyasına sorunsuz işlendi.")