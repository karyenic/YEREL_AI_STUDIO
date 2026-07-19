import io
import os
import re
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
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from openpyxl import Workbook

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app, expose_headers=['X-Saved-Filename'])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLLAMA_NUM_CTX = 8192  # varsayilan (2048-4096) yerine genis baglam penceresi - gecmis kirpilmasin

# ---------------------------------------------------------------------------
# Model hiz istatistikleri - her modelin ortalama yanit suresini basit bir
# JSON dosyasinda tutar. Tahmine degil, gercek veriye dayali karar vermeyi
# saglar (hangi model gercekten yavas/hizli).
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


# ---------------------------------------------------------------------------
# Bulut kullanim sayaci - Gemini/Kimi'ye gunde kac istek gittigini takip eder,
# kota surprizi yasamamak icin.
# ---------------------------------------------------------------------------
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
            print(f"[Kullanim] kaydedilemedi: {e}")


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
EXCELS_DIR = os.path.join(BASE_DIR, 'excels')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(EXCELS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

OLLAMA_HOST = 'http://127.0.0.1:11434'
OLLAMA_TIMEOUT = 300  
OLLAMA_STATUS_TIMEOUT = 8  
OLLAMA_KEEP_ALIVE = '30m'  
ollama_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT)
ollama_status_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_STATUS_TIMEOUT)
ollama_process = None

_warmup_lock = threading.Lock()
_warmup_in_progress = False

MASTER_SYSTEM_PROMPT = (
    "Sen, adi Guven olan bir kullaniciyla, onun kendi bilgisayarinda calisan yerel bir "
    "yapay zeka asistanisin. Guven, Dell 16250 Plus model bir dizustu bilgisayar kullaniyor "
    "ve seninle bu cihaz uzerinde kurulu 'Yerel AI Studio' adli bir uygulama uzerinden sohbet "
    "ediyor; yani bu bir bulut hizmeti degil, onun kendi makinesinde calisan ozel bir kurulum. "
    "Guven, bilgisayar ve Android mobil cihazlar konusunda amator/siradan bir kullanicidir; "
    "teknik terimleri gereksiz yere kullanmadan, sade ve anlasilir bir dille yardimci ol. "
    "Onunla HER ZAMAN yari profesyonel, saygili ve akici bir Turkce ile konus - resmiyetten "
    "uzak ama ozensiz de olmayan bir uslup kullan. Cevaplarini gereksiz uzatma, gerektiginde "
    "kisa ve net ol; kod veya teknik bir adim istenirse adim adim ve sade bir dille anlat."
)

LANGUAGE_RULE = (
    " ONEMLI DIL KURALI: Cevabinin TAMAMINI, bastan sona, akici ve dogru dilbilgisi "
    "kurallarina uygun TURKCE yaz. Ozne-yuklem uyumuna dikkat et, devrik veya bozuk cumle "
    "kurma. Ingilizce kelime veya cumle KESINLIKLE kullanma; bir terimin Turkce karsiligi "
    "yoksa once Turkce aciklamasini yaz, istersen parantez icinde orijinalini belirt, ama "
    "cumlenin tamami Turkce olmali."
)

RESPONSE_STYLE_RULE = (
    " YANIT TARZI KURALLARI: "
    "(1) KISA VE OZ OL: Varsayilan olarak cevabini 2-4 cumle ile sinirla. "
    "(2) KLISE TEKRARI YAPMA: Doğrudan konuya/cevaba gec. "
    "(3) KOD BLOGU KURALI: Kod istendiginde mutlaka uygun bir kod blogu icinde ver. "
    "(4) SOHBET PENCERESINE UYGUN FORMAT: Kisa madde isaretli listeler veya kisa paragraflar tercih et. "
    "(5) BELIRSIZLIKTE TEK SORU SOR: Tek ve net bir netlestirici soru sor. "
    "(6) UYDURMA, DURUST OL: Bilmiyorsan veya emin degilsen bunu acikca belirt."
)

