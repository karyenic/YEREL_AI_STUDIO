import os
import json

SKILL_INFO = {
    "name": "code_reviewer",
    "description": "Yerel Python/PowerShell kodlarini analiz eder, hatalari ayiklar ve iyilestirir.",
    "version": "1.0.0"
}

def read_code_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Hata: {str(e)}"

def run_skill(model_runner, config_path=None):
    code_dir = os.path.join(os.path.dirname(__file__), "kodlar")
    files = [f for f in os.listdir(code_dir) if not f.startswith(".")]
    if not files:
        return f"📭 Incelenecek kod dosyasi bulunamadi. Lutfen ilgili dosyayi su klasore atin:\n`{code_dir}`"
    target_file = os.path.join(code_dir, files[0])
    code_content = read_code_file(target_file)
    if code_content.startswith("Hata:"):
        return code_content
    prompt = f"Sen uzman bir Senior Yazilim Gelistiricisisin. Asagidaki kodu incele:\nDosya: {files[0]}\nKod:\n{code_content[:4000]}\n\nLutfen hatalari, riskleri ve iyilestirilmis kodu belirt."
    return model_runner(prompt)
