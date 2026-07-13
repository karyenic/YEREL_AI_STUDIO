import io
import os
import re
import sys
import time
import atexit
import base64
import threading
import subprocess
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, send_file
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

# ---------------------------------------------------------------------------
# Kalici kayit klasorleri (excels/ ve uploads/), app.py ile ayni klasorde
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCELS_DIR = os.path.join(BASE_DIR, 'excels')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(EXCELS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Ollama servis yonetimi (program acilirken baslat, kapanirken kapat)
#
# Bu bilgisayarda NVIDIA GPU olmadigi icin Ollama otomatik olarak CPU modunda
# calisir; ekstra bir GPU ayari gerekmiyor. CPU'da uretim daha yavas
# olabildigi icin istemci zaman asimi (timeout) bilerek genis tutuldu.
# ---------------------------------------------------------------------------
OLLAMA_HOST = 'http://127.0.0.1:11434'
OLLAMA_TIMEOUT = 300  # saniye - CPU'da buyuk modeller yavas cevap verebilir
OLLAMA_STATUS_TIMEOUT = 8  # saniye - durum/liste sorgulari hizli basarisiz olmali, uzun beklememeli
OLLAMA_KEEP_ALIVE = '30m'  # model bu sure boyunca bellekte tutulur, tekrar tekrar diskten yuklenmez
ollama_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT)
ollama_status_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_STATUS_TIMEOUT)
ollama_process = None

# Ayni anda sadece TEK bir model isitma (warmup) islemi calissin - CPU'da birden
# fazla buyuk modelin ayni anda yuklenmeye calisilmasi sistemi tikiyordu.
_warmup_lock = threading.Lock()
_warmup_in_progress = False

# ---------------------------------------------------------------------------
# Master sistem promptu - tum yerel/bulut modellere otomatik olarak eklenir.
# Kisisel bilgilerinizi veya tercihlerinizi degistirmek icin sadece bu metni
# duzenlemeniz yeterli, baska hicbir yeri degistirmenize gerek yok.
# ---------------------------------------------------------------------------
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

# ONEMLI DIL KURALI - kucuk modellerin Ingilizce'ye kaymasini/devrik cumle kurmasini
# azaltmak icin belirgin, tekrarlanan ve ornekli bir talimat.
LANGUAGE_RULE = (
    " ONEMLI DIL KURALI: Cevabinin TAMAMINI, bastan sona, akici ve dogru dilbilgisi "
    "kurallarina uygun TURKCE yaz. Ozne-yuklem uyumuna dikkat et, devrik veya bozuk cumle "
    "kurma. Ingilizce kelime veya cumle KESINLIKLE kullanma; bir terimin Turkce karsiligi "
    "yoksa once Turkce aciklamasini yaz, istersen parantez icinde orijinalini belirt, ama "
    "cumlenin tamami Turkce olmali. Dogru uslup ornegi: 'Elbette, hemen yardimci olayim, "
    "once su adimi deneyelim.' Yanlis uslup ornegi (boyle YAZMA): 'Sure, I can help you "
    "with that bunu yapalim.'"
)

# ---------------------------------------------------------------------------
# Model bazli 'yetenek' promptlari - her modele kendi guclu oldugu alan
# cercevesinde bir rol/odak tanimlanir. Anahtar, model adinin icinde gecen
# bir alt-metin olmalidir (kucuk harf, ornegin 'moondream', 'vision', 'qwen').
# ---------------------------------------------------------------------------
MODEL_SKILL_PROMPTS = {
    'moondream': (
        "Bu model ozellikle gorsel (resim) analiz etmek icin egitilmis kucuk ve hizli bir "
        "modeldir. Bir gorsel geldiginde, gorseldeki nesneleri, renkleri, metinleri ve genel "
        "sahneyi net ve sade bir sekilde tarif et. Karmasik mantik veya uzun yazi istenirse, "
        "bu konuda sinirli oldugunu belirtip kisa tutmaya calis."
    ),
    'vision': (
        "Bu, gorsel (resim) analiz etme konusunda guclu bir yerel modeldir. Gonderilen "
        "gorselleri dikkatle inceleyip acik ve anlasilir sekilde aciklama yap; gorseldeki "
        "onemli detaylari atlamamaya ozen goster."
    ),
    'deepseek-r1': (
        "Bu model adim adim mantik yurutme (reasoning) konusunda guclu bir yerel modeldir. "
        "Karmasik veya cok adimli sorularda dusunce surecini kisaca ozetleyerek ilerle, ama "
        "nihai cevabini net ve kisa tut; gereksiz uzun ic dusunme metinleri gosterme."
    ),
    'phi': (
        "Bu, kucuk ama hizli calisan genel amacli bir yerel modeldir. Kisa, dogrudan ve "
        "net cevaplar vermeye odaklan; uzun/karmasik konularda basitlestirerek anlat."
    ),
    'qwen': (
        "Bu, genel sohbet, gunluk sorular ve orta duzeyde kod/metin yazimi icin dengeli "
        "calisan bir yerel modeldir."
    ),
    'gemma': (
        "Bu, genel sohbet ve yaratici yazim (metin, fikir, taslak uretme) konusunda "
        "kullanisli bir yerel modeldir."
    ),
    'llama3.1': (
        "Bu, genel amacli, dengeli calisan bir yerel modeldir."
    ),
    'llama3.2': (
        "Bu, kucuk ve hizli, genel amacli bir yerel modeldir. Basit ve gunluk sorular icin uygundur."
    ),
    'gemini': (
        "Bu, gucu yuksek bulut tabanli bir modeldir; karmasik, cok adimli veya detay "
        "gerektiren sorularda da guvenle derinlemesine yardimci olabilirsin."
    ),
}


