import io
import os
import sys
import time
import json
import atexit
import base64
import threading
import subprocess
import importlib
import importlib.util
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
import ollama
import requests
from pypdf import PdfReader
from openpyxl import Workbook

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app, expose_headers=['X-Saved-Filename'])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLLAMA_NUM_CTX = 8192

EXCELS_DIR = os.path.join(BASE_DIR, 'excels')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(EXCELS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# SKILL SISTEMI - skills/ altindaki her klasordeki .py dosyasini otomatik
# yukler. Her skill modulu SKILL_INFO (sozluk) ve run_skill(model_runner,
# config_path=None) fonksiyonu icermelidir. run_skill, isini yapip sonucu
# string olarak dondurur; model_runner(prompt) cagrisiyla gercek LLM'e
# erisir.
# ---------------------------------------------------------------------------
SKILLS_DIR = os.path.join(BASE_DIR, 'skills')


def discover_skills():
    skills = {}
    if not os.path.isdir(SKILLS_DIR):
        return skills
    for entry in sorted(os.listdir(SKILLS_DIR)):
        skill_path = os.path.join(SKILLS_DIR, entry)
        if not os.path.isdir(skill_path):
            continue
        py_files = [f for f in os.listdir(skill_path) if f.endswith('.py')]
        if not py_files:
            continue
        # Klasorle ayni adli .py dosyasi varsa onu tercih et, yoksa ilkini kullan
        preferred = entry + '.py'
        chosen = preferred if preferred in py_files else py_files[0]
        module_path = os.path.join(skill_path, chosen)
        try:
            spec = importlib.util.spec_from_file_location(f"skills_{entry}", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'run_skill') and hasattr(module, 'SKILL_INFO'):
                skills[entry] = {'info': module.SKILL_INFO, 'run_skill': module.run_skill}
                print(f"[Skill] '{entry}' yuklendi: {module.SKILL_INFO.get('name', entry)}")
            else:
                print(f"[Skill] '{entry}' atlandi - run_skill veya SKILL_INFO eksik.")
        except Exception as e:
            print(f"[Skill] '{entry}' yuklenemedi: {e}")
    return skills


SKILLS = discover_skills()

# code_reviewer skill'i 'kodlar' alt klasorunu bekliyor - yoksa ilk
# calistirmada hata verir, burada guvence altina aliyoruz.
_code_reviewer_kodlar = os.path.join(SKILLS_DIR, 'code_reviewer', 'kodlar')
if os.path.isdir(os.path.join(SKILLS_DIR, 'code_reviewer')):
    os.makedirs(_code_reviewer_kodlar, exist_ok=True)


def make_model_runner(preferred_model=None):
    """Skill'lerin cagirdigi model_runner(prompt) fonksiyonunu olusturur."""
    def runner(prompt):
        model = preferred_model
        if not model:
            available = list_local_models() or PRIORITY_LOCAL
            model = available[0] if available else 'qwen2.5:3b'
        try:
            if is_cloud_model(model):
                return generate_cloud(model, prompt)
            return generate_local(model, prompt)
        except Exception as e:
            return f"Hata: model çalıştırılamadı ({e})"
    return runner

# ---------------------------------------------------------------------------
# STATS & CLOUD USAGE
# ---------------------------------------------------------------------------
STATS_FILE = os.path.join(BASE_DIR, 'model_stats.json')
_stats_lock = threading.Lock()

def _load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_stats(stats):
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Stats] kaydedilemedi: {e}")

def record_response_time(model, seconds):
    with _stats_lock:
        stats = _load_stats()
        entry = stats.get(model, {'count': 0, 'avg_seconds': 0.0})
        count = entry['count'] + 1
        avg = (entry['avg_seconds'] * entry['count'] + seconds) / count
        stats[model] = {'count': count, 'avg_seconds': round(avg, 2)}
        _save_stats(stats)

USAGE_FILE = os.path.join(BASE_DIR, 'cloud_usage.json')
_usage_lock = threading.Lock()

