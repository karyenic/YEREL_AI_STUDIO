import os, re

html_path = os.path.join("static", "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Süre Takip Değişkenleri
    vars_code = """
    let responseStartTime = 0;
    let responseTimesHistory = [];
"""
    if "let responseStartTime = 0;" not in content:
        content = content.replace("let currentAbortController = null;", "let currentAbortController = null;\n" + vars_code)

    # 2. Gönderim Anında Sayacı Başlatma
    if "responseStartTime = performance.now();" not in content:
        content = content.replace("conv.pending = true;", "conv.pending = true;\n        responseStartTime = performance.now();")

    # 3. Model Adının Yanına Süre ve Ortalama Ekleme Mantığı
    time_calc_js = """
            // Model adının yanına süre hesabı (Son yanıt ve Ortalama)
            if (responseStartTime > 0) {
                const elapsedSec = ((performance.now() - responseStartTime) / 1000).toFixed(1);
                responseTimesHistory.push(parseFloat(elapsedSec));
                const sum = responseTimesHistory.reduce((a, b) => a + b, 0);
                const avgSec = (sum / responseTimesHistory.length).toFixed(1);

                const timeInfo = ` (${elapsedSec}s | ort: ${avgSec}s)`;
                finalModel = finalModel ? (finalModel + timeInfo) : ('Model' + timeInfo);
                responseStartTime = 0;
            }
"""
    
    target_finish = "addMessageTo(convId, 'assistant', accumulated, finalModel, finalFallback, finalRequestedModel);"
    if target_finish in content and "responseTimesHistory.push" not in content:
        content = content.replace(target_finish, time_calc_js + "\n            " + target_finish)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Model adının yanına yanıt süresi ve ortalama süre bilgisi başarıyla entegre edildi.")
else:
    print("❌ HATA: static/index.html bulunamadı!")