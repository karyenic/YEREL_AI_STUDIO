import os

html_path = os.path.join("static", "index.html")

html_content = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GK YEREL AI</title>
    <style>
        :root {
            /* KOYU TEMA (DARK) */
            --bg-body: #0f0f13;
            --text-body: #e0e0e0;
            --text-muted: #999;
            --bg-sidebar: #14141c;
            --border-color: #3f3f4e;
            --bg-hist-item: #1e1e26;
            --bg-hist-active: #2b6e9e;
            --bg-input-field: #1e1e26;
            --border-input: #5a5a6e;
            --bg-topbar: #14141c;
            --bg-chatbox: #0f0f13;
            --bg-msg-user: #1e4a6b;
            --text-msg-user: #ffffff;
            --bg-msg-assistant: #22222b;
            --text-msg-assistant: #e0e0e0;
            --bg-input-area: #15151b;
            --bg-prompt-field: #181820;
            --text-prompt-field: #ffffff;
        }

        body.dim-theme {
            /* LOŞ TEMA (DIM) */
            --bg-body: #22252b;
            --text-body: #e6e8eb;
            --text-muted: #a0a5b1;
            --bg-sidebar: #1b1e23;
            --border-color: #454a54;
            --bg-hist-item: #2c3038;
            --bg-hist-active: #3b82f6;
            --bg-input-field: #2c3038;
            --border-input: #5c6370;
            --bg-topbar: #1b1e23;
            --bg-chatbox: #22252b;
            --bg-msg-user: #2563eb;
            --text-msg-user: #ffffff;
            --bg-msg-assistant: #2d323b;
            --text-msg-assistant: #e6e8eb;
            --bg-input-area: #1b1e23;
            --bg-prompt-field: #2a2e37;
            --text-prompt-field: #ffffff;
        }

        body.light-theme {
            /* AÇIK TEMA (LIGHT) */
            --bg-body: #f2f2f5;
            --text-body: #1a1a1e;
            --text-muted: #6b6b70;
            --bg-sidebar: #ffffff;
            --border-color: #c0c0ca;
            --bg-hist-item: #f0f0f3;
            --bg-hist-active: #2b6e9e;
            --bg-input-field: #ffffff;
            --border-input: #888898;
            --bg-topbar: #ffffff;
            --bg-chatbox: #f2f2f5;
            --bg-msg-user: #2b6e9e;
            --text-msg-user: #ffffff;
            --bg-msg-assistant: #ffffff;
            --text-msg-assistant: #1a1a1e;
            --bg-input-area: #ffffff;
            --bg-prompt-field: #f0f0f4;
            --text-prompt-field: #1a1a1e;
        }

        * { margin:0; padding:0; box-sizing:border-box; font-family:system-ui; font-size:1.05rem; }
        body { background:var(--bg-body); color:var(--text-body); height:100vh; overflow:hidden; transition: background 0.2s ease, color 0.2s ease; }

        #sidebar {
            width:300px; position:fixed; top:0; left:0; height:100vh; z-index:100;
            background:var(--bg-sidebar); border-right:2px solid var(--border-color);
            display:flex; flex-direction:column; padding:16px; overflow-y:auto;
        }
        #newChatBtn { padding:10px; background:#2b6e9e; border:none; border-radius:40px; color:white; font-weight:bold; cursor:pointer; margin-bottom:12px; font-size:1.05rem; }
        #modelSelect { width:100%; background:var(--bg-input-field); border:2px solid var(--border-input); color:var(--text-body); padding:8px 12px; border-radius:14px; font-size:0.95rem; margin-bottom:10px; }

        #historyList { flex:1; overflow-y:auto; }
        .hist-item { display:flex; justify-content:space-between; align-items:center; padding:10px 12px; margin:5px 0; background:var(--bg-hist-item); border-radius:12px; cursor:pointer; font-size:0.95rem; border:2px solid var(--border-color); }
        .hist-item.active { background:var(--bg-hist-active); border-color:#3b82f6; color:#ffffff; }
        .hist-item .last-msg { font-size:0.75rem; color:var(--text-muted); margin-top:2px; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; max-width:180px; }
        .hist-item .del { background:none; border:none; color:#ff8888; cursor:pointer; font-size:0.9rem; padding:0 4px; }

        /* SOL MENÜDEKİ YANIP SÖNME EFEKTİ (BLINK) */
        @keyframes hist-blink {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; background-color: #2b6e9e; color: #ffffff; transform: scale(1.02); }
        }
        .hist-item.blink-effect { animation: hist-blink 0.6s ease-in-out 3; }

        #main { margin-left:300px; display:flex; flex-direction:column; height:100vh; }
        #topbar { padding:12px 20px; background:var(--bg-topbar); border-bottom:2px solid var(--border-color); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
        .right-tools { display:flex; align-items:center; gap:8px; }

        #statusBar { display:flex; gap:6px; align-items:center; }
        .status-pill { font-size:0.8rem; padding:4px 12px; border-radius:20px; font-weight:bold; display:inline-flex; align-items:center; gap:5px; background:#1e4a3a; color:#7de3b3; }
        .status-pill::before { content:'●'; font-size:0.7rem; color:#34c77a; }

        #chatBox { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:16px; scroll-behavior:smooth; background:var(--bg-chatbox); }
        .msg-wrapper { display:flex; flex-direction:column; max-width:80%; }
        .msg-wrapper.user { align-self:flex-end; align-items:flex-end; }
        .msg-wrapper.assistant { align-self:flex-start; align-items:flex-start; }
        .msg-wrapper.system { align-self:center; align-items:center; max-width:90%; }

        /* MODEL ROZETİ VE SAAT DAMGASI */
        .model-badge { font-size:0.8rem; padding:3px 10px; border-radius:12px; margin-bottom:4px; font-weight:bold; background:#1e4a3a; color:#7de3b3; display:inline-block; }
        .msg-wrapper.user .model-badge { background:#1e4a6b; color:#ffffff; }

        .msg { padding:14px 18px; border-radius:18px; word-wrap:break-word; font-size:1.05rem; white-space:pre-wrap; border: 2px solid var(--border-input); box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
        .user .msg { background:var(--bg-msg-user); color:var(--text-msg-user); border-color:#3b82f6; }
        .assistant .msg { background:var(--bg-msg-assistant); color:var(--text-msg-assistant); }
        .system .msg { background:#2a2a35; color:#e0e0e0; font-size:0.9rem; text-align:center; }

        .chat-time { font-size:0.7rem; color:var(--text-muted); margin-top:4px; text-align:right; }

        #inputArea { padding:16px; background:var(--bg-input-area); border-top:2px solid var(--border-color); display:flex; flex-direction:column; gap:12px; }
        .input-row { display:flex; gap:12px; align-items:flex-end; }
        
        #prompt { 
            flex:1; 
            background:var(--bg-prompt-field); 
            border:2px solid var(--border-input); 
            border-radius:16px; 
            padding:14px; 
            color:var(--text-prompt-field); 
            resize:vertical; 
            font-size:1.1rem; 
            min-height: 140px; 
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.25);
        }
        #prompt:focus { border-color: #3b82f6; outline: none; }

        button { background:#2b6e9e; border:none; border-radius:40px; color:white; padding:0 20px; height:44px; cursor:pointer; font-weight:bold; font-size:1rem; }
        button:disabled { opacity:0.6; cursor:not-allowed; }
        button.stop-btn { background:#c0392b !important; }
    </style>
</head>
<body>
<div id="sidebar">
    <h2>💬 Sohbetler</h2>
    <button id="newChatBtn">+ Yeni Sohbet</button>
    <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:4px;">Model seç</div>
    <select id="modelSelect">
        <option value="auto">🤖 Auto (Akıllı Seçim)</option>
        <option value="qwen2.5:7b">🖥️ qwen2.5:7b</option>
        <option value="qwen2.5-coder:7b">🖥️ qwen2.5-coder:7b</option>
        <option value="gemini-2.5-flash">☁️ Gemini 2.5 Flash</option>
    </select>
    <div id="historyList"></div>
</div>
<div id="main">
    <div id="topbar">
        <div style="display:flex; align-items:center; gap:10px;">
            <span id="chatTitle" style="font-weight:bold;">Sohbet</span>
        </div>
        <div class="right-tools">
            <div id="statusBar">
                <span class="status-pill">🖥️ Ollama</span>
                <span class="status-pill">☁️ Gemini</span>
            </div>
            <button id="themeToggle">🌙 Koyu</button>
            <button id="shutdownBtn" style="background:#c0392b; color:white; border:none; border-radius:4px; padding:6px 12px; cursor:pointer;">⏻ Çıkış</button>
        </div>
    </div>
    <div id="chatBox"></div>
    <div id="inputArea">
        <div class="input-row">
            <textarea id="prompt" placeholder="Mesaj yaz... (Enter gönder, Shift+Enter satır atlar)"></textarea>
            <button id="sendBtn">Gönder</button>
        </div>
    </div>
</div>

<script>
let themeMode = 'dark';
let isPending = false;
let activeController = null;

let conversations = {};
let currentConvId = null;
let nextId = 1;

const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('sendBtn');
const chatBox = document.getElementById('chatBox');
const themeToggle = document.getElementById('themeToggle');
const modelSelect = document.getElementById('modelSelect');
const newChatBtn = document.getElementById('newChatBtn');
const historyList = document.getElementById('historyList');

function getTimestamp() {
    const now = new Date();
    return now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}

function saveLocal() {
    try {
        localStorage.setItem('convs', JSON.stringify(conversations));
        localStorage.setItem('currentId', currentConvId);
        localStorage.setItem('nextId', nextId);
    } catch(e){}
}

function loadLocal() {
    try {
        const saved = localStorage.getItem('convs');
        if (saved) {
            conversations = JSON.parse(saved);
            currentConvId = localStorage.getItem('currentId');
            nextId = parseInt(localStorage.getItem('nextId')) || 1;
        }
    } catch(e){}
    if (!currentConvId || !conversations[currentConvId]) {
        createNewChat();
    } else {
        renderHistory();
        renderChat();
    }
}

function createNewChat() {
    const m = modelSelect ? modelSelect.value : 'auto';
    const id = String(nextId++);
    conversations[id] = {
        model: m,
        messages: [{ role: 'system', content: 'Sistem: Yeni sohbet başladı.', time: getTimestamp() }]
    };
    currentConvId = id;
    saveLocal();
    renderHistory();
    renderChat();
}

function renderHistory() {
    if (!historyList) return;
    historyList.innerHTML = '';
    for (let id in conversations) {
        const conv = conversations[id];
        const div = document.createElement('div');
        div.className = 'hist-item' + (id === currentConvId ? ' active' : '') + (conv.isFinished ? ' blink-effect' : '');

        if (conv.isFinished) {
            setTimeout(() => { conv.isFinished = false; }, 2000);
        }

        const lastMsg = conv.messages[conv.messages.length - 1]?.content || 'Yeni Sohbet';
        let snippet = lastMsg.length > 25 ? lastMsg.substring(0, 25) + '…' : lastMsg;

        div.innerHTML = `
            <div style="display:flex; flex-direction:column;">
                <strong>${conv.model}</strong>
                <span class="last-msg">${snippet}</span>
            </div>
            <button class="del" onclick="event.stopPropagation(); deleteChat('${id}')">🗑️</button>
        `;

        div.onclick = () => {
            currentConvId = id;
            saveLocal();
            renderHistory();
            renderChat();
        };
        historyList.appendChild(div);
    }
}

function deleteChat(id) {
    delete conversations[id];
    const keys = Object.keys(conversations);
    currentConvId = keys.length ? keys[0] : null;
    saveLocal();
    if (!currentConvId) createNewChat();
    else { renderHistory(); renderChat(); }
}

function renderChat() {
    if (!chatBox || !currentConvId || !conversations[currentConvId]) return;
    const conv = conversations[currentConvId];
    chatBox.innerHTML = '';

    conv.messages.forEach(msg => {
        const wrap = document.createElement('div');
        wrap.className = 'msg-wrapper ' + msg.role;

        let badge = '';
        if (msg.role === 'user') badge = '<div class="model-badge">GÜVEN</div>';
        else if (msg.role === 'assistant') badge = '<div class="model-badge">' + (msg.model || conv.model) + '</div>';

        wrap.innerHTML = badge + '<div class="msg">' + msg.content + '<div class="chat-time">' + (msg.time || '') + '</div></div>';
        chatBox.appendChild(wrap);
    });
    chatBox.scrollTop = chatBox.scrollHeight;
}

// TEMA DÖNGÜSÜ
if (themeToggle) {
    themeToggle.onclick = () => {
        document.body.classList.remove('dim-theme', 'light-theme');
        if (themeMode === 'dark') {
            themeMode = 'dim';
            document.body.classList.add('dim-theme');
            themeToggle.innerText = '🌗 Loş';
        } else if (themeMode === 'dim') {
            themeMode = 'light';
            document.body.classList.add('light-theme');
            themeToggle.innerText = '☀️ Açık';
        } else {
            themeMode = 'dark';
            themeToggle.innerText = '🌙 Koyu';
        }
    };
}

async function sendMessage() {
    const text = promptEl ? promptEl.value.trim() : '';
    if (!text || isPending) return;

    const conv = conversations[currentConvId];
    const time = getTimestamp();

    conv.messages.push({ role: 'user', content: text, time: time });
    promptEl.value = '';
    renderChat();

    isPending = true;
    sendBtn.innerText = '🔴 Durdur';
    sendBtn.classList.add('stop-btn');

    const assistantEntry = { role: 'assistant', content: '⏳ Düşünüyor...', time: getTimestamp(), model: conv.model };
    conv.messages.push(assistantEntry);
    renderChat();

    activeController = new AbortController();

    try {
        // Düzgün Türkçe kuralı enjekte ediliyor
        const systemPrompt = "Lütfen yanıtını yalnızca düzgün ve akıcı bir Türkçe ile ver. Başka dillerde veya yabancı karakterlerde yanıt verme.";
        const fullPrompt = systemPrompt + "\\n\\nKullanıcı: " + text;

        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: fullPrompt, model: conv.model, history: [] }),
            signal: activeController.signal
        });

        if (!res.ok) throw new Error('Sunucu Hatası');

        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        assistantEntry.content = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            const lines = chunk.split('\\n');
            for (let line of lines) {
                if (!line.trim()) continue;
                try {
                    const parsed = JSON.parse(line);
                    if (parsed.type === 'chunk') {
                        assistantEntry.content += parsed.text;
                        renderChat();
                    }
                } catch(e){}
            }
        }
        conv.isFinished = true; // Sol menüde Blink tetikleme
    } catch(e) {
        if (e.name === 'AbortError') assistantEntry.content += '\\n[Yanıt Durduruldu]';
        else assistantEntry.content = 'Yanıt alınırken bir hata oluştu.';
    } finally {
        isPending = false;
        sendBtn.innerText = 'Gönder';
        sendBtn.classList.remove('stop-btn');
        saveLocal();
        renderHistory();
        renderChat();
    }
}

if (sendBtn) sendBtn.onclick = () => { if (isPending && activeController) activeController.abort(); else sendMessage(); };
if (promptEl) promptEl.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };
if (newChatBtn) newChatBtn.onclick = () => createNewChat();

loadLocal();
</script>
</body>
</html>"""

os.makedirs("static", exist_ok=True)
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ İŞLEM TAMAM: Arayüz, sol sütun geçmişi, rozetler ve Türkçe kuralı başarıyla güncellendi!")