# Kucuk modeller "hafizan var mi" gibi meta-sorularda kendinden emin sekilde
# uydurma bilgi verebiliyor (ornegin hic bahsi gecmeyen bir proje/dosyayi
# "hatirladigini" iddia etmek gibi). Bunu azaltmak icin acik bir kural.
MEMORY_SCOPE_RULE = (
    " HAFIZA KAPSAMI KURALI: Senin hafizan SADECE bu spesifik sohbet penceresinde "
    "az once yazilan mesajlarla sinirlidir. Baska hicbir sohbeti, projeyi, dosyayi "
    "veya konusmayi BILEMEZSIN ve GORMEZSIN - farkli bir sohbet penceresinde veya "
    "farkli bir zamanda konusulmus olabilecek hicbir seyi 'hatirliyorum' diye iddia "
    "etme. Sadece bu mevcut sohbette gercekten yazilmis olanlari hatirladigini soyle; "
    "emin olmadigin bir 'hatirlama' iddiasinda bulunmaktansa, 'bu konusmada boyle bir "
    "sey gecmedi' demen daha dogrudur."
)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
KIMI_API_KEY = os.environ.get('KIMI_API_KEY', '').strip()

CLOUD_MODELS = {}
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        CLOUD_MODELS['gemini-2.5-flash'] = 'gemini-2.5-flash'
    except Exception: pass

# Kimi modelini OpenAI entegrasyonu ile sisteme tanıtıyoruz
if KIMI_API_KEY:
    CLOUD_MODELS['kimi-k3'] = 'moonshot-v1-8k'  # Kimi entegrasyonu aktif

def is_cloud_model(model): return model in CLOUD_MODELS
def is_vision_capable(model): return any(k in model.lower() for k in ('vision', 'moondream')) or is_cloud_model(model)
def is_ollama_running():
    try:
        ollama_status_client.list()
        return True
    except Exception: return False

