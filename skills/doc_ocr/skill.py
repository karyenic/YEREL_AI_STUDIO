import os
import json

SKILL_INFO = {
    "name": "doc_ocr",
    "description": "PDF ve taranmış belgelerden metin/veri okur, yerel AI ile structured Excel/Markdown tablosuna dönüştürür.",
    "version": "1.0.0"
}

def read_text_from_file(file_path):
    """Belge içeriğini okur (Metin/PDF temel okuma)."""
    try:
        if file_path.endswith('.pdf'):
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            except ImportError:
                return "⚠️ PDF okuma için 'pypdf' kütüphanesi eksik. (pip install pypdf)"
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        return f"Hata: {str(e)}"

def run_skill(model_runner, config_path=None):
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")

    input_dir = os.path.join(os.path.dirname(__file__), "girdiler")
    files = [f for f in os.listdir(input_dir) if not f.startswith('.')]

    if not files:
        return f"📭 İşlenecek belge bulunamadı. Lütfen işlemek istediğiniz PDF veya metin dosyasını şu klasöre atın:\n`{input_dir}`"

    target_file = os.path.join(input_dir, files[0])
    raw_content = read_text_from_file(target_file)

    if raw_content.startswith("⚠️") or raw_content.startswith("Hata"):
        return raw_content

    prompt = f"""Aşağıdaki belge metnini dikkatlice analiz et.
İçindeki tüm verileri (parça adları, kodlar, adetler, fiyatlar veya teknik ölçüler) temiz bir **Markdown Tablosu** formatına dönüştür.

Belge Adı: {files[0]}
Belge İçeriği:
{raw_content[:3000]}
"""
    return model_runner(prompt)
