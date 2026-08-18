import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Tam ortada duran Slate Gray (Mavi-Gri) Loş Tema CSS
    better_dim_css = """
        body.dim-theme {
            --bg-body: #22272e;
            --text-body: #adbac7;
            --text-muted: #768390;
            --bg-sidebar: #1c2128;
            --border-color: #373e47;
            --bg-hist-item: #2d333b;
            --bg-hist-active: #2b6e9e;
            --bg-input-field: #2d333b;
            --border-input: #444c56;
            --bg-topbar: #1c2128;
            --bg-chatbox: #22272e;
            --bg-msg-user: #1f4e7d;
            --text-msg-user: #ffffff;
            --bg-msg-assistant: #2d333b;
            --text-msg-assistant: #adbac7;
            --bg-msg-system: #442d2d;
            --text-msg-system: #f5a996;
            --bg-input-area: #1c2128;
            --bg-prompt-field: #22272e;
            --text-prompt-field: #adbac7;
            --bg-preview: #22272e;
        }
"""
    # Eski dim-theme CSS bloğunu yenisiyle değiştir
    if "body.dim-theme {" in content:
        content = re.sub(r'body\.dim-theme\s*\{[\s\S]*?\}', better_dim_css.strip(), content)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Loş tema renkleri orta ton Slate Gray olarak güncellendi.")
    else:
        print("❌ HATA: dim-theme tanımı bulunamadı.")
else:
    print("❌ HATA: static/index.html bulunamadı!")