def start_ollama():
    global ollama_process
    if is_ollama_running(): return
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        ollama_process = subprocess.Popen(['ollama', 'serve'], creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            time.sleep(0.5)
            if is_ollama_running(): return
    except Exception: pass

def stop_ollama():
    try:
        import os
        os.system("taskkill /F /IM ollama.exe /T >nul 2>&1")
        os.system("taskkill /F /IM ollama_llama_server.exe /T >nul 2>&1")
    except Exception: pass

atexit.register(stop_ollama)

def build_system_prompt(has_internet=False, model=None):
    today = datetime.now().strftime('%d.%m.%Y')
    if model and is_vision_capable(model) and not is_cloud_model(model) and 'moondream' in model.lower():
        return "Sen Guven abinin yerel asistanisin. Gorseli kisa, net ve Turkce acikla."
    prompt = MASTER_SYSTEM_PROMPT + LANGUAGE_RULE + RESPONSE_STYLE_RULE + MEMORY_SCOPE_RULE + f" Bugunun tarihi: {today}."
    if has_internet:
        prompt += (
            " Bu mesaj icin internetten gercek zamanli bir web aramasi yapildi ve sonuclari "
            "sana asagida saglandi; bu bilgileri guncel ve guvenilir kaynak olarak kullanabilirsin."
        )
    else:
        prompt += (
            " Senin gercek zamanli internet erisimin YOKTUR. Guncel bilgi istenirse bunu "
            "bilemeyecegini acikca belirt - asla internete eristigini iddia etme."
        )
    return prompt

def generate_cloud(model, prompt, images=None, history=None, has_internet=False):
    system_prompt = build_system_prompt(has_internet=has_internet, model=model)
    
    # 1. EĞER SEÇİLEN MODEL KİMİ K3 İSE:
    if model == 'kimi-k3':
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KIMI_API_KEY}"
        }
        messages = [{"role": "system", "content": system_prompt}]
        for h in (history or []):
            role = 'user' if h.get('role') == 'user' else 'assistant'
            messages.append({"role": role, "content": h.get('content', '')})
        
        # Görsel desteğini OpenAI standardında paslıyoruz
        current_content = [{"type": "text", "text": prompt}]
        if images:
            for img_b64 in images:
                current_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
        
        messages.append({"role": "user", "content": current_content})
        
        payload = {
            "model": "moonshot-v1-auto", # Kimi K3'ün API ana motoru
            "messages": messages,
            "temperature": 0.3
        }
        resp = requests.post("https://api.moonshot.cn/v1/chat/completions", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
        
    # 2. EĞER SEÇİLEN MODEL GEMINI İSE:
    else:
        if not GEMINI_API_KEY: raise RuntimeError("Gemini anahtari yok.")
        try:
            # Yeni SDK surumleri system_instruction destekler
            gmodel = genai.GenerativeModel(CLOUD_MODELS[model], system_instruction=system_prompt)
            use_system_instruction = True
        except TypeError:
            # Eski SDK surumu system_instruction desteklemiyor; sistem promptunu
            # ilk mesajin basina elle ekleyecegiz (asagida).
            gmodel = genai.GenerativeModel(CLOUD_MODELS[model])
            use_system_instruction = False

        contents = []
        for h in (history or []):
            role = 'user' if h.get('role') == 'user' else 'model'
            contents.append({'role': role, 'parts': [h.get('content', '')]})

        current_prompt = prompt
        if not use_system_instruction and not contents:
            current_prompt = system_prompt + "\n\n---\n\nKullanicinin mesaji:\n" + prompt

        # ONEMLI DUZELTME: gorseller 'contents' listesine degil, mevcut turun
        # 'parts' listesine eklenmeli - yoksa Gemini'ye bozuk istek gider.
        current_parts = [current_prompt]
        if images:
            for img_b64 in images:
                current_parts.append({'mime_type': 'image/png', 'data': base64.b64decode(img_b64)})
        contents.append({'role': 'user', 'parts': current_parts})
        return gmodel.generate_content(contents).text

def generate_local(model, prompt, images=None, history=None, has_internet=False):
    messages = [{'role': 'system', 'content': build_system_prompt(has_internet=has_internet, model=model)}]
    for h in (history or []):
        if h.get('role') in ('user', 'assistant'):
            messages.append({'role': h.get('role'), 'content': h.get('content', '')})
    current_msg = {'role': 'user', 'content': prompt}
    if images: current_msg['images'] = images
    messages.append(current_msg)
    if not is_ollama_running(): start_ollama()
    response = ollama_client.chat(
        model=model, messages=messages, keep_alive=OLLAMA_KEEP_ALIVE,
        options={'num_ctx': OLLAMA_NUM_CTX}
    )
    return response['message']['content']

def web_search(query, max_results=4):
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({'title': r.get('title', ''), 'url': r.get('href', ''), 'snippet': r.get('body', '')})
    except Exception: pass
    return results

def generate_web_research(prompt, images=None):
    results = web_search(prompt)
    context = "\n".join([f"Kaynak: {r['title']} - URL: {r['url']}\nOzet: {r['snippet']}" for r in results])
    synthesis_prompt = f"Soru: {prompt}\n\nWeb Sonuclari:\n{context}\n\nBu bilgileri kullanarak Turkce net bir ozet yaz."
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Web arastirmasi Gemini 2.5 Flash gerektirir; .env dosyasinda GEMINI_API_KEY tanimli olmali."
        )
    # ONEMLI: has_internet=True - gercekten arama yapildigini modele bildirir.
    return generate_cloud('gemini-2.5-flash', synthesis_prompt, images=images, has_internet=True)

def generate_with_model(model, prompt, images=None, history=None):
    if model == 'web-arastirmaci': return generate_web_research(prompt, images=images)
    if is_cloud_model(model): return generate_cloud(model, prompt, images=images, history=history)
    return generate_local(model, prompt, images=images, history=history)

# ---------------------------------------------------------------------------
# STREAMING (akan yanit) uretim fonksiyonlari - her biri parca parca metin
# yield eder. Bagimsiz calisirlar, mevcut generate_local/generate_cloud'a
# dokunmuyorlar (onlar excel/warmup gibi tek-parca gereken yerlerde kalmaya
# devam ediyor).
# ---------------------------------------------------------------------------
def _stream_ollama(model, prompt, images, history, has_internet=False):
    messages = [{'role': 'system', 'content': build_system_prompt(has_internet=has_internet, model=model)}]
    for h in (history or []):
        if h.get('role') in ('user', 'assistant'):
            messages.append({'role': h.get('role'), 'content': h.get('content', '')})
    current_msg = {'role': 'user', 'content': prompt}
    if images: current_msg['images'] = images
    messages.append(current_msg)
    if not is_ollama_running(): start_ollama()
    stream = ollama_client.chat(
        model=model, messages=messages, keep_alive=OLLAMA_KEEP_ALIVE,
        options={'num_ctx': OLLAMA_NUM_CTX}, stream=True
    )
    for chunk in stream:
        piece = chunk['message']['content']
        if piece:
            yield piece


