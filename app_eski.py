from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import ollama
import base64
import io
import os
import uuid
import pandas as pd
from pypdf import PdfReader
from pdf2image import convert_from_bytes

app = Flask(__name__, static_folder='static')
CORS(app)

UPLOAD_FOLDER = "uploads"
EXCEL_FOLDER = "excels"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXCEL_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    model = data.get('model', 'moondream:latest')
    if not prompt:
        return jsonify({'error': 'Boş mesaj'}), 400
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return jsonify({'response': response['response'], 'model': model})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat-multi-image', methods=['POST'])
def chat_multi_image():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    model = data.get('model', 'moondream:latest')
    images = data.get('images', [])
    if not prompt or not images:
        return jsonify({'error': 'Prompt ve en az bir görsel gerekli'}), 400
    try:
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt, 'images': images}]
        )
        return jsonify({'response': response['message']['content'], 'model': model})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/image-to-excel', methods=['POST'])
def image_to_excel():
    data = request.get_json()
    model = data.get('model', 'moondream:latest')
    image_base64 = data.get('image', '')
    if not image_base64:
        return jsonify({'error': 'Görsel gerekli'}), 400
    try:
        prompt = """Bu görseldeki tablo verisini JSON formatında çıkar.
Tablo sütun başlıklarını ve satırları içeren bir JSON array'i oluştur.
Örnek: [{"Sütun1": "değer1", "Sütun2": "değer2"}, ...]
Sadece JSON çıktısı ver, başka metin yazma."""
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt, 'images': [image_base64]}]
        )
        json_text = response['message']['content']
        import re
        json_match = re.search(r'\[.*\]', json_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        data_list = eval(json_text)
        df = pd.DataFrame(data_list)
        excel_path = os.path.join(EXCEL_FOLDER, f"excel_{uuid.uuid4().hex}.xlsx")
        df.to_excel(excel_path, index=False)
        return send_file(excel_path, as_attachment=True, download_name="tablo.xlsx")
    except Exception as e:
        return jsonify({'error': f'Excel üretilemedi: {str(e)}'}), 500

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya yok'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Sadece PDF dosyası kabul edilir'}), 400
    try:
        pdf_bytes = file.read()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        text = text[:3000]
        return jsonify({'text': text, 'pages': len(reader.pages)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
def list_models():
    try:
        response = ollama.list()
        models = []
        if hasattr(response, 'models'):
            for m in response.models:
                name = getattr(m, 'model', None) or getattr(m, 'name', None)
                if name:
                    models.append(name)
        return jsonify(models)
    except Exception as e:
        print(f"Model listesi hatası: {e}")
        return jsonify(['moondream:latest'])
        # veya manuel liste döndürmek istersen:
        # return jsonify(['gemma4:12b','deepseek-r1:1.5b','phi3:latest','llama3.2-vision:11b','moondream:latest','granite3.2-vision:2b','phi4:latest','llama3.2:3b','gemma2:2b','qwen2.5:3b','llama3.1:latest'])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)