def record_cloud_usage(model):
    today = datetime.now().strftime('%Y-%m-%d')
    with _usage_lock:
        usage = {}
        if os.path.exists(USAGE_FILE):
            try:
                with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                    usage = json.load(f)
            except Exception:
                usage = {}
        day_entry = usage.get(today, {})
        day_entry[model] = day_entry.get(model, 0) + 1
        usage[today] = day_entry
        try:
            with open(USAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(usage, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Kullanım] kaydedilemedi: {e}")

def get_today_cloud_usage():
    today = datetime.now().strftime('%Y-%m-%d')
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                usage = json.load(f)
            return usage.get(today, {})
        except Exception:
            return {}
    return {}

OLLAMA_HOST = 'http://127.0.0.1:11434'
OLLAMA_TIMEOUT = 300
OLLAMA_STATUS_TIMEOUT = 8
OLLAMA_KEEP_ALIVE = '30m'
ollama_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT)
ollama_status_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_STATUS_TIMEOUT)
ollama_process = None

MASTER_SYSTEM_PROMPT = (
    "Sen, adı Güven olan bir kullanıcıyla, onun kendi bilgisayarında çalışan yerel bir "
    "yapay zeka asistanısın. Güven, Dell 16250 Plus model bir dizüstü bilgisayar kullanıyor "
    "ve seninle bu cihaz üzerinde kurulu 'Yerel AI Studio V5' adlı uygulama üzerinden sohbet "
    "ediyor; yani bu bir bulut hizmeti değil, onun kendi makinesinde çalışan özel bir kurulum. "
    "Güven, bilgisayar ve Android mobil cihazlar konusunda amatör/sıradan bir kullanıcıdır; "
    "teknik terimleri gereksiz yere kullanmadan, sade ve anlaşılır bir dille yardımcı ol. "
    "Onunla HER ZAMAN yarı profesyonel, saygılı ve akıcı bir Türkçe ile konuş - resmiyetten "
    "uzak ama özensiz de olmayan bir üslup kullan. Cevaplarını gereksiz uzatma, gerektiğinde "
    "kısa ve net ol; kod veya teknik bir adım istenirse adım adım ve sade bir dille anlat."
)

LANGUAGE_RULE = (
    " ÖNEMLİ DİL KURALI: Cevabının TAMAMINI, baştan sona, akıcı ve doğru dilbilgisi "
    "kurallarına uygun TÜRKÇE yaz. Özne-yüklem uyumuna dikkat et, devrik veya bozuk cümle "
    "kurma. İngilizce kelime veya cümle KESİNLİKLE kullanma; bir terimin Türkçe karşılığı "
    "yoksa önce Türkçe açıklamasını yaz, istersen parantez içinde orijinalini belirt, ama "
    "cümlenin tamamı Türkçe olmalı."
)

RESPONSE_STYLE_RULE = (
    " YANIT TARZI KURALLARI: "
    "(1) KISA VE ÖZ OL: Varsayılan olarak cevabını 2-4 cümle ile sınırla. "
    "(2) KLİŞE TEKRARI YAPMA: Doğrudan konuya/cevaba geç. "
    "(3) KOD BLOĞU KURALI: Kod istendiğinde mutlaka uygun bir kod bloğu içinde ver. "
    "(4) SOHBET PENCERESİNE UYGUN FORMAT: Kısa madde işaretli listeler veya kısa paragraflar tercih et. "
    "(5) BELİRSİZLİKTE TEK SORU SOR: Tek ve net bir netleştirici soru sor. "
    "(6) UYDURMA, DÜRÜST OL: Bilmiyorsan veya emin değilsen bunu açıkça belirt."
)

MEMORY_SCOPE_RULE = (
    " HAFIZA KAPSAMI KURALI: Senin hafızan SADECE bu spesifik sohbet penceresinde "
    "az önce yazılan mesajlarla sınırlıdır. Başka hiçbir sohbeti, projeyi, dosyayı "
    "veya konuşmayı BİLEMEZSİN ve GÖREMEZSİN."
)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()

CLOUD_MODELS = {}
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        CLOUD_MODELS['gemini-2.5-flash'] = 'gemini-2.5-flash'
    except Exception:
        pass

def is_cloud_model(model):
    return model in CLOUD_MODELS

def is_vision_capable(model):
    return any(k in model.lower() for k in ('vision', 'moondream')) or is_cloud_model(model)

def is_ollama_running():
    try:
        ollama_status_client.list()
        return True
    except Exception:
        return False