def _stream_gemini(model, prompt, images, history, has_internet=False):
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini anahtari yok.")
    system_prompt = build_system_prompt(has_internet=has_internet, model=model)
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
        current_prompt = system_prompt + "\n\n---\n\nKullanicinin mesaji:\n" + prompt

    current_parts = [current_prompt]
    if images:
        for img_b64 in images:
            current_parts.append({'mime_type': 'image/png', 'data': base64.b64decode(img_b64)})
    contents.append({'role': 'user', 'parts': current_parts})
    stream = gmodel.generate_content(contents, stream=True)
    for chunk in stream:
        if getattr(chunk, 'text', None):
            yield chunk.text


def _stream_kimi(model, prompt, images, history, has_internet=False):
    if not KIMI_API_KEY:
        raise RuntimeError("Kimi API anahtari yok.")
    system_prompt = build_system_prompt(has_internet=has_internet, model=model)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {KIMI_API_KEY}"}
    messages = [{"role": "system", "content": system_prompt}]
    for h in (history or []):
        role = 'user' if h.get('role') == 'user' else 'assistant'
        messages.append({"role": role, "content": h.get('content', '')})
    current_content = [{"type": "text", "text": prompt}]
    if images:
        for img_b64 in images:
            current_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
    messages.append({"role": "user", "content": current_content})
    payload = {"model": "moonshot-v1-auto", "messages": messages, "temperature": 0.3, "stream": True}
    resp = requests.post(
        "https://api.moonshot.cn/v1/chat/completions",
        headers=headers, json=payload, timeout=60, stream=True
    )
    resp.raise_for_status()
    for line in resp.iter_lines():
        if not line:
            continue
        line = line.decode('utf-8')
        if not line.startswith('data: '):
            continue
        data_str = line[len('data: '):].strip()
        if data_str == '[DONE]':
            break
        try:
            data = json.loads(data_str)
            delta = data['choices'][0]['delta'].get('content', '')
            if delta:
                yield delta
        except Exception:
            continue


def stream_from_model(model, prompt, images=None, history=None):
    """Modelden parca parca metin uretir. web-arastirmaci cok adimli bir
    islem oldugu icin (arama+okuma+sentez) tek parca olarak donuyor."""
    if model == 'web-arastirmaci':
        text = generate_web_research(prompt, images=images)
        yield text
        return
    if model == 'kimi-k3':
        yield from _stream_kimi(model, prompt, images, history)
    elif is_cloud_model(model):
        yield from _stream_gemini(model, prompt, images, history)
    else:
        yield from _stream_ollama(model, prompt, images, history)


def stream_chat_response(prompt, model, images, history):
    """Flask Response icin NDJSON (satir satir JSON) ureten jeneratordur.
    Once istenen modelin ILK parcasini almayi dener; basarisiz olursa
    (kullanici fark etmeden) siradaki yedek modele gecer. Bir model basarili
    sekilde akmaya basladiktan sonra kesintisiz devam eder."""
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
                print(f"[MODEL HATASI] '{candidate}' yanit veremedi: {e}")
                continue

            # Bu noktaya geldiysek model basariyla ilk parcayi uretti - artik
            # bu modelle devam ediyoruz, baska bir sey denemiyoruz.
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
                print(f"[MODEL HATASI] '{candidate}' akis sirasinda kesildi: {e}")
                yield json.dumps({'type': 'error', 'message': f'Yanit yarida kesildi: {e}'}, ensure_ascii=False) + '\n'
                return

            record_response_time(candidate, time.time() - start_time)
            if is_cloud_model(candidate):
                record_cloud_usage(candidate)
            yield json.dumps({'type': 'done'}, ensure_ascii=False) + '\n'
            return

        yield json.dumps({
            'type': 'error',
            'message': "Denenen hicbir model yanit veremedi (" + ', '.join(tried) + ")."
        }, ensure_ascii=False) + '\n'

    return Response(event_stream(), mimetype='application/x-ndjson')