def get_model_skill_prompt(model):
    if not model:
        return ""
    model_lower = model.lower()
    for key, text in MODEL_SKILL_PROMPTS.items():
        if key in model_lower:
            return text
    return ""


def build_system_prompt(has_internet=False, model=None):
    """Master promptu, dil kurali, guncel tarih, internet erisim durumu ve modele
    ozel yetenek talimatiyla birlikte olusturur."""
    today = datetime.now().strftime('%d.%m.%Y')
    prompt = MASTER_SYSTEM_PROMPT + LANGUAGE_RULE + f" Bugunun tarihi: {today}."

    if has_internet:
        prompt += (
            " Bu mesaj icin internetten gercek zamanli bir web aramasi yapildi ve sonuclari "
            "sana asagida saglandi; bu bilgileri guncel ve guvenilir kaynak olarak kullanabilirsin."
        )
    else:
        prompt += (
            " Senin gercek zamanli internet erisimin YOKTUR. Guncel bilgi, haber, hava durumu "
            "veya canli veri istenirse bunu bilemeyecegini acikca belirt ve internete erisimin "
            "olmadigini soyle - asla internete eristigini veya guncel veri gordugunu iddia etme."
        )

    skill_text = get_model_skill_prompt(model)
    if skill_text:
        prompt += " " + skill_text

    return prompt


def is_ollama_running():
    try:
        ollama_status_client.list()
        return True
    except Exception:
        return False


