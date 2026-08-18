import io
import os
import sys
import time
import json
import atexit
import base64
import threading
import subprocess
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
import ollama
from openpyxl import Workbook

# -------------------------------------------------
# 1. ORTAM VE DOSYA YOLLARI
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# GPU (Intel Arc 140V vb.) Sürücü Desteği - Olursa kullanır, olmazsa es geçer
os.environ['OLLAMA_IGPU_ENABLE'] = '1'

app = Flask(__name__, static_folder='static')
CORS(app, expose_headers=['X-Saved-Filename'])

EXCELS_DIR = os.path.join(BASE_DIR, 'excels')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(EXCELS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# -------------------------------------------------
# 2. MODEL CONTEXT VE DONANIM AYARLARI
# -------------------------------------------------
MODEL_CTX = {
    "qwen2.5:7b": 8192,
    "qwen2.5-coder:7b": 12288,
    "qwen2.5-hermes:latest": 8192,
    "gemma4:latest": 8192,
    "llama3.1:latest": 8192,
    "deepseek-r1:7b": 4096,
    "qwen2.5:3b": 4096,
    "llama3.2:3b": 4096,
    "gemma2:2b": 4096,
    "deepseek-r1:1.5b": 4096,
    "moondream:latest": 2048,
    "granite3.2-vision:2b": 2048,
}
DEFAULT_CTX = 4096

def get_num_ctx(model: str) -> int:
    if model in MODEL_CTX:
        return MODEL_CTX[model]
    m = model.lower()
    if "coder" in m: return 12288
    if "deepseek-r1" in m and ("7b" in m or "8b" in m): return 4096
    if any(x in m for x in ["1.5b", "2b", "3b"]): return 4096
    if "vision" in m or "moondream" in m: return 2048
    return DEFAULT_CTX

# -------------------------------------------------
# 3. OLLAMA VE GEMINI İSTEMCİLERİ
# -------------------------------------------------
OLLAMA_HOST = 'http://127.0.0.1:11434'
ollama_client = ollama.Client(host=OLLAMA_HOST, timeout=300)
ollama_status_client = ollama.Client(host=OLLAMA_HOST, timeout=8)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
CLOUD_MODELS = {}
gemini_client = None

if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        CLOUD_MODELS['gemini-2.5-flash'] = 'gemini-2.5-flash'
        print("[GK AI] Gemini bulut baglantisi hazir.")
    except Exception as e:
        print(f"[GK AI] Gemini baglanti uyarisi: {e}")

def is_cloud_model(model): return model in CLOUD_MODELS
def is_vision_capable(model): return any(k in model.lower() for k in ('vision', 'moondream')) or is_cloud_model(model)

def is_ollama_running():
    try:
        ollama_status_client.list()
        return True
    except Exception:
        return False

def start_ollama():
    if is_ollama_running(): return
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        subprocess.Popen(['ollama', 'serve'], creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(15):
            time.sleep(0.5)
            if is_ollama_running(): return
    except Exception: pass

def stop_ollama():
    try:
        os.system("taskkill /F /IM ollama.exe /T >nul 2>&1")
        os.system("taskkill /F /IM ollama_llama_server.exe /T >nul 2>&1")
    except Exception: pass

atexit.register(stop_ollama)

# -------------------------------------------------
# 4. SYSTEM PROMPTLAR VE AKILLI ROTALAMA
# -------------------------------------------------
MASTER_SYSTEM_PROMPT = (
    "Sen, adı Güven olan bir kullanıcıyla, onun kendi bilgisayarında çalışan yerel bir "
    "yapay zeka asistanısın. Güven, Dell 16250 Plus model bir dizüstü bilgisayar kullanıyor "
    "ve seninle bu cihaz üzerinde kurulu 'GK YEREL AI' adlı uygulama üzerinden sohbet "
    "ediyor; yani bu bir bulut hizmeti değil, onun kendi makinesinde çalışan özel bir kurulum. "
    "Güven, bilgisayar ve Android mobil cihazlar konusunda amatör/sıradan bir kullanıcıdır; "
    "teknik terimleri gereksiz yere kullanmadan, sade ve anlaşılır bir dille yardımcı ol. "
    "Onunla HER ZAMAN yarı profesyonel, saygılı ve akıcı bir Türkçe ile konuş."
)

LANGUAGE_RULE = " ÖNEMLİ DİL KURALI: Cevabının TAMAMINI, baştan sona, akıcı ve doğru dilbilgisi kurallarına uygun TÜRKÇE yaz."
RESPONSE_STYLE_RULE = " YANIT TARZI KURALLARI: (1) KISA VE ÖZ OL. (2) KLİŞE TEKRARI YAPMA. (3) KOD BLOĞU KURALI: Kod istendiğinde kod bloğunda ver."

CODE_KEYWORDS = ('python', 'kod', 'script', 'fonksiyon', 'html', 'css', 'javascript', 'bug', 'flask', 'yazılım', 'yaz')
REASONING_KEYWORDS = ('neden', 'kanıtla', 'adım adım', 'mantık', 'karşılaştır', 'analiz et', 'hesapla', 'ispat')
WEB_TRIGGER_KEYWORDS = ('güncel', 'araştır', 'webde ara', 'son durum', 'haberler', 'fiyatı', 'bugün')

DEFAULT_MODEL = "qwen2.5:7b"

def resolve_auto_model(prompt: str, has_images: bool = False) -> str:
    p = prompt.lower()
    if has_images or any(k in p for k in ('görsel', 'resim', 'fotoğraf', 'tabloyu oku')):
        return 'moondream:latest'
    if any(k in p for k in CODE_KEYWORDS):
        return 'qwen2.5-coder:7b'
    if any(k in p for k in REASONING_KEYWORDS):
        return 'deepseek-r1:7b'
    return DEFAULT_MODEL

def build_system_prompt(model=None):
    today = datetime.now().strftime('%d.%m.%Y')
    return MASTER_SYSTEM_PROMPT + LANGUAGE_RULE + RESPONSE_STYLE_RULE + f" Bugünün tarihi: {today}."

# -------------------------------------------------
# 5. MODEL AKIŞLARI VE GÖREV DEVRİ
# -------------------------------------------------
def format_gemini_contents(prompt, images=None, history=None):
    from google.genai import types
    contents = []
    for h in (history or []):
        role = 'user' if h.get('role') == 'user' else 'model'
        text_content = h.get('content', '')
        if text_content: contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text_content)]))
    current_parts = [types.Part.from_text(text=prompt)]
    if images:
        for img_b64 in images:
            current_parts.append(types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type='image/png'))
    contents.append(types.Content(role='user', parts=current_parts))
    return contents