def list_local_models():
    try:
        response = ollama_status_client.list()
        return [m.model for m in response.models]
    except Exception: return []

PRIORITY_LOCAL = ['qwen2.5:3b', 'qwen2.5:7b', 'llama3.2:3b', 'gemma2:2b', 'deepseek-r1:1.5b']

def build_fallback_candidates(failed_model, vision_only=False):
    available = list_local_models()
    if not available: available = PRIORITY_LOCAL
    candidates = [m for m in available if m != failed_model]
    if vision_only:
        # Gorsel gonderilmisse, sadece gorsel destekleyen modellere dus
        candidates = [m for m in candidates if is_vision_capable(m)]
    return candidates

def generate_with_fallback(requested_model, prompt, images=None, history=None):
    # Kimi veya Gemini kotası patlarsa anında yerel modellere vites atan emniyet mekanizması
    start_time = time.time()
    try:
        text = generate_with_model(requested_model, prompt, images=images, history=history)
        record_response_time(requested_model, time.time() - start_time)
        if is_cloud_model(requested_model):
            record_cloud_usage(requested_model)
        return {'response': text, 'model': requested_model, 'fallback': False}
    except Exception as e:
        print(f"[BULUT KOTA VEYA MODEL SIKINTISI] Otomatik yerel moda gecildi: {e}")
    
    for candidate in build_fallback_candidates(requested_model, vision_only=bool(images)):
        candidate_start = time.time()
        try:
            text = generate_with_model(candidate, prompt, images=images, history=history)
            record_response_time(candidate, time.time() - candidate_start)
            if is_cloud_model(candidate):
                record_cloud_usage(candidate)
            return {'response': text, 'model': candidate, 'fallback': True, 'requested_model': requested_model}
        except Exception: continue
    raise RuntimeError("Hicbir yerel model yanit veremedi.")

@app.route('/')
def index(): return send_from_directory('static', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model', 'qwen2.5:3b')
    history = data.get('history', [])
    if not prompt:
        return jsonify({'error': 'Bos mesaj'}), 400
    return stream_chat_response(prompt, model, images=None, history=history)

@app.route('/chat-multi-image', methods=['POST'])
def chat_multi_image():
    data = request.get_json()
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model', 'moondream:latest')
    images = data.get('images', [])
    history = data.get('history', [])
    if not images:
        return jsonify({'error': 'Gorsel bulunamadi'}), 400
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
    table_prompt = "Bu gorseldeki tabloyu hucreleri '|' ile ayirarak yaz."
    result = generate_with_fallback(model, table_prompt, images=[image_b64])
    wb = Workbook()
    ws = wb.active
    for line in result['response'].strip().splitlines():
        if line.strip(): ws.append([c.strip() for c in line.strip('|').split('|')])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="tablo.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

CONVERSATIONS_BACKUP_FILE = os.path.join(BASE_DIR, 'conversations_backup.json')

@app.route('/save-conversations', methods=['POST'])
def save_conversations():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Gecersiz veri'}), 400
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
        'kimi': bool(KIMI_API_KEY),
        'cloud_usage_today': get_today_cloud_usage()
    })

@app.route('/model-stats', methods=['GET'])
def model_stats():
    return jsonify(_load_stats())

@app.route('/models', methods=['GET'])
def list_models():
    local_models = list_local_models()
    if not local_models: local_models = PRIORITY_LOCAL
    for unwanted in ['phi3:latest', 'phi3', 'gemma4:12b']:
        if unwanted in local_models: local_models.remove(unwanted)
        
    clouds = []
    if GEMINI_API_KEY: clouds.append('gemini-2.5-flash')
    if KIMI_API_KEY: clouds.append('kimi-k3') # Listeye Kimi K3'ü ekliyoruz
    
    return jsonify({
        'local': local_models, 
        'cloud': clouds, 
        'research': ['web-arastirmaci'] if GEMINI_API_KEY else []
    })

@app.route('/warmup', methods=['POST'])
def warmup(): return jsonify({'status': 'skipped'})

if __name__ == '__main__':
    start_ollama()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)