def start_ollama():
    global ollama_process
    if is_ollama_running():
        print('[Ollama] zaten calisiyor.')
        return
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        ollama_process = subprocess.Popen(
            ['ollama', 'serve'],
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        for _ in range(20):
            time.sleep(0.5)
            if is_ollama_running():
                print('[Ollama] baslatildi.')
                return
        print('[Ollama] UYARI: baslatildi ama hazir oldugu dogrulanamadi.')
    except FileNotFoundError:
        print("[Ollama] UYARI: 'ollama' komutu bulunamadi (PATH icinde olmayabilir).")
    except Exception as e:
        print(f'[Ollama] baslatma hatasi: {e}')


def stop_ollama():
    global ollama_process
    if ollama_process is not None:
        print('[Ollama] kapatiliyor...')
        ollama_process.terminate()
        try:
            ollama_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ollama_process.kill()


atexit.register(stop_ollama)

# ---------------------------------------------------------------------------
# Bulut model (Gemini) ayarlari - API anahtari .env dosyasindan okunur
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
CLOUD_MODELS = {'gemini-2.5-flash': 'gemini-2.5-flash'}

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        print(f"[Gemini] API anahtari bulundu (uzunluk: {len(GEMINI_API_KEY)}). Bulut model aktif.")
    except ImportError as e:
        print(f"[Gemini] UYARI: 'google-generativeai' paketi kurulu degil ({e}). "
              f"'pip install google-generativeai' calistirin.")
        GEMINI_API_KEY = ''  # paket yoksa bulut modelini devre disi birak
else:
    print("[Gemini] .env icinde GEMINI_API_KEY bulunamadi. Bulut model devre disi.")


def is_cloud_model(model):
    return model in CLOUD_MODELS


WEB_RESEARCH_MODEL_NAME = 'web-arastirmaci'


def web_search(query, max_results=4):
    """DuckDuckGo uzerinden anahtar kelime aramasi yapar (API anahtari gerekmez)."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                'title': r.get('title', ''),
                'url': r.get('href') or r.get('url', ''),
                'snippet': r.get('body', ''),
            })
    return results


def fetch_page_text(url, max_chars=3000, timeout=8):
    """Bir web sayfasinin ana metnini cikarir (script/stil etiketleri atlanir)."""
    try:
        resp = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript']):
            tag.decompose()
        text = ' '.join(soup.get_text(separator=' ').split())
        return text[:max_chars] if text else '(Bu sayfada okunabilir metin bulunamadi.)'
    except Exception as e:
        return f'(Bu sayfa okunamadi: {e})'


def generate_web_research(prompt, images=None):
    """Web'de arama yapar, ilgili sayfalari okur ve Gemini 2.5 Flash ile sentezler."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Web arastirmasi ozelligi Gemini 2.5 Flash gerektirir; .env dosyasinda "
            "GEMINI_API_KEY tanimli olmali."
        )

    try:
        results = web_search(prompt, max_results=4)
    except Exception as e:
        raise RuntimeError(f"Web aramasi basarisiz oldu: {e}")

    if not results:
        raise RuntimeError("Web aramasi hicbir sonuc getirmedi.")

    context_parts = []
    for i, r in enumerate(results, start=1):
        page_text = fetch_page_text(r['url'])
        context_parts.append(
            f"[Kaynak {i}] {r['title']}\nURL: {r['url']}\n"
            f"Ozet: {r['snippet']}\nIcerik: {page_text}"
        )
    context = '\n\n---\n\n'.join(context_parts)

    synthesis_prompt = (
        f"Kullanicinin sorusu: {prompt}\n\n"
        f"Asagida bu soruyla ilgili olarak web'den az once toplanan guncel kaynaklar var. "
        f"Bu kaynaklari kullanarak soruyu Turkce, net ve dogru bir sekilde yanitla. "
        f"Kaynaklarda cevap yoksa bunu acikca belirt, uydurma. Yanitinin sonunda "
        f"kullandigin kaynaklarin URL'lerini numarali sekilde listele.\n\n{context}"
    )

    return generate_cloud('gemini-2.5-flash', synthesis_prompt, images=images, has_internet=True)


def is_vision_capable(model):
    if is_cloud_model(model):
        return True
    keywords = ('vision', 'moondream')
    return any(k in model for k in keywords)


def generate_cloud(model, prompt, images=None, has_internet=False, history=None):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY tanimli degil. Proje klasorune bir '.env' dosyasi "
            "ekleyip icine GEMINI_API_KEY=... satirini yazin."
        )
    system_prompt = build_system_prompt(has_internet=has_internet, model=model)
    use_system_instruction = True
    try:
        # Yeni SDK surumleri system_instruction destekler
        gmodel = genai.GenerativeModel(CLOUD_MODELS[model], system_instruction=system_prompt)
    except TypeError:
        # Eski SDK surumu system_instruction desteklemiyor; sistem promptunu
        # ilk mesajin basina elle ekleyecegiz (asagida).
        gmodel = genai.GenerativeModel(CLOUD_MODELS[model])
        use_system_instruction = False

    # Onceki sohbet turlerini Gemini'nin 'user'/'model' rol formatina cevir
    contents = []
    for h in (history or []):
        role = h.get('role')
        text = h.get('content', '')
        if not text:
            continue
        if role == 'user':
            contents.append({'role': 'user', 'parts': [text]})
        elif role == 'assistant':
            contents.append({'role': 'model', 'parts': [text]})

    current_prompt = prompt
    if not use_system_instruction and not contents:
        # Eski SDK + gecmis yok: sistem promptunu ilk mesaja ekle
        current_prompt = system_prompt + "\n\n---\n\nKullanicinin mesaji:\n" + prompt

    current_parts = [current_prompt]
    if images:
        for img_b64 in images:
            current_parts.append({'mime_type': 'image/png', 'data': base64.b64decode(img_b64)})
    contents.append({'role': 'user', 'parts': current_parts})

    resp = gmodel.generate_content(contents)
    return resp.text


def generate_local(model, prompt, images=None, history=None):
    messages = [{'role': 'system', 'content': build_system_prompt(has_internet=False, model=model)}]
    for h in (history or []):
        role = h.get('role')
        text = h.get('content', '')
        if not text or role not in ('user', 'assistant'):
            continue
        messages.append({'role': role, 'content': text})

    current_msg = {'role': 'user', 'content': prompt}
    if images:
        current_msg['images'] = images
    messages.append(current_msg)

    if not is_ollama_running():
        start_ollama()
    response = ollama_client.chat(model=model, messages=messages, keep_alive=OLLAMA_KEEP_ALIVE)
    return response['message']['content']