def _stream_ollama(model, prompt, images, history):
    messages = [{'role': 'system', 'content': build_system_prompt(model=model)}]
    for h in (history or []):
        if h.get('role') in ('user', 'assistant'):
            messages.append({'role': h.get('role'), 'content': h.get('content', '')})
    current_msg = {'role': 'user', 'content': prompt}
    if images: current_msg['images'] = images
    messages.append(current_msg)
    
    if not is_ollama_running(): start_ollama()

    # GPU KORUMALI ÇAĞRI: Önce varsayılan ayarlarla dener, hata alırsa GPU parametresiz CPU'ya düşer
    try:
        stream = ollama_client.chat(
            model=model, messages=messages, keep_alive='30m',
            options={'num_ctx': get_num_ctx(model)}, stream=True
        )
        for chunk in stream:
            piece = chunk['message']['content']
            if piece: yield piece
    except Exception as e:
        print(f"[Ollama İkaz] Standart akış başarısız, sadeleştirilmiş moda geçiliyor: {e}")
        stream = ollama_client.chat(model=model, messages=messages, stream=True)
        for chunk in stream:
            piece = chunk['message']['content']
            if piece: yield piece

def _stream_gemini(model, prompt, images, history):
    if not GEMINI_API_KEY or not gemini_client: raise RuntimeError("Gemini istemcisi aktif değil.")
    from google.genai import types
    system_prompt = build_system_prompt(model=model)
    contents = format_gemini_contents(prompt, images=images, history=history)
    config = types.GenerateContentConfig(system_instruction=system_prompt)
    response_stream = gemini_client.models.generate_content_stream(model=CLOUD_MODELS[model], contents=contents, config=config)
    for chunk in response_stream:
        if getattr(chunk, 'text', None): yield chunk.text

def _stream_gemini_search(prompt, history=None):
    if not GEMINI_API_KEY or not gemini_client: raise RuntimeError("Gemini istemcisi aktif değil.")
    from google.genai import types
    system_prompt = build_system_prompt(model='gemini-2.5-flash')
    contents = format_gemini_contents(prompt, history=history)
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
    response_stream = gemini_client.models.generate_content_stream(model='gemini-2.5-flash', contents=contents, config=config)
    for chunk in response_stream:
        if getattr(chunk, 'text', None): yield chunk.text