def start_ollama():
    global ollama_process
    if is_ollama_running():
        return
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        ollama_process = subprocess.Popen(['ollama', 'serve'], creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            time.sleep(0.5)
            if is_ollama_running():
                return
    except Exception:
        pass

def stop_ollama():
    try:
        import os
        os.system("taskkill /F /IM ollama.exe /T >nul 2>&1")
        os.system("taskkill /F /IM ollama_llama_server.exe /T >nul 2>&1")
    except Exception:
        pass

atexit.register(stop_ollama)

def load_json_file(filename, default_data):
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[{filename} Okuma Hatası]: {e}")
    return default_data

def build_system_prompt(model=None):
    today = datetime.now().strftime('%d.%m.%Y')
    if model and is_vision_capable(model) and not is_cloud_model(model) and 'moondream' in model.lower():
        return "Sen Güven abinin yerel asistanısın. Görseli kısa, net ve Türkçe açıkla."

    # prompts.json bulunamazsa veya icinde bir anahtar eksikse, Python
    # icindeki sabit metinler YEDEK olarak kullanilir - boylece dosya
    # bozuk/eksik olsa bile model talimatsiz kalmaz.
    prompts = load_json_file('prompts.json', {})
    master_prompt = prompts.get('master_system_prompt') or MASTER_SYSTEM_PROMPT
    lang_rule = prompts.get('language_rule') or LANGUAGE_RULE
    style_rule = prompts.get('response_style_rule') or RESPONSE_STYLE_RULE
    mem_rule = prompts.get('memory_scope_rule') or MEMORY_SCOPE_RULE

    return master_prompt + lang_rule + style_rule + mem_rule + f" Bugünün tarihi: {today}."

def generate_cloud(model, prompt, images=None, history=None):
    system_prompt = build_system_prompt(model=model)
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini anahtarı yok.")
    try:
        gmodel = genai.GenerativeModel(CLOUD_MODELS[model], system_instruction=system_prompt)
        use_system_instruction = True
    except TypeError:
        gmodel = genai.GenerativeModel(CLOUD_MODELS[model])
        use_system_instruction = False

    contents = []
    for h in (history or []):
        role = 'user' if h.get('role') == 'user' else 'model'
        contents.append({'role': role, 'parts': [h.get('content', '')]})

    current_prompt = prompt
    if not use_system_instruction and not contents:
        current_prompt = system_prompt + "\n\n---\n\nKullanıcının mesajı:\n" + prompt

    current_parts = [current_prompt]
    if images:
        for img_b64 in images:
            current_parts.append({'mime_type': 'image/png', 'data': base64.b64decode(img_b64)})
    contents.append({'role': 'user', 'parts': current_parts})
    return gmodel.generate_content(contents).text

def generate_local(model, prompt, images=None, history=None):
    messages = [{'role': 'system', 'content': build_system_prompt(model=model)}]
    for h in (history or []):
        if h.get('role') in ('user', 'assistant'):
            messages.append({'role': h.get('role'), 'content': h.get('content', '')})
    current_msg = {'role': 'user', 'content': prompt}
    if images:
        current_msg['images'] = images
    messages.append(current_msg)
    if not is_ollama_running():
        start_ollama()
    response = ollama_client.chat(
        model=model, messages=messages, keep_alive=OLLAMA_KEEP_ALIVE,
        options={'num_ctx': OLLAMA_NUM_CTX}
    )
    return response['message']['content']

def _stream_ollama(model, prompt, images, history):
    messages = [{'role': 'system', 'content': build_system_prompt(model=model)}]
    for h in (history or []):
        if h.get('role') in ('user', 'assistant'):
            messages.append({'role': h.get('role'), 'content': h.get('content', '')})
    current_msg = {'role': 'user', 'content': prompt}
    if images:
        current_msg['images'] = images
    messages.append(current_msg)
    if not is_ollama_running():
        start_ollama()
    stream = ollama_client.chat(
        model=model, messages=messages, keep_alive=OLLAMA_KEEP_ALIVE,
        options={'num_ctx': OLLAMA_NUM_CTX}, stream=True
    )
    for chunk in stream:
        piece = chunk['message']['content']
        if piece:
            yield piece

def _stream_gemini(model, prompt, images, history):
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini anahtarı yok.")
    system_prompt = build_system_prompt(model=model)
    try:
        gmodel = genai.GenerativeModel(CLOUD_MODELS[model], system_instruction=system_prompt)
        use_system_instruction = True
    except TypeError:
        gmodel = genai.GenerativeModel(CLOUD_MODELS[model])
        use_system_instruction = False

    contents = []
    for h in (history or []):
        role = 'user' if h.get('role') == 'user' else 'model'
        contents.append({'role': role, 'parts': [h.get('content', '')]})

    current_prompt = prompt
    if not use_system_instruction and not contents:
        current_prompt = system_prompt + "\n\n---\n\nKullanıcının mesajı:\n" + prompt

    current_parts = [current_prompt]
    if images:
        for img_b64 in images:
            current_parts.append({'mime_type': 'image/png', 'data': base64.b64decode(img_b64)})
    contents.append({'role': 'user', 'parts': current_parts})
    stream = gmodel.generate_content(contents, stream=True)
    for chunk in stream:
        if getattr(chunk, 'text', None):
            yield chunk.text

def stream_from_model(model, prompt, images=None, history=None):
    if model.startswith('skill:'):
        skill_key = model[len('skill:'):]
        skill = SKILLS.get(skill_key)
        if not skill:
            raise RuntimeError(f"Skill bulunamadı veya yüklenemedi: {skill_key}")
        runner = make_model_runner()
        result = skill['run_skill'](runner)
        yield result
        return
    if is_cloud_model(model):
        yield from _stream_gemini(model, prompt, images, history)
    else:
        yield from _stream_ollama(model, prompt, images, history)

def stream_chat_response(prompt, model, images, history):
    def event_stream():
        vision_only = bool(images)
        candidates = [model] + build_fallback_candidates(model, vision_only=vision_only)
        tried = []

        for idx, candidate in enumerate(candidates):
            is_primary = (idx == 0)
            tried.append(candidate)
            start_time = time.time()
            try:
                gen = stream_from_model(candidate, prompt, images=images, history=history)
                first_piece = next(gen)
            except StopIteration:
                first_piece = ''
                gen = iter([])
            except Exception as e:
                print(f"[MODEL HATASI] '{candidate}' yanıt veremedi: {e}")
                continue

            meta = {'type': 'meta', 'model': candidate, 'fallback': not is_primary}
            if not is_primary:
                meta['requested_model'] = model
            yield json.dumps(meta, ensure_ascii=False) + '\n'

            if first_piece:
                yield json.dumps({'type': 'chunk', 'text': first_piece}, ensure_ascii=False) + '\n'

            try:
                for piece in gen:
                    yield json.dumps({'type': 'chunk', 'text': piece}, ensure_ascii=False) + '\n'
            except Exception as e:
                print(f"[MODEL HATASI] '{candidate}' akış sırasında kesildi: {e}")
                yield json.dumps({'type': 'error', 'message': f'Yanıt yarıda kesildi: {e}'}, ensure_ascii=False) + '\n'
                return

            record_response_time(candidate, time.time() - start_time)
            if is_cloud_model(candidate):
                record_cloud_usage(candidate)
            yield json.dumps({'type': 'done'}, ensure_ascii=False) + '\n'
            return

        yield json.dumps({
            'type': 'error',
            'message': "Denenen hiçbir model yanıt veremedi (" + ', '.join(tried) + ")."
        }, ensure_ascii=False) + '\n'

    return Response(event_stream(), mimetype='application/x-ndjson')

def list_local_models():
    try:
        response = ollama_status_client.list()
        return [m.model for m in response.models]
    except Exception:
        try:
            output = subprocess.check_output(['ollama', 'list'], text=True, encoding='utf-8')
            lines = output.strip().split('\n')
            models = []
            for line in lines[1:]:
                if line.strip():
                    name = line.split()[0]
                    if name:
                        models.append(name)
            return models
        except Exception as e:
            return PRIORITY_LOCAL

PRIORITY_LOCAL = [
    'qwen2.5-coder:7b',
    'qwen2.5:3b',
    'qwen2.5:7b',
    'llama3.2:3b',
    'gemma2:2b',
    'deepseek-r1:1.5b',
    'moondream:latest',
    'granite3.2-vision:2b',
    'llama3.1:latest'
]

def build_fallback_candidates(failed_model, vision_only=False):
    available = list_local_models()
    if not available:
        available = PRIORITY_LOCAL
    candidates = [m for m in available if m != failed_model]
    if vision_only:
        candidates = [m for m in candidates if is_vision_capable(m)]
    return candidates

# ---------------------------------------------------------------------------
# FLASK ROTARILARI
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model', 'qwen2.5:3b')
    history = data.get('history', [])
    if not prompt:
        return jsonify({'error': 'Boş mesaj'}), 400
    return stream_chat_response(prompt, model, images=None, history=history)

@app.route('/chat-multi-image', methods=['POST'])
def chat_multi_image():
    data = request.get_json()
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model', 'moondream:latest')
    images = data.get('images', [])
    history = data.get('history', [])
    if not images:
        return jsonify({'error': 'Görsel bulunamadı'}), 400
    return stream_chat_response(
        prompt or 'Bu görsel(ler) hakkında detaylı yorum yap.',
        model, images=images, history=history
    )

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    file = request.files['file']
    file_bytes = file.read()
    reader = PdfReader(io.BytesIO(file_bytes))
    full_text = '\n'.join([p.extract_text() or '' for p in reader.pages]).strip()
    return jsonify({'text': full_text, 'pages': len(reader.pages)})

@app.route('/image-to-excel', methods=['POST'])
def image_to_excel():
    data = request.get_json()
    image_b64 = data.get('image')
    model = data.get('model', 'moondream:latest')
    table_prompt = "Bu görseldeki tabloyu hücreleri '|' ile ayırarak yaz."

    candidates = [model] + build_fallback_candidates(model, vision_only=True)
    result_text = None
    for candidate in candidates:
        try:
            if is_cloud_model(candidate):
                result_text = generate_cloud(candidate, table_prompt, images=[image_b64])
            else:
                result_text = generate_local(candidate, table_prompt, images=[image_b64])
            break
        except Exception as e:
            print(f"[MODEL HATASI] '{candidate}' excel donusumunde basarisiz: {e}")
            continue

    if result_text is None:
        return jsonify({'error': 'Hiçbir model görseli işleyemedi.'}), 500

    wb = Workbook()
    ws = wb.active
    for line in result_text.strip().splitlines():
        if line.strip():
            ws.append([c.strip() for c in line.strip('|').split('|')])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="tablo.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

CONVERSATIONS_BACKUP_FILE = os.path.join(BASE_DIR, 'conversations_backup.json')

@app.route('/save-conversations', methods=['POST'])
def save_conversations():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Geçersiz veri'}), 400
    try:
        with open(CONVERSATIONS_BACKUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load-conversations', methods=['GET'])
def load_conversations():
    if not os.path.exists(CONVERSATIONS_BACKUP_FILE):
        return jsonify({'found': False})
    try:
        with open(CONVERSATIONS_BACKUP_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'found': True, 'data': data})
    except Exception as e:
        return jsonify({'found': False, 'error': str(e)})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'ollama': is_ollama_running(),
        'gemini': bool(GEMINI_API_KEY),
        'cloud_usage_today': get_today_cloud_usage()
    })

@app.route('/model-stats', methods=['GET'])
def model_stats():
    return jsonify(_load_stats())

@app.route('/models', methods=['GET'])
def list_models():
    try:
        local_models = list_local_models()
    except Exception as e:
        local_models = PRIORITY_LOCAL

    if not local_models:
        local_models = PRIORITY_LOCAL

    clouds = []
    if GEMINI_API_KEY:
        clouds.append('gemini-2.5-flash')

    skills_list = [
        {
            'key': f'skill:{k}',
            'name': v['info'].get('name', k),
            'description': v['info'].get('description', '')
        }
        for k, v in SKILLS.items()
    ]

    return jsonify({
        'local': local_models,
        'cloud': clouds,
        'research': [],
        'skills': skills_list
    })

@app.route('/warmup', methods=['POST'])
def warmup():
    return jsonify({'status': 'skipped'})

if __name__ == '__main__':
    start_ollama()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)