def generate_with_model(model, prompt, images=None, history=None):
    if model == WEB_RESEARCH_MODEL_NAME:
        return generate_web_research(prompt, images=images)
    if is_cloud_model(model):
        return generate_cloud(model, prompt, images=images, history=history)
    return generate_local(model, prompt, images=images, history=history)


def list_local_models():
    try:
        response = ollama_status_client.list()
        names = []
        if hasattr(response, 'models'):
            for m in response.models:
                name = getattr(m, 'model', None) or getattr(m, 'name', None)
                if name:
                    names.append(name)
        return names
    except Exception:
        return []


# CPU'da hizli calisan kucuk modeller once denenir (yedeklemede zaman kaybetmemek icin)
# Not: llama3.2-vision:11b, gemma4:12b ve phi4:latest bilerek listede degil -
# bu bilgisayarda (GPU'suz, CPU-only) pratik olarak cok yavas/uyumsuz bulundular.
PRIORITY_LOCAL = [
    'qwen2.5:3b', 'qwen2.5:7b', 'llama3.2:3b', 'gemma2:2b', 'phi3:latest',
    'moondream:latest', 'granite3.2-vision:2b', 'deepseek-r1:1.5b', 'llama3.1:latest',
]


def build_fallback_candidates(failed_model, vision_only=False):
    candidates = []

    # Web arastirmacisi basarisiz olursa, once web'siz dogrudan Gemini'yi dene
    if failed_model == WEB_RESEARCH_MODEL_NAME and GEMINI_API_KEY:
        candidates.append('gemini-2.5-flash')

    available = list_local_models()
    ordered = [m for m in PRIORITY_LOCAL if m in available and m != failed_model]
    ordered += [m for m in available if m not in ordered and m != failed_model]
    if vision_only:
        ordered = [m for m in ordered if is_vision_capable(m)]
    candidates += ordered

    if GEMINI_API_KEY and failed_model not in ('gemini-2.5-flash', WEB_RESEARCH_MODEL_NAME):
        candidates.append('gemini-2.5-flash')

    return candidates


# Modele gonderilecek gecmis mesaj sayisi sinirlandirilir - kucuk yerel
# modellerin baglam penceresini asmamak ve CPU'da yavaslamamak icin.
MAX_HISTORY_MESSAGES = 12


def trim_history(history):
    if not history:
        return []
    return history[-MAX_HISTORY_MESSAGES:]


def generate_with_fallback(requested_model, prompt, images=None, history=None):
    """Istenen model yanit veremezse otomatik olarak baska bir modele gecer."""
    vision_only = bool(images)
    tried = [requested_model]
    history = trim_history(history)

    try:
        text = generate_with_model(requested_model, prompt, images=images, history=history)
        return {'response': text, 'model': requested_model, 'fallback': False}
    except Exception as e:
        print(f"[MODEL HATASI] '{requested_model}' yanit veremedi: {e}")

    for candidate in build_fallback_candidates(requested_model, vision_only=vision_only):
        tried.append(candidate)
        try:
            text = generate_with_model(candidate, prompt, images=images, history=history)
            return {
                'response': text,
                'model': candidate,
                'fallback': True,
                'requested_model': requested_model,
            }
        except Exception as e:
            print(f"[MODEL HATASI] Yedek '{candidate}' de yanit veremedi: {e}")
            continue

    raise RuntimeError(
        "Denenen hicbir model yanit veremedi (" + ', '.join(tried) + "). "
        "Ollama servisinin calistigindan ve modellerin kurulu oldugundan "
        "emin olun ('ollama pull <model_adi>'). Gercek hata detayi icin "
        "programi calistirdiginiz konsol/terminal penceresine bakin."
    )


# ---------------------------------------------------------------------------
# Route'lar
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model', 'moondream:latest')
    history = data.get('history', [])
    if not prompt:
        return jsonify({'error': 'Bos mesaj'}), 400
    try:
        result = generate_with_fallback(model, prompt, history=history)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chat-multi-image', methods=['POST'])