def stream_from_model(model, prompt, images=None, history=None):
    prompt_lower = prompt.lower()
    
    # AJAN HİBRİT AKIŞI: Güncel web araması gerekiyorsa
    if any(kw in prompt_lower for kw in WEB_TRIGGER_KEYWORDS) and GEMINI_API_KEY and gemini_client and model != 'arastirma:gemini-search':
        yield "🌐 *[GK AI Ajanı]: Canlı web verileri için Gemini Google Search kullanılıyor...*\n\n"
        web_facts = ""
        try:
            for chunk in _stream_gemini_search(f"En güncel verileri bul: {prompt}", history=history):
                web_facts += chunk
        except Exception:
            web_facts = "(Canlı web verisi alınamadı, yerel bilgilerle devam ediliyor.)"

        enriched_prompt = (
            f"KULLANICI İSTEĞİ: {prompt}\n\n"
            f"GOOGLE SEARCH CANLI BİLGİLERİ:\n{web_facts}\n\n"
            f"TALİMAT: Bu canlı verileri kullanarak istenen cevabı/tabloyu/sunumu eksiksiz oluştur."
        )
        if is_cloud_model(model):
            yield from _stream_gemini(model, enriched_prompt, images, history)
        else:
            yield from _stream_ollama(model, enriched_prompt, images, history)
        return

    if model == 'arastirma:gemini-search':
        yield from _stream_gemini_search(prompt, history)
        return
    if is_cloud_model(model):
        yield from _stream_gemini(model, prompt, images, history)
    else:
        yield from _stream_ollama(model, prompt, images, history)

def stream_chat_response(prompt, model, images, history):
    def event_stream():
        try:
            gen = stream_from_model(model, prompt, images=images, history=history)
            first_piece = next(gen)
        except StopIteration:
            first_piece = ''
            gen = iter([])
        except Exception as e:
            yield json.dumps({'type': 'error', 'message': f"Model Hatası ({model}): {e}"}, ensure_ascii=False) + '\n'
            return

        yield json.dumps({'type': 'meta', 'model': model, 'fallback': False}, ensure_ascii=False) + '\n'
        if first_piece: yield json.dumps({'type': 'chunk', 'text': first_piece}, ensure_ascii=False) + '\n'

        try:
            for piece in gen: yield json.dumps({'type': 'chunk', 'text': piece}, ensure_ascii=False) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'message': f'Akış kesildi: {e}'}, ensure_ascii=False) + '\n'
            return

        yield json.dumps({'type': 'done'}, ensure_ascii=False) + '\n'

    return Response(event_stream(), mimetype='application/x-ndjson')

# -------------------------------------------------
# 6. ROUTER VE SERVİSLER
# -------------------------------------------------
@app.route('/')
def index(): return send_from_directory('static', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model') or DEFAULT_MODEL
    history = data.get('history', [])
    if not prompt: return jsonify({'error': 'Boş mesaj'}), 400
    if model == 'auto':
        model = resolve_auto_model(prompt, has_images=False)
    return stream_chat_response(prompt, model, images=None, history=history)

@app.route('/chat-multi-image', methods=['POST'])
def chat_multi_image():
    data = request.get_json() or {}
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model', 'moondream:latest')
    images = data.get('images', [])
    history = data.get('history', [])
    if not images: return jsonify({'error': 'Görsel bulunamadı'}), 400
    if model == 'auto':
        model = resolve_auto_model(prompt, has_images=True)
    return stream_chat_response(
        prompt or 'Bu görsel(ler) hakkında detaylı yorum yap.',
        model, images=images, history=history
    )

@app.route('/image-to-excel', methods=['POST'])
def image_to_excel():
    data = request.get_json() or {}
    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'error': 'Görsel bulunamadı.'}), 400

    table_prompt = "Bu görseldeki tabloyu satır ve sütunlarını '|' karakteri ile ayırarak net bir tablo olarak yaz."
    try:
        res = ollama_client.chat(
            model='moondream:latest',
            messages=[{'role': 'user', 'content': table_prompt, 'images': [image_b64]}]
        )
        result_text = res['message']['content']
    except Exception as e:
        return jsonify({'error': f'Görsel işlenemedi: {e}'}), 500

    wb = Workbook()
    ws = wb.active
    for line in result_text.strip().splitlines():
        if '|' in line:
            cells = [c.strip() for c in line.strip('|').split('|')]
            if any(cells): ws.append(cells)

    filename = f"tablo_{int(time.time())}.xlsx"
    filepath = os.path.join(EXCELS_DIR, filename)
    wb.save(filepath)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = send_file(buffer, as_attachment=True, download_name="tablo.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response.headers['X-Saved-Filename'] = filename
    return response

@app.route('/status', methods=['GET'])
def status():
    ollama_ok = is_ollama_running()
    if not ollama_ok:
        start_ollama()
        ollama_ok = is_ollama_running()
        
    return jsonify({
        'ollama': ollama_ok,
        'gemini': bool(GEMINI_API_KEY and gemini_client)
    })

@app.route('/models', methods=['GET'])
def list_models():
    local_models = []
    try:
        response = ollama_status_client.list()
        local_models = [m.model for m in response.models]
    except Exception:
        local_models = ['qwen2.5:7b', 'qwen2.5-coder:7b', 'llama3.2:3b', 'moondream:latest']

    clouds = ['gemini-2.5-flash'] if (GEMINI_API_KEY and gemini_client) else []
    research_list = ['arastirma:gemini-search'] if (GEMINI_API_KEY and gemini_client) else []
    return jsonify({'local': ['auto'] + local_models, 'cloud': clouds, 'research': research_list, 'skills': []})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)