def chat_multi_image():
    data = request.get_json()
    prompt = (data.get('prompt') or '').strip()
    model = data.get('model', 'moondream:latest')
    images = data.get('images', [])
    history = data.get('history', [])
    if not images:
        return jsonify({'error': 'Gorsel bulunamadi'}), 400
    try:
        result = generate_with_fallback(
            model,
            prompt or 'Bu görsel(ler) hakkında detaylı yorum yap.',
            images=images,
            history=history
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadi'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya secilmedi'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Sadece PDF dosyalari desteklenir'}), 400
    try:
        file_bytes = file.read()

        # Yuklenen PDF'i uploads/ klasorune kalici olarak kaydet
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        safe_name = f"{timestamp}_{file.filename}"
        save_path = os.path.join(UPLOADS_DIR, safe_name)
        with open(save_path, 'wb') as f:
            f.write(file_bytes)

        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = [p.extract_text() or '' for p in reader.pages]
        full_text = '\n'.join(text_parts).strip()
        if not full_text:
            full_text = '(Bu PDF icinde metin bulunamadi; taranmis/gorsel bir belge olabilir.)'
        return jsonify({'text': full_text, 'pages': len(reader.pages), 'saved_as': safe_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/image-to-excel', methods=['POST'])
def image_to_excel():
    data = request.get_json()
    model = data.get('model', 'moondream:latest')
    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'error': 'Gorsel bulunamadi'}), 400
    try:
        table_prompt = (
            "Bu gorseldeki tabloyu incele. Sadece tablo verisini, her satiri bir "
            "satira gelecek sekilde, hucreleri '|' karakteriyle ayirarak yaz. "
            "Baslik satirini da dahil et. Tablo disinda hicbir aciklama, "
            "yorum veya ek metin yazma."
        )
        result = generate_with_fallback(model, table_prompt, images=[image_b64])
        raw_text = result['response'].strip()

        rows = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.fullmatch(r'[\|\-\s:]+', line):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append(cells)

        if not rows:
            return jsonify({'error': 'Modelden tablo verisi alinamadi. Baska bir gorsel/model deneyin.'}), 500

        wb = Workbook()
        ws = wb.active
        ws.title = 'Tablo'
        for row in rows:
            ws.append(row)
        for col_cells in ws.columns:
            length = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max(length + 2, 10), 40)

        # Excel dosyasini excels/ klasorune kalici olarak kaydet
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"tablo_{timestamp}.xlsx"
        save_path = os.path.join(EXCELS_DIR, filename)
        wb.save(save_path)

        # Ayni zamanda tarayiciya indirilmek uzere de gonder
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers['X-Saved-Filename'] = filename
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/warmup', methods=['POST'])
def warmup():
    """Bir modeli arka planda 'isitir' (belleğe onceden yukler). Bos prompt
    gonderilir - bu, gercek bir yanit uretmeden modeli sadece RAM'e yukler,
    boylece CPU'yu bosuna mesgul etmez. Ayni anda sadece TEK bir isitma
    calisir; CPU'da birden fazla buyuk model isitmasi sistemi tikiyordu."""
    global _warmup_in_progress
    data = request.get_json() or {}
    model = data.get('model')
    if not model or is_cloud_model(model) or model == WEB_RESEARCH_MODEL_NAME:
        return jsonify({'status': 'skipped'})

    with _warmup_lock:
        if _warmup_in_progress:
            return jsonify({'status': 'busy'})
        _warmup_in_progress = True

    def _warm():
        global _warmup_in_progress
        try:
            if not is_ollama_running():
                start_ollama()
            # Bos prompt: model sadece belleğe yuklenir, token uretilmez (hizli)
            ollama_client.generate(model=model, prompt='', keep_alive=OLLAMA_KEEP_ALIVE)
        except Exception:
            pass
        finally:
            _warmup_in_progress = False

    threading.Thread(target=_warm, daemon=True).start()
    return jsonify({'status': 'started'})


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'ollama': is_ollama_running(),
        'gemini': bool(GEMINI_API_KEY)
    })


@app.route('/models', methods=['GET'])
def list_models():
    local_models = list_local_models()
    if not local_models:
        local_models = [
            'deepseek-r1:1.5b', 'phi3:latest', 'moondream:latest',
            'granite3.2-vision:2b', 'llama3.2:3b', 'gemma2:2b',
            'qwen2.5:3b', 'qwen2.5:7b', 'llama3.1:latest'
        ]
    research_models = [WEB_RESEARCH_MODEL_NAME] if GEMINI_API_KEY else []
    return jsonify({
        'local': local_models,
        'cloud': list(CLOUD_MODELS.keys()),
        'research': research_models
    })


if __name__ == '__main__':
    start_ollama()
    # debug=False ve use_reloader=False: Flask'in reloader'i script'i iki kez
    # calistirip Ollama'yi iki kez baslatmaya/kapatmaya calisabilir, bu yuzden kapali.
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)